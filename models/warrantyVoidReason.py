from odoo import api, fields, models, _


class WarrantyVoidReason(models.Model):
    _name = "warranty.void.reason"
    _description = "Warranty Void Reason"
    _rec_name = "name"

    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active', default=True, copy=False)


