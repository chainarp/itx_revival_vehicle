# -*- coding: utf-8 -*-

from odoo import fields, models


class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    itx_acquired_id = fields.Many2one(
        comodel_name='itx.revival.acquired',
        string='Acquired Vehicle',
        index=True,
        help='ผูกกับรถคันไหน',
    )
