# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


DECISION_SELECTION = [
    ('not_buy', 'ไม่ซื้อ'),
    ('sell_whole', 'ซื้อขายทั้งคัน'),
    ('dismantle', 'ซื้อแตก Part'),
]

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('preparing', 'Preparing'),
    ('complete', 'Complete'),
    ('cancelled', 'Cancelled'),
    ('acquired', 'Acquired'),
]

OVERALL_CONDITION_SELECTION = [
    ('normal_wear', 'Normal Wear (เสื่อมสภาพปกติ)'),
    ('accident', 'Accident (อุบัติเหตุ)'),
    ('flood', 'Flood (น้ำท่วม)'),
    ('fire', 'Fire (ไฟไหม้)'),
    ('other', 'Other (อื่นๆ)'),
]

REGISTRATION_BOOK_STATUS_SELECTION = [
    ('clean', 'Clean (ปกติ)'),
    ('parking_stamped', 'Parking Stamped (ประทับแจ้งจอด)'),
    ('lost', 'Lost (เล่มหาย)'),
    ('unknown', 'Unknown (ไม่ทราบ)'),
]

PARKING_REPORTED_PCT_PARAM = 'itx_revival_vehicle.parking_reported_pct'
PARKING_NOT_REPORTED_PCT_PARAM = 'itx_revival_vehicle.parking_not_reported_pct'
DEFAULT_PARKING_REPORTED_PCT = 0.15
DEFAULT_PARKING_NOT_REPORTED_PCT = 0.25


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
        help='ทุนประกันของรถคันนี้',
    )
    is_parking_reported = fields.Boolean(
        string='Parking Reported',
        default=False,
        tracking=True,
        help='เจ้าของแจ้งจอดกับกรมขนส่งแล้วหรือยัง — มีผลต่อราคาเสนอซื้อ',
    )
    registration_book_status = fields.Selection(
        selection=REGISTRATION_BOOK_STATUS_SELECTION,
        string='Registration Book Status',
        default='unknown',
        help='สภาพเล่มทะเบียน',
    )
    suggested_price = fields.Monetary(
        string='Suggested Price',
        compute='_compute_suggested_price',
        store=True,
        currency_field='company_currency_id',
        help='ราคาเสนอซื้อ = ทุนประกัน × % ตามสถานะแจ้งจอด (อ่านจาก system parameter)',
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
    target_price = fields.Float(
        string='Target Price',
        digits='Product Price',
        tracking=True,
    )
    expected_revenue = fields.Float(
        string='Expected Revenue',
        compute='_compute_expected_values',
        store=True,
        digits='Product Price',
    )
    expected_profit = fields.Float(
        string='Expected Profit',
        compute='_compute_expected_values',
        store=True,
        digits='Product Price',
    )
    expected_roi = fields.Float(
        string='Expected ROI (%)',
        compute='_compute_expected_values',
        store=True,
        digits=(5, 2),
    )

    # === Decision ===
    decision = fields.Selection(
        selection=DECISION_SELECTION,
        string='Decision',
        tracking=True,
    )
    decision_note = fields.Text(string='Decision Note')
    decision_date = fields.Date(string='Decision Date')
    decision_by = fields.Many2one(comodel_name='res.users', string='Decision By')

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

    # === BOM Link ===
    bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        string='Spec BOM',
        readonly=True,
        copy=False,
        help='Spec-level BOM (master data)',
    )

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
    @api.depends('insurance_value', 'is_parking_reported')
    def _compute_suggested_price(self):
        ICP = self.env['ir.config_parameter'].sudo()
        try:
            reported_pct = float(ICP.get_param(PARKING_REPORTED_PCT_PARAM, DEFAULT_PARKING_REPORTED_PCT))
        except (TypeError, ValueError):
            reported_pct = DEFAULT_PARKING_REPORTED_PCT
        try:
            not_reported_pct = float(ICP.get_param(PARKING_NOT_REPORTED_PCT_PARAM, DEFAULT_PARKING_NOT_REPORTED_PCT))
        except (TypeError, ValueError):
            not_reported_pct = DEFAULT_PARKING_NOT_REPORTED_PCT
        for rec in self:
            pct = reported_pct if rec.is_parking_reported else not_reported_pct
            rec.suggested_price = (rec.insurance_value or 0.0) * pct

    @api.depends('line_ids.expected_price', 'line_ids.qty_expected', 'target_price')
    def _compute_expected_values(self):
        for rec in self:
            rec.expected_revenue = sum(
                l.expected_price * l.qty_expected for l in rec.line_ids
            )
            rec.expected_profit = rec.expected_revenue - (rec.target_price or 0)
            if rec.target_price:
                rec.expected_roi = rec.expected_profit / rec.target_price
            else:
                rec.expected_roi = 0

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

    # === Generate Lines ===
    def action_generate_lines(self):
        """Generate assessment lines from spec-level BOM (create if not exists)"""
        self.ensure_one()

        if not self.spec_id or not self.body_type_id:
            raise UserError('กรุณาเลือก Vehicle Spec ที่มี Body Type ก่อน')

        self.line_ids.unlink()

        # 1. Find or create spec-level BOM
        bom = self._get_or_create_spec_bom()
        self.bom_id = bom.id

        # 2. Copy BOM lines → assessment lines
        lines_data = []
        total_lines = len(bom.bom_line_ids)
        default_weight = 100.0 / total_lines if total_lines else 0

        for seq, bom_line in enumerate(bom.bom_line_ids, start=1):
            origin, condition = self._get_origin_condition_from_variant(bom_line.product_id)
            lines_data.append({
                'assessment_id': self.id,
                'sequence': seq * 10,
                'part_name_id': bom_line.product_id.itx_part_name_id.id,
                'product_id': bom_line.product_id.id,
                'part_origin_id': origin.id if origin else False,
                'part_condition_id': condition.id if condition else False,
                'qty_expected': int(bom_line.product_qty) or 1,
                'qty_found': int(bom_line.product_qty) or 1,
                'expected_price': 0.0,
                'cost_weight': bom_line.itx_cost_weight or default_weight,
                'is_found': True,
            })

        self.env['itx.revival.assessment.line'].create(lines_data)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'สร้างรายการอะไหล่แล้ว',
                'message': f'สร้าง {len(lines_data)} รายการจาก BOM ({bom.display_name})',
                'type': 'success',
                'sticky': False,
            }
        }

    def _get_or_create_spec_bom(self):
        """Find existing spec-level BOM or create from template.bom"""
        self.ensure_one()
        MrpBom = self.env['mrp.bom']

        # Search existing
        bom = MrpBom.search([
            ('itx_spec_id', '=', self.spec_id.id),
        ], limit=1)
        if bom:
            return bom

        # Create from template
        templates = self.env['itx.info.vehicle.template.bom'].search([
            ('body_type_id', '=', self.body_type_id.id),
            ('active', '=', True),
        ], order='sequence, id')

        if not templates:
            raise UserError(
                f'ไม่พบ BOM Template สำหรับ Body Type: {self.body_type_id.name}'
            )

        # Fallback origin/condition — use is_default from master data
        PartOrigin = self.env['itx.info.vehicle.part.origin']
        PartCondition = self.env['itx.info.vehicle.part.condition']
        fallback_origin = PartOrigin.search([('is_default', '=', True)], limit=1) \
            or PartOrigin.search([('code', '=', 'OEM')], limit=1)
        fallback_condition = PartCondition.search([('is_default', '=', True)], limit=1) \
            or PartCondition.search([('code', '=', 'GOOD')], limit=1)

        # Create salvage vehicle product (spec level)
        salvage_product = self._get_or_create_salvage_product()

        # Create BOM
        bom = MrpBom.create({
            'product_tmpl_id': salvage_product.product_tmpl_id.id,
            'product_id': salvage_product.id,
            'product_qty': 1,
            'type': 'normal',
            'itx_spec_id': self.spec_id.id,
        })

        # Create BOM lines
        total_parts = len(templates)
        default_weight = 100.0 / total_parts if total_parts else 0

        for tmpl in templates:
            origin = tmpl.default_part_origin_id or fallback_origin
            condition = tmpl.default_part_condition_id or fallback_condition
            product = self._get_or_create_part_product(tmpl.part_template_id, origin, condition)
            if product:
                self.env['mrp.bom.line'].create({
                    'bom_id': bom.id,
                    'product_id': product.id,
                    'product_qty': tmpl.qty or 1,
                    'itx_cost_weight': tmpl.cost_weight or default_weight,
                })

        return bom

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
        if variant and variant.product_tmpl_id.tracking != 'serial':
            variant.product_tmpl_id.tracking = 'serial'
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
    def action_start_preparing(self):
        self.ensure_one()
        if not self.spec_id:
            raise UserError('กรุณาเลือก Vehicle Spec ก่อน')
        if not self.body_type_id:
            raise UserError('Vehicle Spec นี้ไม่มี Body Type กรุณาตั้งค่าใน Spec')
        self.state = 'preparing'

    def action_complete(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError('กรุณา Generate Lines ก่อน')
        if not self.target_price:
            raise UserError('กรุณากรอก Target Price ก่อน')
        self.state = 'complete'

    def action_cancel(self):
        self.ensure_one()
        if self.state == 'complete':
            self.write({
                'decision': 'not_buy',
                'decision_date': fields.Date.context_today(self),
                'decision_by': self.env.user.id,
                'state': 'cancelled',
            })
        else:
            self.state = 'cancelled'

    def action_reset_draft(self):
        self.ensure_one()
        self.write({
            'state': 'draft',
            'decision': False,
            'decision_date': False,
            'decision_by': False,
        })

    def action_create_acquired(self):
        self.ensure_one()
        if self.state != 'complete':
            raise UserError('ต้องอยู่สถานะ Complete ก่อน')
        if not self.decision or self.decision == 'not_buy':
            raise UserError('กรุณาเลือก Decision เป็น "ซื้อขายทั้งคัน" หรือ "ซื้อแตก Part" ก่อน')
        if self.acquired_id:
            raise UserError('มี Acquired Vehicle อยู่แล้ว')

        acquired = self.env['itx.revival.acquired'].create({
            'assessment_id': self.id,
            'vin': self.vehicle_vin or '',
            'vehicle_year': self.vehicle_year,
            'vehicle_color': self.vehicle_color,
            'vehicle_mileage': self.vehicle_mileage,
        })
        self.write({
            'acquired_id': acquired.id,
            'decision_date': fields.Date.context_today(self),
            'decision_by': self.env.user.id,
            'state': 'acquired',
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Acquired Vehicle',
            'res_model': 'itx.revival.acquired',
            'res_id': acquired.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_bom(self):
        """Open spec-level BOM for editing"""
        self.ensure_one()
        if not self.bom_id:
            raise UserError('กรุณา Generate Lines ก่อน')
        return {
            'type': 'ir.actions.act_window',
            'name': f'BOM - {self.spec_id.full_name}',
            'res_model': 'mrp.bom',
            'res_id': self.bom_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_sync_from_bom(self):
        """Re-sync assessment lines from BOM (master)"""
        self.ensure_one()
        if not self.bom_id:
            raise UserError('กรุณา Generate Lines ก่อน')

        self.line_ids.unlink()

        lines_data = []
        total_lines = len(self.bom_id.bom_line_ids)
        default_weight = 100.0 / total_lines if total_lines else 0

        for seq, bom_line in enumerate(self.bom_id.bom_line_ids, start=1):
            origin, condition = self._get_origin_condition_from_variant(bom_line.product_id)
            lines_data.append({
                'assessment_id': self.id,
                'sequence': seq * 10,
                'part_name_id': bom_line.product_id.itx_part_name_id.id,
                'product_id': bom_line.product_id.id,
                'part_origin_id': origin.id if origin else False,
                'part_condition_id': condition.id if condition else False,
                'qty_expected': int(bom_line.product_qty) or 1,
                'qty_found': int(bom_line.product_qty) or 1,
                'expected_price': 0.0,
                'cost_weight': bom_line.itx_cost_weight or default_weight,
                'is_found': True,
            })

        self.env['itx.revival.assessment.line'].create(lines_data)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync สำเร็จ',
                'message': f'อัพเดท {len(lines_data)} รายการจาก BOM',
                'type': 'success',
                'sticky': False,
            }
        }

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
