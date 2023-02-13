from odoo import api, fields, models, _


class WarrantyStatus(models.Model):
    _name = "warranty.status"
    _description = "Warranty Status"
    _rec_name = "name"

    name = fields.Char(string='Warranty Status')
    active = fields.Boolean(string="Active",  default=True)
