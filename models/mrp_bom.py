# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    itx_acquired_id = fields.Many2one(
        comodel_name='itx.revival.acquired',
        string='Acquired Vehicle',
        index=True,
        help='ผูกกับรถคันไหน',
    )


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    itx_cost_weight = fields.Float(
        string='Cost Weight (%)',
        digits=(5, 2),
        help='% สัดส่วนต้นทุน',
    )
    itx_allocated_cost = fields.Float(
        string='Allocated Cost',
        compute='_compute_itx_allocated_cost',
        store=True,
        digits='Product Price',
        help='ต้นทุนที่กระจายให้ชิ้นนี้',
    )
    itx_expected_price = fields.Float(
        string='Expected Price',
        digits='Product Price',
        help='ราคาขายที่คาดการณ์',
    )

    @api.depends('itx_cost_weight', 'bom_id.itx_acquired_id',
                 'bom_id.itx_acquired_id.total_cost')
    def _compute_itx_allocated_cost(self):
        for rec in self:
            if (rec.bom_id and rec.bom_id.itx_acquired_id and
                    rec.bom_id.itx_acquired_id.total_cost):
                # Get total weight from all lines
                total_weight = sum(
                    rec.bom_id.bom_line_ids.mapped('itx_cost_weight')
                )
                if total_weight:
                    rec.itx_allocated_cost = (
                        rec.bom_id.itx_acquired_id.total_cost *
                        rec.itx_cost_weight / total_weight
                    )
                else:
                    rec.itx_allocated_cost = 0
            else:
                rec.itx_allocated_cost = 0
