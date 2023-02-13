from odoo import api, fields, models, _
from datetime import date


class RepairStatus(models.Model):
    _name = 'repair.status'
    _description = 'Repair Status'
    _rec_name = "repair_status"

    repair_id = fields.Char(string='Repair ID', required=True, copy=False, readonly=True,
                           default=lambda self: _('New'))
    repair_status = fields.Char(string="Repair Status")
    is_approval = fields.Boolean(string='Is Approval', default=True)
    is_transfer = fields.Boolean(string='Is Transfer', default=False)
    active = fields.Boolean(string='Active', default=True)
    name = fields.Many2many('res.users',string="Approve Admin")
    color=fields.Integer(string="Color")


    @api.model
    def create(self, vals):
        if vals.get('repair_id', _('New')) == _('New'):
            vals['repair_id'] = self.env['ir.sequence'].next_by_code('repair.status') or _('New')
        res = super(RepairStatus, self).create(vals)

        return res