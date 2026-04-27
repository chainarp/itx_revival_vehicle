# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


ACQUIRED_STATE_SELECTION = [
    ('draft', 'Draft'),
    ('po_created', 'PO Created'),
    ('releasing', 'Releasing'),
    # Path B only (dismantle):
    ('stocked', 'In Stock'),
    ('dismantling', 'Dismantling'),
    ('parts_ready', 'Parts Ready'),
    # Path A only (broker/sell_whole):
    ('delivered', 'Delivered'),
    # Common settlement:
    ('settling', 'Settling'),
    ('closed', 'Closed'),
]

OWNERSHIP_TRANSFER_STATUS = [
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('not_applicable', 'N/A'),
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

    # === Invoice/Bill Links ===
    vendor_bill_count = fields.Integer(
        compute='_compute_invoice_counts',
    )
    customer_invoice_count = fields.Integer(
        compute='_compute_invoice_counts',
    )

    # === ROI Computed ===
    expected_revenue = fields.Monetary(
        related='assessment_id.expected_revenue',
        string='Expected Revenue',
        currency_field='company_currency_id',
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

    # === Release Document (ใบปล่อยรถ) ===
    release_request_date = fields.Date(
        string='Release Request Date',
        help='วันที่ขอใบปล่อยรถจากประกัน',
    )
    release_doc_date = fields.Date(
        string='Release Doc Received',
        help='วันที่ได้รับใบปล่อยรถ',
    )
    release_note = fields.Char(
        string='Release Note',
        help='หมายเหตุใบปล่อยรถ',
    )

    # === Settlement (ชำระค่าซาก) ===
    payment_to_insurance_date = fields.Date(
        string='Payment Date',
        help='วันที่โอนค่าซากให้ประกัน',
    )
    payment_to_insurance_amount = fields.Monetary(
        string='Payment Amount',
        currency_field='company_currency_id',
        help='จำนวนเงินที่โอนให้ประกัน',
    )
    registration_book_received_date = fields.Date(
        string='Reg. Book Received',
        help='วันที่ได้รับเล่มทะเบียน',
    )
    ownership_transfer_status = fields.Selection(
        selection=OWNERSHIP_TRANSFER_STATUS,
        string='Ownership Transfer',
        default='pending',
        tracking=True,
    )
    ownership_transfer_date = fields.Date(
        string='Transfer Date',
        help='วันที่โอนกรรมสิทธิ์สำเร็จ',
    )
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )

    # === Path A: Broker/Sell Whole ===
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        readonly=True,
        copy=False,
        help='SO ขายยกคัน (dropship)',
    )
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        help='ลูกค้าที่ซื้อยกคัน',
    )
    delivery_date = fields.Date(
        string='Delivery Date',
        help='วันที่ลูกค้ารับรถ',
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
    def _compute_invoice_counts(self):
        for rec in self:
            if rec.purchase_order_id:
                rec.vendor_bill_count = len(rec.purchase_order_id.invoice_ids.filtered(
                    lambda m: m.move_type == 'in_invoice'
                ))
            else:
                rec.vendor_bill_count = 0
            if rec.sale_order_id:
                rec.customer_invoice_count = len(rec.sale_order_id.invoice_ids.filtered(
                    lambda m: m.move_type == 'out_invoice'
                ))
            else:
                rec.customer_invoice_count = 0

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

    def _ensure_product(self):
        if not self.product_id:
            bom = self.env['mrp.bom'].search([
                ('itx_spec_id', '=', self.spec_id.id),
            ], limit=1)
            if bom and bom.product_id:
                self.product_id = bom.product_id.id
            else:
                raise UserError('ไม่พบ Vehicle Product กรุณา Generate Lines ใน Assessment ก่อน')

    def _get_or_create_vin_lot(self):
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
            lot.write({'itx_vin': self.vin, 'itx_acquired_id': self.id})
        return lot

    def _prefill_picking_vin_lot(self, picking):
        """Pre-fill lot/serial (VIN) on picking move lines — ไม่ validate ให้ user กดเอง."""
        if not picking or picking.state in ('done', 'cancel'):
            return
        self._ensure_product()
        if not self.vin:
            return

        vehicle_move = picking.move_ids.filtered(
            lambda m: m.product_id.id == self.product_id.id
        )[:1]
        if not vehicle_move:
            return

        if picking.state == 'draft':
            picking.action_confirm()
        picking.action_assign()

        lot = self._get_or_create_vin_lot()

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
            (move_lines - first).unlink()

    # --- draft → po_created (Path B: dismantle — PO ตรง) ---
    def action_create_po(self):
        self.ensure_one()
        if self.purchase_order_id:
            raise UserError('มี Purchase Order อยู่แล้ว')
        if not self.vendor_id:
            raise UserError('กรุณาระบุ Vendor ก่อน')
        if not self.purchase_price:
            raise UserError('กรุณาระบุ Purchase Price ก่อน')

        self._ensure_product()

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
        if self.analytic_account_id:
            for line in po.order_line:
                line.analytic_distribution = {str(self.analytic_account_id.id): 100}

        self.write({
            'purchase_order_id': po.id,
            'state': 'po_created',
        })

    # --- draft → po_created (Path A: sell_whole — SO + dropship auto PO) ---
    def action_create_so_dropship(self):
        self.ensure_one()
        if self.sale_order_id:
            raise UserError('มี Sale Order อยู่แล้ว')
        if not self.customer_id:
            raise UserError('กรุณาระบุ Customer ก่อน')
        if not self.vendor_id:
            raise UserError('กรุณาระบุ Vendor (ประกัน) ก่อน')
        if not self.purchase_price:
            raise UserError('กรุณาระบุ Purchase Price ก่อน')

        self._ensure_product()
        product = self.product_id

        # Ensure dropship route on product
        dropship_route = self.env.ref(
            'stock_dropshipping.route_drop_shipping', raise_if_not_found=False,
        )
        if dropship_route and dropship_route not in product.route_ids:
            product.route_ids = [(4, dropship_route.id)]

        # Ensure vendor (supplierinfo) with correct price
        supplierinfo = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('partner_id', '=', self.vendor_id.id),
        ], limit=1)
        if supplierinfo:
            supplierinfo.price = self.purchase_price
        else:
            self.env['product.supplierinfo'].create({
                'product_tmpl_id': product.product_tmpl_id.id,
                'partner_id': self.vendor_id.id,
                'price': self.purchase_price,
                'min_qty': 1,
            })

        # Determine sale price (agreed > offering > purchase)
        sale_price = (
            self.assessment_id.agreed_sale_price
            or self.assessment_id.offering_sale_price
            or self.purchase_price
        )

        # Create SO
        so = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'origin': self.name,
        })
        self.env['sale.order.line'].create({
            'order_id': so.id,
            'product_id': product.id,
            'name': f'{product.display_name} - VIN: {self.vin}',
            'product_uom_qty': 1,
            'price_unit': sale_price,
        })
        if self.analytic_account_id:
            for line in so.order_line:
                line.analytic_distribution = {str(self.analytic_account_id.id): 100}

        # Confirm SO → triggers dropship procurement → auto PO
        so.action_confirm()

        # Retrieve auto-created PO from dropship
        po = self.env['purchase.order'].search([
            ('origin', 'ilike', so.name),
            ('partner_id', '=', self.vendor_id.id),
        ], limit=1, order='id desc')

        # Confirm PO
        if po and po.state in ('draft', 'sent'):
            po.button_confirm()

        # Pre-fill VIN lot on dropship picking (user validates manually)
        dropship_picking = (so.picking_ids | (po.picking_ids if po else self.env['stock.picking'])).filtered(
            lambda p: p.state not in ('done', 'cancel')
        )[:1]
        if dropship_picking:
            self._prefill_picking_vin_lot(dropship_picking)

        # Create Vendor Bill (draft — ไม่ post ให้ user ตรวจก่อน)
        if po and po.state == 'purchase' and po.invoice_status == 'to invoice':
            po.action_create_invoice()

        # Create Customer Invoice (draft — ไม่ post ให้ user ตรวจก่อน)
        if so.state == 'sale':
            so._create_invoices()

        self.write({
            'sale_order_id': so.id,
            'purchase_order_id': po.id if po else False,
            'state': 'po_created',
        })

    # --- helpers: check payment status ---
    def _get_unpaid_vendor_bills(self):
        if not self.purchase_order_id:
            return self.env['account.move']
        return self.purchase_order_id.invoice_ids.filtered(
            lambda m: m.move_type == 'in_invoice' and m.payment_state not in ('paid', 'in_payment')
        )

    def _get_unpaid_customer_invoices(self):
        if not self.sale_order_id:
            return self.env['account.move']
        return self.sale_order_id.invoice_ids.filtered(
            lambda m: m.move_type == 'out_invoice' and m.payment_state not in ('paid', 'in_payment')
        )

    # --- po_created → releasing ---
    def action_request_release(self):
        self.ensure_one()
        # Path A (sell_whole): ลูกค้าต้องจ่ายครบก่อนขอปล่อยรถ
        if self.decision == 'sell_whole':
            unpaid = self._get_unpaid_customer_invoices()
            if unpaid:
                names = ', '.join(unpaid.mapped('display_name'))
                raise UserError(
                    f'ลูกค้ายังจ่ายเงินไม่ครบ ไม่สามารถขอใบปล่อยได้\n'
                    f'Invoice ค้างจ่าย: {names}'
                )
        self.write({
            'release_request_date': fields.Date.context_today(self),
            'state': 'releasing',
        })

    # --- releasing → stocked (Path B: รถเข้าโกดัง) ---
    def action_confirm_stock(self):
        """Validate PO incoming picking with VIN lot → state=stocked."""
        self.ensure_one()
        if self.state != 'releasing':
            raise UserError('ต้องอยู่สถานะ Releasing ก่อน')
        if not self.purchase_order_id:
            raise UserError('ไม่มี Purchase Order ผูกไว้')

        picking = self.purchase_order_id.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'incoming' and p.state not in ('done', 'cancel')
        )[:1]
        if not picking:
            raise UserError('ไม่พบ Incoming Picking ที่ยังไม่ done ของ PO นี้')

        self._prefill_picking_vin_lot(picking)
        self.state = 'stocked'

    # --- stocked → dismantling (Path B) ---
    def action_create_dismantling(self):
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

    # --- releasing → delivered (Path A: ลูกค้ารับรถ dropship) ---
    def action_delivered(self):
        self.ensure_one()
        if self.sale_order_id:
            pickings = self.sale_order_id.picking_ids.filtered(
                lambda p: p.state != 'done'
            )
            if pickings:
                names = ', '.join(pickings.mapped('display_name'))
                raise UserError(
                    f'ยังมี Delivery Order ที่ยัง validate ไม่เสร็จ\n'
                    f'กรุณา validate ก่อน: {names}'
                )
        self.write({
            'delivery_date': fields.Date.context_today(self),
            'state': 'delivered',
        })

    # --- parts_ready / delivered → settling ---
    def action_settle(self):
        self.ensure_one()
        if self.state not in ('parts_ready', 'delivered'):
            raise UserError('ต้องอยู่สถานะ Parts Ready หรือ Delivered ก่อน')
        self.state = 'settling'

    # --- settling → closed ---
    def action_close(self):
        self.ensure_one()
        errors = []
        # ตรวจ Vendor Bill (จ่ายค่าซากให้ประกัน)
        unpaid_bills = self._get_unpaid_vendor_bills()
        if unpaid_bills:
            names = ', '.join(unpaid_bills.mapped('display_name'))
            errors.append(f'Vendor Bill ยังไม่จ่าย: {names}')
        elif not self.purchase_order_id.invoice_ids.filtered(lambda m: m.move_type == 'in_invoice'):
            errors.append('ยังไม่มี Vendor Bill (ยังไม่ได้จ่ายค่าซากให้ประกัน)')
        # ตรวจ Customer Invoice (รับเงินจากลูกค้า) — เฉพาะ sell_whole
        if self.decision == 'sell_whole':
            unpaid_inv = self._get_unpaid_customer_invoices()
            if unpaid_inv:
                names = ', '.join(unpaid_inv.mapped('display_name'))
                errors.append(f'Customer Invoice ยังไม่รับเงิน: {names}')
        if errors:
            raise UserError('ไม่สามารถปิดเคสได้:\n• ' + '\n• '.join(errors))
        self.state = 'closed'

    # --- any state → draft (reset for testing) ---
    def action_reset_draft(self):
        self.ensure_one()
        if self.state == 'draft':
            return
        self.write({'state': 'draft'})

    # === Navigation ===
    def action_view_po(self):
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

    def action_view_so(self):
        self.ensure_one()
        if not self.sale_order_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_vendor_bill(self):
        self.ensure_one()
        bills = self.purchase_order_id.invoice_ids.filtered(
            lambda m: m.move_type == 'in_invoice'
        )
        if len(bills) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Vendor Bill',
                'res_model': 'account.move',
                'res_id': bills.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bills',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', bills.ids)],
        }

    def action_view_customer_invoice(self):
        self.ensure_one()
        invoices = self.sale_order_id.invoice_ids.filtered(
            lambda m: m.move_type == 'out_invoice'
        )
        if len(invoices) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Customer Invoice',
                'res_model': 'account.move',
                'res_id': invoices.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices.ids)],
        }
