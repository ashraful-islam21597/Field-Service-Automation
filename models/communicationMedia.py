
from odoo import api, fields, models, _
from datetime import date


class CommunicationMedia(models.Model):
    _name = 'communication.media'
    _description = 'Communication Media'
    _rec_name = "communication_media"

    communication_media = fields.Char(string='Communication Media')
    active = fields.Boolean(string="Active", default=True)