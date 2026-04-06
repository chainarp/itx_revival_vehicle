# -*- coding: utf-8 -*-

from odoo import api, fields, models


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
        comodel_name='product.product',
        string='Product',
        index=True,
        help='Product จาก spec-level BOM',
    )

    # === Origin & Condition ===
    part_origin_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.origin',
        string='Part Origin',
        related='product_id.itx_part_origin_id',
        store=True,
    )
    part_condition_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.condition',
        string='Part Condition',
        related='product_id.itx_condition_id',
        store=True,
    )

    # === Quantity ===
    qty_expected = fields.Integer(
        string='Qty Expected',
        default=1,
        help='จำนวนที่คาดว่ามี (จาก BOM)',
    )
    qty_found = fields.Integer(
        string='Qty Found',
        default=1,
        help='จำนวนที่สายสืบเจอจริง',
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
        help='% สัดส่วนต้นทุน',
    )
    allocated_cost = fields.Float(
        string='Allocated Cost',
        compute='_compute_allocated_cost',
        store=True,
        digits='Product Price',
    )

    # === Field Survey ===
    is_found = fields.Boolean(
        string='Found',
        default=True,
        help='สายสืบเจอหรือไม่',
    )
    actual_condition_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.condition',
        string='Actual Condition',
        index=True,
        help='สภาพจริงจากหน้างาน (สายสืบกรอก)',
    )
    field_note = fields.Char(
        string='Field Note',
        help='หมายเหตุจากหน้างาน',
    )

    # === Related ===
    spec_id = fields.Many2one(
        related='assessment_id.spec_id',
        store=True,
        index=True,
    )

    # === Compute ===
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

    # === Onchange ===
    @api.onchange('is_found')
    def _onchange_is_found(self):
        if not self.is_found:
            self.actual_condition_id = False
            self.qty_found = 0
            self.expected_price = 0
