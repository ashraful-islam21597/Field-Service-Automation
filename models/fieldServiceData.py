from odoo import api, fields, models, _
from datetime import date


class FieldServiceData(models.Model):
    _name = 'field.service.data'
    _description = 'Field Service Data'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "serial_no"

    serial_no = fields.Char(string='IMEI/Serial No.', required=True, readonly=True, tracking=True,
                            default=lambda self: _('New'))
    invoice = fields.Char(string="Invoice No")
    product_id = fields.Many2one('product.product', required=True)
    customer_id = fields.Many2one('res.partner', required=True)
    p_date = fields.Date(string="POP Date")
    warranty_status = fields.Many2one("warranty.status", string="Warranty Status")
    warranty_expiry_date_l = fields.Date(string="Warranty Expiry Date(L)")
    warranty_expiry_date_p = fields.Date(string="Warranty Expiry Date(p)")
    guaranty_expiry_date = fields.Date(string="Guaranty Expiry Date")

    @api.model
    def create(self, vals):
        if vals.get('serial_no', _('New')) == _('New'):
            vals['serial_no'] = self.env['ir.sequence'].next_by_code('field.service.data') or _('New')
        res = super(FieldServiceData, self).create(vals)

        return res
