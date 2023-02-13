from odoo import api, fields, models, _


class ServiceType(models.Model):
    _name = "service.type"
    _description = "Service Type"
    _rec_name = "name"

    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active', default=True, copy=False)


