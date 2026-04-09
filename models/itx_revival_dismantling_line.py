# -*- coding: utf-8 -*-

from odoo import fields, models


class ItxRevivalDismantlingLine(models.Model):
    _name = 'itx.revival.dismantling.line'
    _description = 'Vehicle Dismantling Line'
    _order = 'sequence, id'

    # === Parent ===
    dismantling_id = fields.Many2one(
        comodel_name='itx.revival.dismantling',
        string='Dismantling Order',
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
    assessment_line_id = fields.Many2one(
        comodel_name='itx.revival.assessment.line',
        string='Assessment Line',
        readonly=True,
    )

    # === Assessed (readonly — from assessment) ===
    assessed_origin_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.origin',
        string='Assessed Origin',
        readonly=True,
    )
    assessed_condition_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.condition',
        string='Assessed Condition',
        readonly=True,
    )
    assessed_qty = fields.Integer(
        string='Assessed Qty',
        readonly=True,
    )

    # === Actual (user fills — dismantling reality) ===
    actual_origin_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.origin',
        string='Actual Origin',
    )
    actual_condition_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.condition',
        string='Actual Condition',
    )
    actual_qty = fields.Integer(
        string='Actual Qty',
        default=1,
    )

    # === Product ===
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product (Assessed)',
        readonly=True,
        help='Product จาก assessment (OEM&GOOD default)',
    )
    actual_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product (Actual)',
        readonly=True,
        help='Product จริง (ถ้า condition ต่างจาก assessed)',
    )

    # === Lot ===
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot/Serial',
        readonly=True,
        help='Lot ที่สร้างตอน confirm (stamp VIN)',
    )

    # === Cost ===
    cost_weight = fields.Float(
        string='Cost Weight (%)',
        digits=(5, 2),
    )

    # === Control ===
    is_included = fields.Boolean(
        string='Include',
        default=True,
        help='รวมใน Dismantling หรือไม่',
    )
    note = fields.Char(string='Note')
