# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


DECISION_SELECTION = [
    ('not_buy', 'ไม่ซื้อ'),
    ('sell_whole', 'ซื้อขายทั้งคัน'),
    ('dismantle', 'ซื้อแตก Part'),
]

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('assessed', 'Assessed'),
    ('decided', 'Decided'),
    ('acquired', 'Acquired'),
    ('cancelled', 'Cancelled'),
]


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
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    # === Vehicle Information ===
    spec_id = fields.Many2one(
        comodel_name='itx.info.vehicle.spec',
        string='Vehicle Spec',
        required=True,
        index=True,
        tracking=True,
        help='สเปครถที่ประเมิน',
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
        index=True,
    )
    model_id = fields.Many2one(
        comodel_name='itx.info.vehicle.model',
        string='Model',
        related='spec_id.model_id',
        store=True,
        index=True,
    )
    generation_id = fields.Many2one(
        comodel_name='itx.info.vehicle.generation',
        string='Generation',
        related='spec_id.generation_id',
        store=True,
        index=True,
    )

    # === Vehicle Details ===
    vehicle_year = fields.Integer(
        string='Vehicle Year',
        help='ปีรถ',
    )
    vehicle_color = fields.Char(
        string='Vehicle Color',
        help='สีรถ',
    )
    vehicle_mileage = fields.Integer(
        string='Mileage (km)',
        help='เลขไมล์',
    )
    vehicle_vin = fields.Char(
        string='VIN',
        index=True,
        help='เลขตัวถัง (ถ้ารู้ตอนนี้)',
    )
    location = fields.Char(
        string='Location',
        help='ที่อยู่ซากรถ',
    )

    # === Assessment Info ===
    assessor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Assessor',
        help='สายสืบที่ไปดู',
    )
    assessment_date = fields.Date(
        string='Assessment Date',
        default=fields.Date.context_today,
    )

    # === Pricing ===
    asking_price = fields.Float(
        string='Asking Price',
        digits='Product Price',
        help='ราคาที่เจ้าของตั้ง',
    )
    target_price = fields.Float(
        string='Target Price',
        digits='Product Price',
        tracking=True,
        help='ราคาที่เราจะเสนอซื้อ',
    )
    expected_revenue = fields.Float(
        string='Expected Revenue',
        compute='_compute_expected_values',
        store=True,
        digits='Product Price',
        help='รายได้ที่คาดการณ์ (ผลรวมราคาอะไหล่)',
    )
    expected_profit = fields.Float(
        string='Expected Profit',
        compute='_compute_expected_values',
        store=True,
        digits='Product Price',
        help='กำไรที่คาดการณ์',
    )
    expected_roi = fields.Float(
        string='Expected ROI (%)',
        compute='_compute_expected_values',
        store=True,
        digits=(5, 2),
        help='ROI ที่คาดการณ์ (%)',
    )

    # === Decision ===
    decision = fields.Selection(
        selection=DECISION_SELECTION,
        string='Decision',
        tracking=True,
    )
    decision_note = fields.Text(
        string='Decision Note',
        help='เหตุผลการตัดสินใจ',
    )
    decision_date = fields.Date(
        string='Decision Date',
    )
    decision_by = fields.Many2one(
        comodel_name='res.users',
        string='Decision By',
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
    line_count = fields.Integer(
        string='Part Count',
        compute='_compute_line_count',
    )

    # === Link to Acquired ===
    acquired_id = fields.Many2one(
        comodel_name='itx.revival.acquired',
        string='Acquired Vehicle',
        readonly=True,
        copy=False,
    )

    # === Notes ===
    note = fields.Text(
        string='Notes',
    )

    # === Compute Methods ===
    @api.depends('line_ids', 'line_ids.expected_price', 'target_price')
    def _compute_expected_values(self):
        for rec in self:
            rec.expected_revenue = sum(rec.line_ids.mapped('expected_price'))
            rec.expected_profit = rec.expected_revenue - (rec.target_price or 0)
            if rec.target_price:
                rec.expected_roi = (rec.expected_profit / rec.target_price) * 100
            else:
                rec.expected_roi = 0

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    # === CRUD Methods ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'itx.revival.assessment'
                ) or 'New'
        return super().create(vals_list)

    # === Action Methods ===
    def action_generate_lines(self):
        """Generate assessment lines from BOM template based on body_type"""
        self.ensure_one()

        if not self.spec_id:
            raise UserError('กรุณาเลือก Vehicle Spec ก่อน')

        if not self.body_type_id:
            raise UserError('Vehicle Spec นี้ไม่มี Body Type กรุณาตั้งค่าใน Spec')

        # Clear existing lines
        self.line_ids.unlink()

        # Get BOM template for this body type
        bom_templates = self.env['itx.info.vehicle.template.bom'].search([
            ('body_type_id', '=', self.body_type_id.id),
            ('active', '=', True),
        ], order='sequence, id')

        if not bom_templates:
            raise UserError(
                f'ไม่พบ BOM Template สำหรับ Body Type: {self.body_type_id.name}'
            )

        # Calculate default cost weight
        total_parts = len(bom_templates)
        default_weight = 100.0 / total_parts if total_parts else 0

        lines_data = []
        for seq, bom in enumerate(bom_templates, start=1):
            # Lookup or create product
            product = self._get_or_create_product(bom.part_template_id)

            lines_data.append({
                'assessment_id': self.id,
                'sequence': seq * 10,
                'part_name_id': bom.part_template_id.id,
                'part_category_id': bom.part_category_id.id,
                'product_id': product.id if product else False,
                'expected_price': 0.0,  # H/O จะกรอกทีหลัง
                'cost_weight': default_weight,
                'is_found': True,  # Default = เจอ
            })

        self.env['itx.revival.assessment.line'].create(lines_data)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'สร้างรายการอะไหล่แล้ว',
                'message': f'สร้าง {len(lines_data)} รายการจาก BOM Template',
                'type': 'success',
                'sticky': False,
            }
        }

    def _get_or_create_product(self, part_template):
        """Lookup or create product.template for this spec + part"""
        self.ensure_one()

        ProductTemplate = self.env['product.template']
        PartOrigin = self.env['itx.info.vehicle.part.origin']
        PartCondition = self.env['itx.info.vehicle.part.condition']

        # Get default origin and condition
        default_origin = PartOrigin.search([('code', '=', 'OEM')], limit=1)
        default_condition = PartCondition.search([('code', '=', 'FAIR')], limit=1)

        if not default_origin or not default_condition:
            return False  # Master data not found

        # Search existing product
        domain = [
            ('itx_is_vehicle_part', '=', True),
            ('itx_spec_id', '=', self.spec_id.id),
            ('itx_part_name_id', '=', part_template.id),
            ('itx_part_origin_id', '=', default_origin.id),
            ('itx_condition_id', '=', default_condition.id),
        ]
        product = ProductTemplate.search(domain, limit=1)

        if product:
            return product

        # Create new product
        product = ProductTemplate.create({
            'name': part_template.name,
            'itx_is_vehicle_part': True,
            'itx_spec_id': self.spec_id.id,
            'itx_part_name_id': part_template.id,
            'itx_part_category_id': part_template.category_id.id,
            'itx_part_origin_id': default_origin.id,
            'itx_condition_id': default_condition.id,
            'type': 'product',
            'sale_ok': True,
            'purchase_ok': False,
        })

        return product

    def action_assessed(self):
        """Move to Assessed state"""
        self.ensure_one()
        if not self.line_ids:
            raise UserError('กรุณา Generate Lines ก่อน')
        self.state = 'assessed'

    def action_decide(self):
        """Move to Decided state"""
        self.ensure_one()
        if not self.decision:
            raise UserError('กรุณาเลือก Decision ก่อน')
        self.write({
            'state': 'decided',
            'decision_date': fields.Date.context_today(self),
            'decision_by': self.env.user.id,
        })

    def action_cancel(self):
        """Cancel assessment"""
        self.ensure_one()
        self.state = 'cancelled'

    def action_reset_draft(self):
        """Reset to draft"""
        self.ensure_one()
        self.state = 'draft'

    def action_create_acquired(self):
        """Create Acquired Vehicle from this assessment"""
        self.ensure_one()

        if self.state != 'decided':
            raise UserError('ต้องอยู่สถานะ Decided ก่อน')

        if self.decision == 'not_buy':
            raise UserError('ไม่สามารถสร้าง Acquired ได้ เพราะตัดสินใจไม่ซื้อ')

        if self.acquired_id:
            raise UserError('มี Acquired Vehicle อยู่แล้ว')

        # Create acquired vehicle
        acquired = self.env['itx.revival.acquired'].create({
            'assessment_id': self.id,
            'vin': self.vehicle_vin or '',
            'vehicle_year': self.vehicle_year,
            'vehicle_color': self.vehicle_color,
            'vehicle_mileage': self.vehicle_mileage,
        })

        self.write({
            'acquired_id': acquired.id,
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

    def action_print_checklist(self):
        """Print checklist PDF for assessor"""
        self.ensure_one()
        # TODO: Implement report
        raise UserError('PDF Checklist ยังไม่พร้อมใช้งาน')

    def action_view_lines(self):
        """View assessment lines"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assessment Lines',
            'res_model': 'itx.revival.assessment.line',
            'view_mode': 'list',
            'domain': [('assessment_id', '=', self.id)],
            'context': {'default_assessment_id': self.id},
        }
