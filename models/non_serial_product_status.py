from odoo import api, fields, models, _
from datetime import date


class NonSerialProductStatus(models.Model):
    _name = 'non.serial.product.status'
    _description = 'Non Serial Product Status'
    _rec_name = 'nsp_status_reference'

    nsp_status_reference = fields.Char(string='Name', required=True, copy=False, readonly=True,
                                       default=lambda self: _('New'))
    nsp_status = fields.Char(string="Status")

    @api.model
    def create(self, vals):
        if vals.get('nsp_status_reference', _('New')) == _('New'):
            vals['nsp_status_reference'] = self.env['ir.sequence'].next_by_code('non.serial.product.status') or _('New')
        res = super(NonSerialProductStatus, self).create(vals)
        return res
