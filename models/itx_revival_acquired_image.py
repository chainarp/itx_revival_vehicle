# -*- coding: utf-8 -*-

from odoo import fields, models


class ItxRevivalAcquiredImage(models.Model):
    _name = 'itx.revival.acquired.image'
    _description = 'Acquired Vehicle Image'
    _order = 'sequence, id'

    # === Parent ===
    acquired_id = fields.Many2one(
        comodel_name='itx.revival.acquired',
        string='Acquired Vehicle',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # === Image ===
    image = fields.Image(
        string='Image',
        required=True,
        max_width=1920,
        max_height=1920,
    )
    description = fields.Char(
        string='Description',
        help='คำอธิบาย เช่น "ห้องเครื่อง", "หน้าซ้าย"',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
