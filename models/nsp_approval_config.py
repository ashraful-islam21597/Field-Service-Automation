from odoo import api, fields, models, _
from datetime import date


class NspApprovalConfig(models.Model):
    _name = 'nsp.approval.config'
    _description = 'Invoice Approval'
    _rec_name = "user_branch"

    user_branch = fields.Many2one('res.branch', string="Branch")
    user_name = fields.Many2many('res.users', string="Approve Admin")
    active = fields.Boolean(default=True, string='Active')

