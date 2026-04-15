# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


ACQUIRED_STATE_SELECTION = [
    ('draft', 'Draft'),
    ('purchased', 'Purchased'),
    ('stocked', 'In Stock'),
    ('dismantling', 'Dismantling'),
    ('completed', 'Completed'),
]


class ItxRevivalAcquired(models.Model):
    _name = 'itx.revival.acquired'
    _description = 'Acquired Vehicle'
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
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    # === Link to Assessment ===
    assessment_id = fields.Many2one(
        comodel_name='itx.revival.assessment',
        string='Assessment',
        required=True,
        ondelete='restrict',
        index=True,
    )

    # === Vehicle Info (from Assessment) ===
    spec_id = fields.Many2one(
        comodel_name='itx.info.vehicle.spec',
        string='Vehicle Spec',
        related='assessment_id.spec_id',
        store=True,
        index=True,
    )
    body_type_id = fields.Many2one(
        comodel_name='itx.info.vehicle.mgr.body.type',
        string='Body Type',
        related='assessment_id.body_type_id',
        store=True,
    )
    brand_id = fields.Many2one(
        comodel_name='itx.info.vehicle.brand',
        string='Brand',
        related='assessment_id.brand_id',
        store=True,
    )
    model_id = fields.Many2one(
        comodel_name='itx.info.vehicle.model',
        string='Model',
        related='assessment_id.model_id',
        store=True,
    )
    generation_id = fields.Many2one(
        comodel_name='itx.info.vehicle.generation',
        string='Generation',
        related='assessment_id.generation_id',
        store=True,
    )
    decision = fields.Selection(
        related='assessment_id.decision',
        store=True,
    )

    # === Vehicle Details ===
    vin = fields.Char(
        string='VIN',
        required=True,
        index=True,
        tracking=True,
        help='เลขตัวถัง (required)',
    )
    vehicle_year = fields.Integer(
        string='Vehicle Year',
    )
    vehicle_color = fields.Char(
        string='Vehicle Color',
    )
    vehicle_mileage = fields.Integer(
        string='Mileage (km)',
    )

    # === Purchase Info ===
    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        help='ผู้ขาย (เจ้าของซาก)',
    )
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        readonly=True,
        copy=False,
    )
    purchase_price = fields.Float(
        string='Purchase Price',
        digits='Product Price',
        tracking=True,
        help='ราคาที่ซื้อจริง',
    )
    purchase_date = fields.Date(
        string='Purchase Date',
    )

    # === Costs ===
    transport_cost = fields.Float(
        string='Transport Cost',
        digits='Product Price',
        help='ค่าขนส่ง',
    )
    dismantling_cost = fields.Float(
        string='Dismantling Cost',
        digits='Product Price',
        help='ค่า outsource รื้อถอน',
    )
    other_cost = fields.Float(
        string='Other Cost',
        digits='Product Price',
        help='ค่าใช้จ่ายอื่น',
    )
    total_cost = fields.Float(
        string='Total Cost',
        compute='_compute_total_cost',
        store=True,
        digits='Product Price',
    )

    # === Analytic ===
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        readonly=True,
        copy=False,
        help='1 คัน = 1 analytic account',
    )

    # === MRP Integration ===
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Vehicle Product',
        help='ตัวซากรถเป็น product (ใช้กับ Unbuild)',
    )

    # === Link to Dismantling ===
    dismantling_id = fields.Many2one(
        comodel_name='itx.revival.dismantling',
        string='Dismantling Order',
        readonly=True,
        copy=False,
    )

    # === State ===
    state = fields.Selection(
        selection=ACQUIRED_STATE_SELECTION,
        string='State',
        default='draft',
        required=True,
        tracking=True,
        index=True,
    )

    # === ROI Computed ===
    expected_revenue = fields.Float(
        related='assessment_id.expected_revenue',
        string='Expected Revenue',
    )
    actual_revenue = fields.Float(
        string='Actual Revenue',
        compute='_compute_actual_values',
        store=True,
        digits='Product Price',
        help='รายได้จริงจากการขายอะไหล่',
    )
    actual_profit = fields.Float(
        string='Actual Profit',
        compute='_compute_actual_values',
        store=True,
        digits='Product Price',
    )
    actual_roi = fields.Float(
        string='Actual ROI (%)',
        compute='_compute_actual_values',
        store=True,
        digits=(5, 2),
    )
    sold_percentage = fields.Float(
        string='Sold %',
        compute='_compute_actual_values',
        store=True,
        digits=(5, 2),
        help='% ชิ้นส่วนที่ขายแล้ว',
    )

    # === Images ===
    image_ids = fields.One2many(
        comodel_name='itx.revival.acquired.image',
        inverse_name='acquired_id',
        string='Images',
    )

    # === Notes ===
    note = fields.Text(
        string='Notes',
    )

    # === Compute Methods ===
    @api.depends('purchase_price', 'transport_cost', 'dismantling_cost', 'other_cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = (
                (rec.purchase_price or 0) +
                (rec.transport_cost or 0) +
                (rec.dismantling_cost or 0) +
                (rec.other_cost or 0)
            )

    @api.depends('total_cost')
    def _compute_actual_values(self):
        """Compute actual revenue from sold parts.
        TODO: Calculate from sale.order.line linked via lot → acquired
        Until sales exist, all values stay 0.
        """
        for rec in self:
            # TODO: sum sale.order.line amounts where lot.itx_acquired_id == rec
            rec.actual_revenue = 0
            if rec.actual_revenue:
                rec.actual_profit = rec.actual_revenue - rec.total_cost
                rec.actual_roi = (rec.actual_profit / rec.total_cost * 100) if rec.total_cost else 0
            else:
                # No sales yet — don't show misleading negative values
                rec.actual_profit = 0
                rec.actual_roi = 0
            rec.sold_percentage = 0

    # === CRUD Methods ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'itx.revival.acquired'
                ) or 'New'
        records = super().create(vals_list)

        # Create analytic account for each acquired vehicle
        for rec in records:
            rec._create_analytic_account()

        return records

    def _create_analytic_account(self):
        """Create analytic account for this acquired vehicle"""
        self.ensure_one()

        if self.analytic_account_id:
            return

        # Use sudo for analytic (requires accounting group)
        AnalyticPlan = self.env['account.analytic.plan'].sudo()
        AnalyticAccount = self.env['account.analytic.account'].sudo()

        plan = AnalyticPlan.search([('name', 'ilike', 'Revival')], limit=1)
        if not plan:
            plan = AnalyticPlan.create({'name': 'Revival Vehicle'})

        display_name = self.name
        if self.spec_id:
            display_name += f" - {self.spec_id.full_name}"
        if self.vehicle_year:
            display_name += f" {self.vehicle_year}"

        analytic = AnalyticAccount.create({
            'name': display_name,
            'plan_id': plan.id,
        })

        self.analytic_account_id = analytic.id

    # === Action Methods ===
    def action_create_po(self):
        """Create Purchase Order for this vehicle"""
        self.ensure_one()

        if self.purchase_order_id:
            raise UserError('มี Purchase Order อยู่แล้ว')

        if not self.vendor_id:
            raise UserError('กรุณาระบุ Vendor ก่อน')

        if not self.purchase_price:
            raise UserError('กรุณาระบุ Purchase Price ก่อน')

        # Get salvage vehicle product from assessment's spec-level BOM
        if not self.product_id:
            bom = self.env['mrp.bom'].search([
                ('itx_spec_id', '=', self.spec_id.id),
            ], limit=1)
            if bom and bom.product_id:
                self.product_id = bom.product_id.id
            else:
                raise UserError('ไม่พบ Vehicle Product กรุณา Generate Lines ใน Assessment ก่อน')

        # Create PO
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor_id.id,
            'date_order': self.purchase_date or fields.Date.context_today(self),
            'origin': self.name,
        })

        self.env['purchase.order.line'].create({
            'order_id': po.id,
            'product_id': self.product_id.id,
            'name': f'{self.product_id.display_name} - VIN: {self.vin}',
            'product_qty': 1,
            'price_unit': self.purchase_price,
        })

        # Link analytic if available
        if self.analytic_account_id:
            for line in po.order_line:
                line.analytic_distribution = {str(self.analytic_account_id.id): 100}

        self.write({
            'purchase_order_id': po.id,
            'state': 'purchased',
        })

    def action_confirm_stock(self):
        """Validate the PO incoming picking with a VIN-stamped lot/serial.

        - Stamps move_line.lot with VIN (creates stock.lot if missing)
        - Validates the picking so Odoo books the move Vendor → WH/Stock
        - Flips state to 'stocked'
        """
        self.ensure_one()
        if self.state != 'purchased':
            raise UserError('ต้องอยู่สถานะ Purchased ก่อน')
        if not self.purchase_order_id:
            raise UserError('ไม่มี Purchase Order ผูกไว้')
        if not self.product_id:
            raise UserError('ไม่พบ Vehicle Product')
        if not self.vin:
            raise UserError('กรุณาระบุ VIN ก่อน Confirm Stock')

        picking = self.purchase_order_id.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'incoming' and p.state not in ('done', 'cancel')
        )[:1]
        if not picking:
            raise UserError('ไม่พบ Incoming Picking ที่ยังไม่ done ของ PO นี้')

        vehicle_move = picking.move_ids.filtered(
            lambda m: m.product_id.id == self.product_id.id
        )[:1]
        if not vehicle_move:
            raise UserError('ไม่พบ move ของ Vehicle Product ใน Picking')

        # Ensure the picking is assignable
        if picking.state == 'draft':
            picking.action_confirm()
        picking.action_assign()

        # Get or create the VIN lot (unique per product+company+name)
        StockLot = self.env['stock.lot']
        lot = StockLot.search([
            ('name', '=', self.vin),
            ('product_id', '=', self.product_id.id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not lot:
            lot = StockLot.create({
                'name': self.vin,
                'product_id': self.product_id.id,
                'company_id': self.env.company.id,
                'itx_vin': self.vin,
                'itx_acquired_id': self.id,
            })
        elif not lot.itx_acquired_id:
            lot.write({
                'itx_vin': self.vin,
                'itx_acquired_id': self.id,
            })

        # Assign lot + qty on the move line(s); ensure exactly 1 line with qty=1
        move_lines = vehicle_move.move_line_ids
        if not move_lines:
            self.env['stock.move.line'].create({
                'move_id': vehicle_move.id,
                'product_id': self.product_id.id,
                'product_uom_id': vehicle_move.product_uom.id,
                'location_id': vehicle_move.location_id.id,
                'location_dest_id': vehicle_move.location_dest_id.id,
                'lot_id': lot.id,
                'quantity': 1.0,
                'picking_id': picking.id,
            })
        else:
            first = move_lines[0]
            first.write({'lot_id': lot.id, 'quantity': 1.0})
            # Drop any extra move lines
            (move_lines - first).unlink()

        vehicle_move.picked = True
        picking.button_validate()

        self.state = 'stocked'

    def action_create_dismantling(self):
        """Create Dismantling Order"""
        self.ensure_one()
        if self.dismantling_id:
            raise UserError('มี Dismantling Order อยู่แล้ว')
        if self.state != 'stocked':
            raise UserError('ต้องอยู่สถานะ In Stock ก่อน')

        dismantling = self.env['itx.revival.dismantling'].create({
            'acquired_id': self.id,
        })
        self.write({
            'dismantling_id': dismantling.id,
            'state': 'dismantling',
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dismantling Order',
            'res_model': 'itx.revival.dismantling',
            'res_id': dismantling.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_complete(self):
        """Mark as completed"""
        self.ensure_one()
        self.state = 'completed'

    def action_view_po(self):
        """View Purchase Order"""
        self.ensure_one()
        if not self.purchase_order_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'res_model': 'purchase.order',
            'res_id': self.purchase_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
