from odoo import api, fields, models, _
from datetime import date
class Brand(models.Model):
    _name='product.brand'
    name=fields.Char(string="Brand")
    active=fields.Boolean(string="Active",default="True")



class Products_Inherit(models.Model):
    _inherit = 'product.template'
    brand = fields.Many2one('product.brand',string="Brand")


    product_type= fields.Selection([('sp','Serial Product'),('nsp','Non Serial Product')],default='sp',string='Type Of Product For service')
    #service_flag=fields.Boolean(string="Flag",default=False)
    #detailed_type = fields.Selection([
    #     ('consu', 'Consumable'),
    #     ('service', 'Service')], string='Product Type', default=lambda  self:self._get_detailed_type(), required=True,
    #     help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
    #          'A consumable product is a product for which stock is not managed.\n'
    #          'A service is a non-material product you provide.')
    #
    # def _get_detailed_type(self):
    #     if 'default_service_flag' in self.env.context.keys() and self.env.context.get('default_service_flag') == True:
    #         return 'service'
    #     else:
    #         return 'consu'
