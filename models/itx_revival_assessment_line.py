# -*- coding: utf-8 -*-

from odoo import api, fields, models


CONDITION_SELECTION = [
    ('good', 'Good (ดี)'),
    ('fair', 'Fair (พอใช้)'),
    ('poor', 'Poor (แย่)'),
    ('missing', 'Missing (ไม่มี)'),
]


class ItxRevivalAssessmentLine(models.Model):
    _name = 'itx.revival.assessment.line'
    _description = 'Vehicle Revival Assessment Line'
    _order = 'sequence, id'

    # === Parent ===
    assessment_id = fields.Many2one(
        comodel_name='itx.revival.assessment',
        string='Assessment',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )

    # === Part Information ===
    part_name_id = fields.Many2one(
        comodel_name='itx.info.vehicle.template.part',
        string='Part Name',
        required=True,
        index=True,
    )
    part_category_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.category',
        string='Part Category',
        related='part_name_id.category_id',
        store=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        index=True,
        help='Product ที่ generate/lookup ได้',
    )

    # === Pricing ===
    expected_price = fields.Float(
        string='Expected Price',
        digits='Product Price',
        help='ราคาที่คาดว่าขายได้ (H/O กรอก)',
    )
    cost_weight = fields.Float(
        string='Cost Weight (%)',
        digits=(5, 2),
        default=0,
        help='% สัดส่วนต้นทุน (ใช้ตอน Unbuild)',
    )
    allocated_cost = fields.Float(
        string='Allocated Cost',
        compute='_compute_allocated_cost',
        store=True,
        digits='Product Price',
        help='ต้นทุนที่กระจายให้ชิ้นนี้',
    )

    # === Field Survey ===
    is_found = fields.Boolean(
        string='Found',
        default=True,
        help='สายสืบเจอหรือไม่',
    )
    actual_condition = fields.Selection(
        selection=CONDITION_SELECTION,
        string='Actual Condition',
        help='สภาพจริงจากหน้างาน',
    )
    field_note = fields.Char(
        string='Field Note',
        help='หมายเหตุจากหน้างาน',
    )

    # === Related Fields ===
    spec_id = fields.Many2one(
        related='assessment_id.spec_id',
        store=True,
        index=True,
    )
    body_type_id = fields.Many2one(
        related='assessment_id.body_type_id',
        store=True,
    )

    # === Compute Methods ===
    @api.depends('cost_weight', 'assessment_id.target_price',
                 'assessment_id.line_ids', 'assessment_id.line_ids.cost_weight')
    def _compute_allocated_cost(self):
        for rec in self:
            if rec.assessment_id and rec.assessment_id.target_price:
                total_weight = sum(rec.assessment_id.line_ids.mapped('cost_weight'))
                if total_weight:
                    rec.allocated_cost = (
                        rec.assessment_id.target_price * rec.cost_weight / total_weight
                    )
                else:
                    rec.allocated_cost = 0
            else:
                rec.allocated_cost = 0

    # === Onchange Methods ===
    @api.onchange('is_found')
    def _onchange_is_found(self):
        """If not found, set condition to missing"""
        if not self.is_found:
            self.actual_condition = 'missing'
            self.expected_price = 0
