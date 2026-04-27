# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


DECISION_SELECTION = [
    ('not_buy', 'ไม่ซื้อ (คืน)'),
    ('sell_whole', 'ขายยกคัน (Broker)'),
    ('dismantle', 'ซื้อแยกอะไหล่'),
]

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('assessed', 'Assessed'),
    ('offering', 'Offering'),
    ('returned', 'Returned'),
    ('sold', 'Sold'),
    ('sold_paid', 'Sold & Paid'),
    ('dismantle', 'To Dismantle'),
]

OVERALL_CONDITION_SELECTION = [
    ('normal_wear', 'Normal Wear (เสื่อมสภาพปกติ)'),
    ('accident', 'Accident (อุบัติเหตุ)'),
    ('flood', 'Flood (น้ำท่วม)'),
    ('fire', 'Fire (ไฟไหม้)'),
    ('other', 'Other (อื่นๆ)'),
]

REGISTRATION_BOOK_STATUS_SELECTION = [
    ('unknown', 'ไม่ทราบ'),
    ('clean', 'ปกติ (ไม่แจ้งจอด)'),
    ('parking_stamped', 'แจ้งจอด'),
]

PARKING_REPORTED_PCT_PARAM = 'itx_revival_vehicle.parking_reported_pct'
PARKING_NOT_REPORTED_PCT_PARAM = 'itx_revival_vehicle.parking_not_reported_pct'
DEFAULT_PARKING_REPORTED_PCT = 0.15
DEFAULT_PARKING_NOT_REPORTED_PCT = 0.25

TARGET_ROI_WHOLE_CAR_PARAM = 'itx_revival_vehicle.target_roi_whole_car'
TARGET_ROI_DISMANTLE_PARAM = 'itx_revival_vehicle.target_roi_dismantle'
DEFAULT_TARGET_ROI_WHOLE_CAR = 0.20
DEFAULT_TARGET_ROI_DISMANTLE = 0.25


class ItxRevivalAssessment(models.Model):
    _name = 'itx.revival.assessment'
    _description = 'Vehicle Revival Assessment'
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

    # === Vehicle Information ===
    spec_id = fields.Many2one(
        comodel_name='itx.info.vehicle.spec',
        string='Vehicle Spec',
        required=True,
        index=True,
        tracking=True,
    )
    body_type_id = fields.Many2one(
        comodel_name='itx.info.vehicle.mgr.body.type',
        string='Body Type',
        related='spec_id.body_type_id',
        store=True,
        index=True,
    )
    brand_id = fields.Many2one(
        comodel_name='itx.info.vehicle.brand',
        string='Brand',
        related='spec_id.brand_id',
        store=True,
    )
    model_id = fields.Many2one(
        comodel_name='itx.info.vehicle.model',
        string='Model',
        related='spec_id.model_id',
        store=True,
    )
    generation_id = fields.Many2one(
        comodel_name='itx.info.vehicle.generation',
        string='Generation',
        related='spec_id.generation_id',
        store=True,
    )

    # === Vehicle Details ===
    vehicle_year = fields.Integer(string='Vehicle Year')
    vehicle_color = fields.Char(string='Vehicle Color')
    vehicle_mileage = fields.Integer(string='Mileage (km)')
    vehicle_vin = fields.Char(string='VIN', index=True)
    plate_number = fields.Char(string='Plate Number', index=True, tracking=True)
    plate_province = fields.Char(string='Plate Province')
    location = fields.Char(string='Location')

    # === Insurance Source ===
    insurance_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Insurance Company',
        domain="[('category_id.name', '=', 'บริษัทประกันภัย')]",
        tracking=True,
        help='บริษัทประกันภัยที่เสนอขายซาก',
    )
    ecf_claim_number = fields.Char(
        string='ECF Claim Number',
        index=True,
        tracking=True,
        help='เลขเคลมจากบริษัทประกัน (key identifier)',
    )
    claim_date = fields.Date(
        string='Claim Date',
        help='วันที่เกิดเหตุเคลม',
    )
    insurance_value = fields.Monetary(
        string='Insurance Value',
        currency_field='company_currency_id',
        tracking=True,
        help='ทุนประกัน (ถ้ามี — ใช้คำนวณราคา 15%/25%)',
    )
    registration_book_status = fields.Selection(
        selection=REGISTRATION_BOOK_STATUS_SELECTION,
        string='สถานะเล่มทะเบียน',
        default='unknown',
        tracking=True,
        help='unknown/clean → 25%, parking_stamped → 15%',
    )
    price_reported = fields.Monetary(
        string='Price (แจ้งจอด)',
        compute='_compute_two_prices',
        store=True,
        currency_field='company_currency_id',
        help='ราคาถ้าแจ้งจอด = ทุนประกัน × 15%',
    )
    price_not_reported = fields.Monetary(
        string='Price (ไม่แจ้งจอด)',
        compute='_compute_two_prices',
        store=True,
        currency_field='company_currency_id',
        help='ราคาถ้าไม่แจ้งจอด = ทุนประกัน × 25%',
    )
    suggested_price = fields.Monetary(
        string='Suggested Price',
        compute='_compute_suggested_price',
        store=True,
        currency_field='company_currency_id',
        help='ราคาเสนอซื้อ — ใช้ 25% เป็นทุนตั้งต้น (ปรับเมื่อรู้สถานะเล่ม)',
    )
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )

    # === Overall Condition (Field Survey) ===
    overall_condition = fields.Selection(
        selection=OVERALL_CONDITION_SELECTION,
        string='Overall Condition',
        help='สภาพโดยรวมของรถ (สายสืบกรอก)',
    )
    overall_condition_note = fields.Text(
        string='Overall Condition Note',
        help='อธิบายสภาพเพิ่มเติม',
    )

    # === Assessment Info ===
    assessor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Assessor',
    )
    assessment_date = fields.Date(
        string='Assessment Date',
        default=fields.Date.context_today,
    )

    # === Pricing ===
    asking_price = fields.Float(
        string='Asking Price',
        digits='Product Price',
    )
    target_price = fields.Monetary(
        string='Target Price',
        currency_field='company_currency_id',
        tracking=True,
        help='ราคาเป้าหมายที่ประเมินว่าจะซื้อซากได้ (ยังไม่ใช่ราคาตกลง — '
             'ราคาซื้อจริงจะอยู่ที่ Purchase Price ใน Acquired Vehicle)',
    )
    whole_car_op_cost = fields.Monetary(
        string='ค่าดำเนินการ (ยกคัน)',
        currency_field='company_currency_id',
        help='ค่าใช้จ่ายดำเนินการรวมสำหรับขายยกคัน เช่น ค่าขนส่ง, ค่านายหน้า, อื่นๆ',
    )
    dismantle_op_cost = fields.Monetary(
        string='ค่าดำเนินการ (แยกซาก)',
        currency_field='company_currency_id',
        help='ค่าใช้จ่ายดำเนินการรวมสำหรับแยกซาก เช่น ค่าขนส่ง, ค่าแรงงานแกะ, อื่นๆ',
    )

    # === ROI Path A: ขายยกคัน ===
    whole_car_revenue = fields.Monetary(
        string='รายได้คาด (ยกคัน)',
        compute='_compute_roi_analysis',
        store=True,
        currency_field='company_currency_id',
    )
    whole_car_total_cost = fields.Monetary(
        string='ต้นทุนรวม (ยกคัน)',
        compute='_compute_roi_analysis',
        store=True,
        currency_field='company_currency_id',
    )
    whole_car_profit = fields.Monetary(
        string='กำไรคาด (ยกคัน)',
        compute='_compute_roi_analysis',
        store=True,
        currency_field='company_currency_id',
    )
    whole_car_roi = fields.Float(
        string='ROI (ยกคัน) %',
        compute='_compute_roi_analysis',
        store=True,
        digits=(5, 2),
    )
    whole_car_meets_target = fields.Boolean(
        string='ผ่านเป้า (ยกคัน)',
        compute='_compute_roi_analysis',
        store=True,
    )

    # === ROI Path B: แยกซาก ===
    expected_revenue = fields.Monetary(
        string='รายได้คาด (แยกซาก)',
        compute='_compute_roi_analysis',
        store=True,
        currency_field='company_currency_id',
    )
    dismantle_total_cost = fields.Monetary(
        string='ต้นทุนรวม (แยกซาก)',
        compute='_compute_roi_analysis',
        store=True,
        currency_field='company_currency_id',
    )
    expected_profit = fields.Monetary(
        string='กำไรคาด (แยกซาก)',
        compute='_compute_roi_analysis',
        store=True,
        currency_field='company_currency_id',
    )
    expected_roi = fields.Float(
        string='ROI (แยกซาก) %',
        compute='_compute_roi_analysis',
        store=True,
        digits=(5, 2),
    )
    dismantle_meets_target = fields.Boolean(
        string='ผ่านเป้า (แยกซาก)',
        compute='_compute_roi_analysis',
        store=True,
    )

    # === ROI Recommendation ===
    recommended_path = fields.Selection(
        selection=[
            ('path_a', 'A: ขายยกคัน'),
            ('path_b', 'B: แยกซาก'),
            ('no_buy', 'ไม่ซื้อ'),
        ],
        string='แนะนำ',
        compute='_compute_roi_analysis',
        store=True,
    )

    # === Decision ===
    decision = fields.Selection(
        selection=DECISION_SELECTION,
        string='Decision',
        tracking=True,
    )
    decision_reason = fields.Text(
        string='เหตุผลที่เลือก',
        help='อธิบายเหตุผลว่าทำไมเลือก path นี้ (เช่น ROI สูงกว่า, มีลูกค้ารอ, สภาพรถเหมาะแยก)',
    )
    decision_note = fields.Text(string='Decision Note')
    decision_date = fields.Date(string='Decision Date')
    decision_by = fields.Many2one(comodel_name='res.users', string='Decision By')

    # === Offering (Wait State) ===
    offering_start_date = fields.Date(
        string='Offering Start Date',
        help='วันที่เริ่มเสนอขายยกคัน',
    )
    offering_deadline = fields.Date(
        string='Offering Deadline',
        tracking=True,
        help='deadline จากประกัน (ขายไม่ได้ภายในกำหนด ต้องคืน)',
    )
    offering_customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Buyer',
        help='ลูกค้าที่ซื้อยกคัน (กรอกเมื่อมีคนซื้อ)',
    )
    offering_sale_price = fields.Monetary(
        string='ราคาตั้งขาย (Plan)',
        currency_field='company_currency_id',
        help='ราคาตั้งขายยกคัน — ใช้คำนวณ ROI ตอนประเมิน',
    )
    agreed_sale_price = fields.Monetary(
        string='ราคาตกลงขาย (Actual)',
        currency_field='company_currency_id',
        help='ราคาขายจริงที่ตกลงกับลูกค้า (รวม VAT) — ใช้ออก SO',
    )
    suggested_sale_price = fields.Monetary(
        string='ราคาแนะนำขาย',
        compute='_compute_suggested_sale_price',
        store=True,
        currency_field='company_currency_id',
        help='ราคาแนะนำขายยกคัน = (Target Price + ค่าดำเนินการยกคัน) × 1.20',
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        related='acquired_id.sale_order_id',
        store=True,
    )
    is_offering_expired = fields.Boolean(
        string='Offering Expired',
        compute='_compute_is_offering_expired',
        search='_search_is_offering_expired',
    )

    # === State ===
    state = fields.Selection(
        selection=STATE_SELECTION,
        string='State',
        default='draft',
        required=True,
        tracking=True,
        index=True,
    )

    # === Lines ===
    line_ids = fields.One2many(
        comodel_name='itx.revival.assessment.line',
        inverse_name='assessment_id',
        string='Assessment Lines',
        copy=True,
    )
    line_count = fields.Integer(compute='_compute_line_count')


    # === Link to Acquired ===
    acquired_id = fields.Many2one(
        comodel_name='itx.revival.acquired',
        string='Acquired Vehicle',
        readonly=True,
        copy=False,
    )

    # === Images (Field Survey) ===
    image_main = fields.Image(
        string='Main Image',
        max_width=1920,
        max_height=1920,
        help='รูปหลัก (แสดงใน kanban/list)',
    )
    image_ids = fields.One2many(
        comodel_name='itx.revival.assessment.image',
        inverse_name='assessment_id',
        string='Images',
        copy=True,
    )
    image_count = fields.Integer(
        string='Image Count',
        compute='_compute_image_count',
    )

    # === Notes ===
    note = fields.Text(string='Notes')

    # === Compute ===
    def _get_parking_pcts(self):
        ICP = self.env['ir.config_parameter'].sudo()
        try:
            reported_pct = float(ICP.get_param(PARKING_REPORTED_PCT_PARAM, DEFAULT_PARKING_REPORTED_PCT))
        except (TypeError, ValueError):
            reported_pct = DEFAULT_PARKING_REPORTED_PCT
        try:
            not_reported_pct = float(ICP.get_param(PARKING_NOT_REPORTED_PCT_PARAM, DEFAULT_PARKING_NOT_REPORTED_PCT))
        except (TypeError, ValueError):
            not_reported_pct = DEFAULT_PARKING_NOT_REPORTED_PCT
        return reported_pct, not_reported_pct

    @api.depends('insurance_value')
    def _compute_two_prices(self):
        reported_pct, not_reported_pct = self._get_parking_pcts()
        for rec in self:
            val = rec.insurance_value or 0.0
            rec.price_reported = val * reported_pct
            rec.price_not_reported = val * not_reported_pct

    @api.depends('insurance_value', 'registration_book_status')
    def _compute_suggested_price(self):
        reported_pct, not_reported_pct = self._get_parking_pcts()
        for rec in self:
            pct = reported_pct if rec.registration_book_status == 'parking_stamped' else not_reported_pct
            rec.suggested_price = (rec.insurance_value or 0.0) * pct

    @api.depends('target_price', 'whole_car_op_cost')
    def _compute_suggested_sale_price(self):
        target_roi_a, _ = self._get_target_roi_pcts()
        for rec in self:
            cost = (rec.target_price or 0.0) + (rec.whole_car_op_cost or 0.0)
            rec.suggested_sale_price = cost * (1 + target_roi_a) if cost else 0.0

    def _get_target_roi_pcts(self):
        ICP = self.env['ir.config_parameter'].sudo()
        try:
            whole_car = float(ICP.get_param(TARGET_ROI_WHOLE_CAR_PARAM, DEFAULT_TARGET_ROI_WHOLE_CAR))
        except (TypeError, ValueError):
            whole_car = DEFAULT_TARGET_ROI_WHOLE_CAR
        try:
            dismantle = float(ICP.get_param(TARGET_ROI_DISMANTLE_PARAM, DEFAULT_TARGET_ROI_DISMANTLE))
        except (TypeError, ValueError):
            dismantle = DEFAULT_TARGET_ROI_DISMANTLE
        return whole_car, dismantle

    @api.depends('line_ids.expected_price', 'line_ids.qty_expected',
                 'target_price', 'whole_car_op_cost', 'dismantle_op_cost',
                 'offering_sale_price')
    def _compute_roi_analysis(self):
        target_roi_a, target_roi_b = self._get_target_roi_pcts()
        for rec in self:
            buy_cost = rec.target_price or 0.0
            cost_a = buy_cost + (rec.whole_car_op_cost or 0.0)
            cost_b = buy_cost + (rec.dismantle_op_cost or 0.0)

            # Path A: ขายยกคัน
            rec.whole_car_revenue = rec.offering_sale_price or 0.0
            rec.whole_car_total_cost = cost_a
            rec.whole_car_profit = rec.whole_car_revenue - cost_a
            rec.whole_car_roi = (
                rec.whole_car_profit / cost_a if cost_a else 0
            )
            rec.whole_car_meets_target = rec.whole_car_roi >= target_roi_a

            # Path B: แยกซาก
            rec.expected_revenue = sum(
                l.expected_price * l.qty_expected for l in rec.line_ids
            )
            rec.dismantle_total_cost = cost_b
            rec.expected_profit = rec.expected_revenue - cost_b
            rec.expected_roi = (
                rec.expected_profit / cost_b if cost_b else 0
            )
            rec.dismantle_meets_target = rec.expected_roi >= target_roi_b

            # Recommendation
            a_ok = rec.whole_car_meets_target and rec.whole_car_revenue > 0
            b_ok = rec.dismantle_meets_target and rec.expected_revenue > 0
            if a_ok and b_ok:
                rec.recommended_path = 'path_a' if rec.whole_car_roi >= rec.expected_roi else 'path_b'
            elif a_ok:
                rec.recommended_path = 'path_a'
            elif b_ok:
                rec.recommended_path = 'path_b'
            else:
                rec.recommended_path = 'no_buy'

    @api.depends('offering_deadline')
    def _compute_is_offering_expired(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_offering_expired = (
                rec.offering_deadline and rec.offering_deadline < today
            )

    def _search_is_offering_expired(self, operator, value):
        today = fields.Date.context_today(self)
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('offering_deadline', '<', today), ('offering_deadline', '!=', False)]
        return ['|', ('offering_deadline', '>=', today), ('offering_deadline', '=', False)]

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.depends('image_ids')
    def _compute_image_count(self):
        for rec in self:
            rec.image_count = len(rec.image_ids)

    # === CRUD ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'itx.revival.assessment'
                ) or 'New'
        return super().create(vals_list)

    def write(self, vals):
        if 'registration_book_status' in vals:
            self._notify_book_status_change(vals['registration_book_status'])
        return super().write(vals)

    def _notify_book_status_change(self, new_status):
        """Post chatter message when registration book status changes, listing affected documents."""
        status_labels = dict(REGISTRATION_BOOK_STATUS_SELECTION)
        reported_pct, not_reported_pct = self._get_parking_pcts()
        for rec in self:
            old_status = rec.registration_book_status
            if old_status == new_status:
                continue
            old_label = status_labels.get(old_status, old_status)
            new_label = status_labels.get(new_status, new_status)
            old_pct = reported_pct if old_status == 'parking_stamped' else not_reported_pct
            new_pct = reported_pct if new_status == 'parking_stamped' else not_reported_pct
            if old_pct == new_pct:
                continue

            val = rec.insurance_value or 0.0
            old_price = val * old_pct
            new_price = val * new_pct

            lines = [
                f'<strong>⚠ สถานะเล่มเปลี่ยน:</strong> {old_label} → {new_label}',
                f'ราคาเปลี่ยนจาก {old_pct:.0%} (฿{old_price:,.0f}) → {new_pct:.0%} (฿{new_price:,.0f})',
                '',
                '<strong>เอกสารที่ต้องตรวจสอบ:</strong>',
            ]
            if rec.acquired_id:
                acq = rec.acquired_id
                if acq.purchase_order_id:
                    lines.append(f'• PO: {acq.purchase_order_id.name} — ปรับราคาจาก ฿{old_price:,.0f} → ฿{new_price:,.0f}')
                if acq.sale_order_id:
                    if new_pct < old_pct:
                        lines.append(f'• SO: {acq.sale_order_id.name} — อาจต้องคืนส่วนต่างลูกค้า')
                    else:
                        lines.append(f'• SO: {acq.sale_order_id.name} — อาจต้องเรียกเก็บเพิ่ม')
                if not acq.purchase_order_id and not acq.sale_order_id:
                    lines.append('• Acquired Vehicle: ยังไม่มี PO/SO — ราคาจะอัพเดทอัตโนมัติ')
            else:
                lines.append('• ยังไม่มี Acquired Vehicle — ราคา suggested_price อัพเดทอัตโนมัติ')

            rec.message_post(
                body='<br/>'.join(lines),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

    # === Generate Lines ===
    def action_generate_lines(self):
        """Generate assessment lines from Template BOM (body_type level)"""
        self.ensure_one()

        if not self.spec_id or not self.body_type_id:
            raise UserError('กรุณาเลือก Vehicle Spec ที่มี Body Type ก่อน')

        self.line_ids.unlink()

        # 1. Read Template BOM for this body type
        templates = self.env['itx.info.vehicle.template.bom'].search([
            ('body_type_id', '=', self.body_type_id.id),
            ('active', '=', True),
        ], order='sequence, id')

        if not templates:
            raise UserError(
                f'ไม่พบ BOM Template สำหรับ Body Type: {self.body_type_id.name}'
            )

        # 2. Ensure salvage vehicle product exists
        self._get_or_create_salvage_product()

        # 3. Fallback origin/condition
        PartOrigin = self.env['itx.info.vehicle.part.origin']
        PartCondition = self.env['itx.info.vehicle.part.condition']
        fallback_origin = PartOrigin.search([('is_default', '=', True)], limit=1) \
            or PartOrigin.search([('code', '=', 'OEM')], limit=1)
        fallback_condition = PartCondition.search([('is_default', '=', True)], limit=1) \
            or PartCondition.search([('code', '=', 'GOOD')], limit=1)

        # 4. Create assessment lines from templates
        total_parts = len(templates)
        default_weight = 100.0 / total_parts if total_parts else 0

        lines_data = []
        for seq, tmpl in enumerate(templates, start=1):
            origin = tmpl.default_part_origin_id or fallback_origin
            condition = tmpl.default_part_condition_id or fallback_condition
            product = self._get_or_create_part_product(tmpl.part_template_id, origin, condition)

            lines_data.append({
                'assessment_id': self.id,
                'sequence': seq * 10,
                'part_name_id': tmpl.part_template_id.id,
                'product_id': product.id if product else False,
                'part_origin_id': origin.id if origin else False,
                'part_condition_id': condition.id if condition else False,
                'qty_expected': tmpl.qty or 1,
                'qty_found': tmpl.qty or 1,
                'expected_price': 0.0,
                'cost_weight': tmpl.cost_weight or default_weight,
                'is_found': True,
            })

        self.env['itx.revival.assessment.line'].create(lines_data)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'สร้างรายการอะไหล่แล้ว',
                'message': f'สร้าง {len(lines_data)} รายการจาก Template BOM ({self.body_type_id.name})',
                'type': 'success',
                'sticky': False,
            }
        }

    def _get_or_create_salvage_product(self):
        """Get or create salvage vehicle product as vehicle part (UK applies)"""
        self.ensure_one()
        TemplatePart = self.env['itx.info.vehicle.template.part']
        PartOrigin = self.env['itx.info.vehicle.part.origin']
        PartCondition = self.env['itx.info.vehicle.part.condition']

        # Get or create "Salvage Vehicle" template part
        salvage_part = TemplatePart.search([('code', '=', 'SALVAGE')], limit=1)
        if not salvage_part:
            # Find or create category
            PartCategory = self.env['itx.info.vehicle.part.category']
            cat = PartCategory.search([('code', '=', 'VEHICLE')], limit=1)
            if not cat:
                cat = PartCategory.create({
                    'code': 'VEHICLE',
                    'name': 'Vehicle (ตัวรถ)',
                    'abbr': 'VH',
                })
            salvage_part = TemplatePart.create({
                'code': 'SALVAGE',
                'name': 'Salvage Vehicle (ซากรถ)',
                'abbr': 'SAL',
                'category_id': cat.id,
            })

        origin = PartOrigin.search([('is_default', '=', True)], limit=1) \
            or PartOrigin.search([('code', '=', 'OEM')], limit=1)
        condition = PartCondition.search([('is_default', '=', True)], limit=1) \
            or PartCondition.search([('code', '=', 'GOOD')], limit=1)

        if not origin or not condition:
            raise UserError('ไม่พบ Part Origin หรือ Part Condition ที่เป็น default ใน master data')

        # Use standard vehicle part lookup (UK: spec + part_name + origin + condition)
        variant = self._get_or_create_part_product(salvage_part, origin, condition)
        # Salvage vehicle must be tracked by serial (1 car = 1 unique VIN)
        if variant:
            tmpl = variant.product_tmpl_id
            if tmpl.tracking != 'serial':
                tmpl.tracking = 'serial'
            if tmpl.purchase_method != 'purchase':
                tmpl.purchase_method = 'purchase'
        return variant

    def _get_or_create_part_product(self, part_template, origin, condition):
        """Lookup or create product.product variant for spec + part + origin × condition.

        Step 1: Find/create product.template by UK (spec, part_name)
        Step 2: Ensure dynamic attributes (Origin + Condition) on template
        Step 3: Create/find variant for origin × condition combination
        Return: product.product (variant)
        """
        self.ensure_one()
        if not origin or not condition:
            return False

        ProductTemplate = self.env['product.template']

        # Step 1: Find or create template by (spec, part_name)
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

        # Step 2+3: Create/find variant via template helper
        return tmpl._get_or_create_variant(origin, condition)

    # === State Actions ===

    # --- draft → assessed ---
    def action_assess(self):
        self.ensure_one()
        if not self.spec_id:
            raise UserError('กรุณาเลือก Vehicle Spec ก่อน')
        if not self.body_type_id:
            raise UserError('Vehicle Spec นี้ไม่มี Body Type กรุณาตั้งค่าใน Spec')
        if not self.line_ids:
            raise UserError('กรุณา Generate Lines ก่อน')
        if not self.target_price:
            raise UserError('กรุณากรอก Target Price ก่อน Complete Assessment')
        self.state = 'assessed'

    # --- assessed → returned (Path 1: ไม่สนใจ) ---
    def action_return(self):
        self.ensure_one()
        self._write_decision('not_buy', 'returned')

    # --- assessed → dismantle (Path 2: ซื้อแยกอะไหล่) ---
    def action_decide_dismantle(self):
        self.ensure_one()
        self._write_decision('dismantle', 'dismantle')

    # --- assessed → offering (Path 3: เสนอขายยกคัน) ---
    def action_offer(self):
        self.ensure_one()
        if not self.offering_deadline:
            raise UserError('กรุณากรอก Offering Deadline ก่อน')
        self.write({
            'decision': 'sell_whole',
            'decision_date': fields.Date.context_today(self),
            'decision_by': self.env.user.id,
            'offering_start_date': fields.Date.context_today(self),
            'state': 'offering',
        })

    # --- offering → sold (ตกลงขาย → สร้าง Acquired + SO dropship) ---
    def action_sold(self):
        self.ensure_one()
        if not self.offering_customer_id:
            raise UserError('กรุณาเลือก Buyer ก่อน')
        if not self.agreed_sale_price:
            raise UserError('กรุณากรอก ราคาตกลงขาย (Actual) ก่อน')
        if not self.vehicle_vin:
            raise UserError('กรุณากรอก VIN ก่อนตกลงขาย')
        if not self.insurance_partner_id:
            raise UserError('กรุณาระบุ Insurance Company (Vendor) ก่อน')
        if self.acquired_id:
            raise UserError('มี Acquired Vehicle อยู่แล้ว')

        # 1. สร้าง Acquired
        acquired = self.env['itx.revival.acquired'].create({
            'assessment_id': self.id,
            'vin': self.vehicle_vin,
            'vehicle_year': self.vehicle_year,
            'vehicle_color': self.vehicle_color,
            'vehicle_mileage': self.vehicle_mileage,
            'purchase_price': self.target_price or self.price_not_reported or 0.0,
            'vendor_id': self.insurance_partner_id.id,
            'customer_id': self.offering_customer_id.id,
        })
        self.acquired_id = acquired.id

        # 2. Override sale price ให้ใช้ agreed_sale_price (รวม VAT)
        acquired.assessment_id.offering_sale_price = self.agreed_sale_price

        # 3. Trigger standard dropship flow (SO + confirm + auto PO)
        acquired.action_create_so_dropship()

        self.state = 'sold'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'ตกลงขายสำเร็จ',
                'message': f'สร้าง Acquired {acquired.name} + SO {acquired.sale_order_id.name} เรียบร้อย',
                'type': 'success',
                'sticky': False,
            }
        }

    # --- sold → sold_paid (จ่ายครบ — ตรวจจาก invoice status) ---
    def action_sold_paid(self):
        self.ensure_one()
        so = self.sale_order_id
        if not so:
            raise UserError('ยังไม่มี Sale Order')
        if so.invoice_status != 'invoiced':
            raise UserError(
                f'SO {so.name} ยังไม่ได้ออก Invoice ครบ '
                f'(สถานะปัจจุบัน: {so.invoice_status})'
            )
        invoices = so.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_invoice'
        )
        unpaid = invoices.filtered(
            lambda inv: inv.payment_state not in ('paid', 'in_payment')
        )
        if unpaid:
            names = ', '.join(unpaid.mapped('name'))
            raise UserError(f'ยังมี Invoice ที่ยังไม่จ่ายครบ: {names}')
        self.state = 'sold_paid'

    # --- offering → returned (หมดเวลา / ยกเลิก) ---
    def action_offering_return(self):
        self.ensure_one()
        self.write({
            'decision': 'not_buy',
            'state': 'returned',
        })

    # --- offering → dismantle (เปลี่ยนใจซื้อแยก) ---
    def action_offering_dismantle(self):
        self.ensure_one()
        self.write({
            'decision': 'dismantle',
            'state': 'dismantle',
        })

    # --- any state → draft (reset for testing) ---
    def action_reset_draft(self):
        self.ensure_one()
        if self.state == 'draft':
            return
        self.write({
            'state': 'draft',
            'decision': False,
            'decision_date': False,
            'decision_by': False,
            'offering_start_date': False,
            'offering_customer_id': False,
            'agreed_sale_price': False,
        })

    def action_view_acquired(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Acquired Vehicle',
            'res_model': 'itx.revival.acquired',
            'res_id': self.acquired_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # --- dismantle → create Acquired record (Path B only) ---
    def action_create_acquired(self):
        self.ensure_one()
        if self.state != 'dismantle':
            raise UserError('ต้องอยู่สถานะ To Dismantle ก่อน')
        if self.acquired_id:
            raise UserError('มี Acquired Vehicle อยู่แล้ว')

        acquired = self.env['itx.revival.acquired'].create({
            'assessment_id': self.id,
            'vin': self.vehicle_vin or '',
            'vehicle_year': self.vehicle_year,
            'vehicle_color': self.vehicle_color,
            'vehicle_mileage': self.vehicle_mileage,
            'purchase_price': self.target_price or self.price_not_reported or 0.0,
            'vendor_id': self.insurance_partner_id.id if self.insurance_partner_id else False,
        })
        self.acquired_id = acquired.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Acquired Vehicle',
            'res_model': 'itx.revival.acquired',
            'res_id': acquired.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _write_decision(self, decision, state):
        self.write({
            'decision': decision,
            'decision_date': fields.Date.context_today(self),
            'decision_by': self.env.user.id,
            'state': state,
        })

    def action_print_checklist(self):
        self.ensure_one()
        # TODO: Implement report
        raise UserError('PDF Checklist ยังไม่พร้อมใช้งาน')

    def action_view_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assessment Lines',
            'res_model': 'itx.revival.assessment.line',
            'view_mode': 'list',
            'domain': [('assessment_id', '=', self.id)],
            'context': {'default_assessment_id': self.id},
        }

    def action_view_images(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assessment Images',
            'res_model': 'itx.revival.assessment.image',
            'view_mode': 'kanban,form',
            'domain': [('assessment_id', '=', self.id)],
            'context': {'default_assessment_id': self.id},
        }

    # === Variant Helpers ===
    def _get_origin_condition_from_variant(self, product_product):
        """Extract origin/condition master records from a product.product variant.

        Traces: variant → attribute_values → origin/condition master data
        via attribute_value_id field on part.origin / part.condition.

        :param product_product: product.product record (variant)
        :return: tuple (origin_record, condition_record)
        """
        PartOrigin = self.env['itx.info.vehicle.part.origin']
        PartCondition = self.env['itx.info.vehicle.part.condition']

        attr_value_ids = product_product.product_template_attribute_value_ids.mapped(
            'product_attribute_value_id'
        )

        origin = PartOrigin.search([
            ('attribute_value_id', 'in', attr_value_ids.ids),
        ], limit=1)
        condition = PartCondition.search([
            ('attribute_value_id', 'in', attr_value_ids.ids),
        ], limit=1)

        return origin, condition
