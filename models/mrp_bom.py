# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    itx_spec_id = fields.Many2one(
        comodel_name='itx.info.vehicle.spec',
        string='Vehicle Spec',
        index=True,
        help='Spec-level BOM (master data)',
    )


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    itx_cost_weight = fields.Float(
        string='Cost Weight (%)',
        digits=(5, 2),
        help='% สัดส่วนต้นทุน',
    )
    itx_total_weight = fields.Float(
        string='Total Weight',
        compute='_compute_itx_total_weight',
        digits=(5, 2),
    )
    itx_weight_status = fields.Char(
        string='Status',
        compute='_compute_itx_total_weight',
    )

    @api.depends('itx_cost_weight', 'bom_id.bom_line_ids.itx_cost_weight')
    def _compute_itx_total_weight(self):
        for rec in self:
            if rec.bom_id:
                total = sum(rec.bom_id.bom_line_ids.mapped('itx_cost_weight'))
                rec.itx_total_weight = total
                diff = total - 100
                if abs(diff) < 0.01:
                    rec.itx_weight_status = '✓ 100%'
                elif diff < 0:
                    rec.itx_weight_status = f'{diff:.2f}%'
                else:
                    rec.itx_weight_status = f'+{diff:.2f}%'
            else:
                rec.itx_total_weight = 0
                rec.itx_weight_status = ''
