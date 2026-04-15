# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


DISMANTLING_STATE_SELECTION = [
    ('draft', 'Draft'),
    ('in_progress', 'In Progress'),
    ('done', 'Done'),
]


class ItxRevivalDismantling(models.Model):
    _name = 'itx.revival.dismantling'
    _description = 'Vehicle Dismantling Order'
    _order = 'name desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # === Identification ===
    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        index=True,
    )
    active = fields.Boolean(default=True)

    # === Link to Acquired ===
    acquired_id = fields.Many2one(
        comodel_name='itx.revival.acquired',
        string='Acquired Vehicle',
        required=True,
        ondelete='restrict',
        index=True,
    )

    # === Related from Acquired ===
    assessment_id = fields.Many2one(
        related='acquired_id.assessment_id',
        store=True,
    )
    spec_id = fields.Many2one(
        related='acquired_id.spec_id',
        store=True,
    )
    vin = fields.Char(
        related='acquired_id.vin',
        store=True,
    )

    # === Dismantling Info ===
    dismantling_date = fields.Date(
        string='Dismantling Date',
    )
    technician_id = fields.Many2one(
        comodel_name='res.partner',
        string='Technician',
        help='ช่างที่รื้อ',
    )

    # === MRP Integration ===
    unbuild_id = fields.Many2one(
        comodel_name='mrp.unbuild',
        string='Unbuild Order',
        readonly=True,
        copy=False,
    )

    # === State ===
    state = fields.Selection(
        selection=DISMANTLING_STATE_SELECTION,
        string='State',
        default='draft',
        required=True,
        tracking=True,
        index=True,
    )

    # === Lines ===
    line_ids = fields.One2many(
        comodel_name='itx.revival.dismantling.line',
        inverse_name='dismantling_id',
        string='Dismantling Lines',
        copy=True,
    )
    line_count = fields.Integer(compute='_compute_line_count')

    # === Notes ===
    note = fields.Text(string='Notes')

    # === Compute ===
    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    # === CRUD ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'itx.revival.dismantling'
                ) or 'New'
        return super().create(vals_list)

    # === Generate Lines ===
    def action_generate_lines(self):
        """Generate dismantling lines from assessment lines (is_found=True)"""
        self.ensure_one()
        if not self.acquired_id or not self.assessment_id:
            raise UserError('ไม่พบข้อมูล Assessment')

        self.line_ids.unlink()

        found_lines = self.assessment_id.line_ids.filtered(
            lambda l: l.is_found and l.product_id
        )
        if not found_lines:
            raise UserError('ไม่มีอะไหล่ที่เจอในแบบประเมิน')

        lines_data = []
        for line in found_lines:
            lines_data.append({
                'dismantling_id': self.id,
                'sequence': line.sequence,
                'part_name_id': line.part_name_id.id,
                'assessment_line_id': line.id,
                'assessed_origin_id': line.part_origin_id.id,
                'assessed_condition_id': line.part_condition_id.id,
                'assessed_qty': line.qty_found,
                'actual_origin_id': line.part_origin_id.id,
                'actual_condition_id': line.part_condition_id.id,
                'actual_qty': line.qty_found,
                'product_id': line.product_id.id,
                'cost_weight': line.cost_weight,
                'is_included': True,
            })

        self.env['itx.revival.dismantling.line'].create(lines_data)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'สร้างรายการอะไหล่แล้ว',
                'message': f'สร้าง {len(lines_data)} รายการจาก Assessment',
                'type': 'success',
                'sticky': False,
            }
        }

    # === State Actions ===
    def action_start(self):
        """Start dismantling — create Unbuild Order"""
        self.ensure_one()
        if not self.line_ids:
            raise UserError('กรุณา Generate Lines ก่อน')

        # Find spec-level BOM
        bom = self.env['mrp.bom'].search([
            ('itx_spec_id', '=', self.spec_id.id),
        ], limit=1)
        if not bom:
            raise UserError('ไม่พบ Spec-level BOM')

        # Get salvage vehicle product
        product = self.acquired_id.product_id
        if not product:
            raise UserError('ไม่พบ Vehicle Product ใน Acquired')

        # Create Unbuild Order
        unbuild = self.env['mrp.unbuild'].create({
            'product_id': product.id,
            'bom_id': bom.id,
            'product_qty': 1,
            'itx_acquired_id': self.acquired_id.id,
            'itx_dismantling_id': self.id,
        })

        self.write({
            'unbuild_id': unbuild.id,
            'dismantling_date': fields.Date.context_today(self),
            'state': 'in_progress',
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'เริ่มรื้อถอน',
                'message': f'สร้าง Unbuild Order: {unbuild.name}',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_done(self):
        """Confirm dismantling done — unbuild via direct stock.move flow.

        Bypasses mrp.unbuild.action_validate() because Odoo requires an MO link
        when produced products are tracked; we don't have one. Instead we create
        stock.moves manually:
          1 consume move: WH/Stock → Production (salvage car, VIN lot)
          N produce moves: Production → resolved_dest (per-part VIN lot)

        Per-part destination is resolved via template_part → category → warehouse
        main stock. All moves are linked to the existing unbuild_id for audit.
        """
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError('ต้องอยู่สถานะ In Progress')

        included_lines = self.line_ids.filtered('is_included')
        if not included_lines:
            raise UserError('ไม่มีรายการอะไหล่ที่รวมใน Dismantling')

        acquired = self.acquired_id
        salvage_product = acquired.product_id
        if not salvage_product:
            raise UserError('ไม่พบ Vehicle Product ใน Acquired')
        if acquired.state != 'dismantling':
            raise UserError('Acquired Vehicle ต้องอยู่สถานะ Dismantling')

        company = self.env.company
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', company.id)], limit=1,
        )
        if not warehouse:
            raise UserError('ไม่พบ Warehouse ของ company ปัจจุบัน')
        stock_loc = warehouse.lot_stock_id
        production_loc = salvage_product.with_company(company).property_stock_production
        if not production_loc:
            raise UserError('ไม่พบ Production Location ของ Vehicle Product')

        # Consume lot must already exist (from acquired.action_confirm_stock)
        StockLot = self.env['stock.lot']
        consume_lot = StockLot.search([
            ('name', '=', self.vin),
            ('product_id', '=', salvage_product.id),
            ('company_id', '=', company.id),
        ], limit=1)
        if not consume_lot:
            raise UserError(
                f'ไม่พบ Serial {self.vin} ของซากรถในสต็อก — '
                f'กรุณา Confirm Stock ที่ Acquired Vehicle ก่อน'
            )

        StockMove = self.env['stock.move']
        StockMoveLine = self.env['stock.move.line']

        # === Consume move: salvage car WH/Stock → Production ===
        consume_move = StockMove.create({
            'name': f'Unbuild: {salvage_product.display_name}',
            'product_id': salvage_product.id,
            'product_uom_qty': 1.0,
            'product_uom': salvage_product.uom_id.id,
            'location_id': stock_loc.id,
            'location_dest_id': production_loc.id,
            'company_id': company.id,
            'unbuild_id': self.unbuild_id.id,
            'origin': self.name,
        })
        consume_move._action_confirm()
        consume_move._action_assign()
        # Stamp VIN lot on the consume move line
        if consume_move.move_line_ids:
            consume_move.move_line_ids[0].write({
                'lot_id': consume_lot.id,
                'quantity': 1.0,
            })
            (consume_move.move_line_ids - consume_move.move_line_ids[0]).unlink()
        else:
            StockMoveLine.create({
                'move_id': consume_move.id,
                'product_id': salvage_product.id,
                'product_uom_id': salvage_product.uom_id.id,
                'location_id': stock_loc.id,
                'location_dest_id': production_loc.id,
                'lot_id': consume_lot.id,
                'quantity': 1.0,
                'company_id': company.id,
            })
        consume_move.picked = True
        consume_move._action_done()

        # === Produce moves: Production → per-part destination ===
        produce_moves = StockMove
        for line in included_lines:
            # Resolve actual product (variant may differ from assessed)
            if (line.actual_origin_id != line.assessed_origin_id or
                    line.actual_condition_id != line.assessed_condition_id):
                actual_product = self._get_or_create_part_product(
                    line.part_name_id,
                    line.actual_origin_id,
                    line.actual_condition_id,
                )
                if actual_product:
                    line.actual_product_id = actual_product.id

            product = line.actual_product_id or line.product_id
            if not product:
                continue

            # Resolve destination: part template → category → warehouse main stock
            dest_loc = line.part_name_id._get_default_stock_location() or stock_loc

            # Get or create VIN lot for this product
            lot = StockLot.search([
                ('name', '=', self.vin),
                ('product_id', '=', product.id),
                ('company_id', '=', company.id),
            ], limit=1)
            if not lot:
                lot = StockLot.create({
                    'name': self.vin,
                    'product_id': product.id,
                    'company_id': company.id,
                    'itx_vin': self.vin,
                    'itx_acquired_id': acquired.id,
                })
            elif not lot.itx_acquired_id:
                lot.write({
                    'itx_vin': self.vin,
                    'itx_acquired_id': acquired.id,
                })

            qty = line.actual_qty or 1.0
            move = StockMove.create({
                'name': f'Unbuild: {product.display_name}',
                'product_id': product.id,
                'product_uom_qty': qty,
                'product_uom': product.uom_id.id,
                'location_id': production_loc.id,
                'location_dest_id': dest_loc.id,
                'company_id': company.id,
                'unbuild_id': self.unbuild_id.id,
                'origin': self.name,
            })
            move._action_confirm()
            move._action_assign()
            if move.move_line_ids:
                move.move_line_ids[0].write({
                    'lot_id': lot.id,
                    'quantity': qty,
                })
                (move.move_line_ids - move.move_line_ids[0]).unlink()
            else:
                StockMoveLine.create({
                    'move_id': move.id,
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'location_id': production_loc.id,
                    'location_dest_id': dest_loc.id,
                    'lot_id': lot.id,
                    'quantity': qty,
                    'company_id': company.id,
                })
            move.picked = True
            line.lot_id = lot.id
            produce_moves |= move

        produce_moves._action_done()

        # Mark the linked unbuild record as done (we bypassed its own validate)
        if self.unbuild_id and self.unbuild_id.state != 'done':
            self.unbuild_id.state = 'done'

        self.state = 'done'
        if acquired.state == 'dismantling':
            acquired.state = 'completed'

    def _get_or_create_part_product(self, part_template, origin, condition):
        """Lookup or create product.product variant for spec + part + origin × condition.

        Uses product.template UK (spec, part_name) + dynamic variant for origin × condition.
        """
        if not origin or not condition:
            return False

        ProductTemplate = self.env['product.template']

        # Find or create template by (spec, part_name)
        domain = [
            ('itx_is_vehicle_part', '=', True),
            ('itx_spec_id', '=', self.spec_id.id),
            ('itx_part_name_id', '=', part_template.id),
        ]
        tmpl = ProductTemplate.search(domain, limit=1)
        if not tmpl:
            tmpl = ProductTemplate.create({
                'name': part_template.name,
                'itx_is_vehicle_part': True,
                'itx_spec_id': self.spec_id.id,
                'itx_part_name_id': part_template.id,
                'itx_part_category_id': part_template.category_id.id if part_template.category_id else False,
                'type': 'consu',
                'is_storable': True,
                'tracking': 'lot',
                'sale_ok': True,
                'purchase_ok': False,
            })

        # Create/find variant
        return tmpl._get_or_create_variant(origin, condition)

    def action_view_unbuild(self):
        self.ensure_one()
        if not self.unbuild_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Unbuild Order',
            'res_model': 'mrp.unbuild',
            'res_id': self.unbuild_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
