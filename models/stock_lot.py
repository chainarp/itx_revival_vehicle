# -*- coding: utf-8 -*-

from odoo import fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    itx_vin = fields.Char(
        string='VIN',
        index=True,
        help='VIN ของซากรถที่ part นี้มา',
    )
    itx_acquired_id = fields.Many2one(
        comodel_name='itx.revival.acquired',
        string='Acquired Vehicle',
        index=True,
        help='ผูกกับรถคันไหน',
    )
