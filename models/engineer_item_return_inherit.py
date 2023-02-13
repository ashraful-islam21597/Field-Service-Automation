from odoo import api, fields, models, _
import datetime
from odoo.exceptions import ValidationError


class EngineerItemReturnInherit(models.Model):
    _inherit = "stock.picking"
    _order = 'name desc'

    item_return_custom = fields.Boolean(default=False)
    return_no = fields.Char(readonly=True, default=lambda self: _('New'), string="Item Return No")
    return_date = fields.Date(default=fields.Datetime.now, string="Return Date", tracking=True)
    branch_id = fields.Many2one('res.branch', string='Branch', tracking=True)
    currency = fields.Many2one('res.currency', string="Currency")
    remark = fields.Text(string="Remark")

    @api.model
    def create(self, vals):
        res = super(EngineerItemReturnInherit, self).create(vals)
        if vals.get('return_no', _('New')) == _('New'):
            if res.picking_type_id.code == 'internal' \
                    and res.item_return_custom == True:
                val = self.env['ir.sequence'].next_by_code('engineer.item.return') or _('New')
                res.name = val
        return res

    # @api.onchange('picking_type_id')
    # def _onchange_picking_type(self):
    #     super(EngineerItemReturnInherit, self)._onchange_picking_type()
    #     if self.item_return_custom == True:
    #         return

