# -*- coding: utf-8 -*-

from odoo import fields, models


IMAGE_CATEGORY_SELECTION = [
    ('exterior', 'Exterior (ภายนอก)'),
    ('interior', 'Interior (ภายใน)'),
    ('engine', 'Engine (ห้องเครื่อง)'),
    ('damage', 'Damage (ความเสียหาย)'),
    ('document', 'Document (เอกสาร/เล่มทะเบียน)'),
    ('other', 'Other (อื่นๆ)'),
]


class ItxRevivalAssessmentImage(models.Model):
    _name = 'itx.revival.assessment.image'
    _description = 'Assessment Field Survey Image'
    _order = 'sequence, id'

    assessment_id = fields.Many2one(
        comodel_name='itx.revival.assessment',
        string='Assessment',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    image = fields.Image(
        string='Image',
        required=True,
        max_width=1920,
        max_height=1920,
    )
    caption = fields.Char(
        string='Caption',
        help='คำอธิบาย เช่น "ด้านหน้าซ้าย", "ห้องเครื่อง"',
    )
    category = fields.Selection(
        selection=IMAGE_CATEGORY_SELECTION,
        string='Category',
        default='exterior',
    )
