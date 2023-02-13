from odoo import api, fields, models, _


class ServiceTypeSetup(models.Model):
    _name = "service.type.setup"
    _description = "Service Type Setup"

    so_service_type = fields.Many2one('service.type', string="SO Service Type")
    service_item = fields.Many2many('product.product',
                                    domain="[('detailed_type', '=', 'service')]",
                                    string="Service Item")



