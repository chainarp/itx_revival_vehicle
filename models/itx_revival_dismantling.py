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
        """Confirm dismantling done — adjust condition & create lots"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError('ต้องอยู่สถานะ In Progress')

        included_lines = self.line_ids.filtered('is_included')
        if not included_lines:
            raise UserError('ไม่มีรายการอะไหล่ที่รวมใน Dismantling')

        for line in included_lines:
            # If actual condition differs from assessed → lookup/create new product
            if (line.actual_origin_id != line.assessed_origin_id or
                    line.actual_condition_id != line.assessed_condition_id):
                actual_product = self._get_or_create_part_product(
                    line.part_name_id,
                    line.actual_origin_id,
                    line.actual_condition_id,
                )
                line.actual_product_id = actual_product.id if actual_product else False

            # Create lot with VIN stamp
            lot = self.env['stock.lot'].create({
                'name': self.vin,
                'product_id': (line.actual_product_id or line.product_id).id,
                'company_id': self.env.company.id,
                'itx_vin': self.vin,
                'itx_acquired_id': self.acquired_id.id,
            })
            line.lot_id = lot.id

        self.state = 'done'

        # Update acquired state
        if self.acquired_id.state == 'dismantling':
            self.acquired_id.state = 'completed'

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
