from odoo import api, fields, models, _
from datetime import date

class ClaimApproval(models.Model):
    _name = 'claim.approval.config'
    _description = 'Claim Approval'
    _rec_name = "user_branch"

    user_branch = fields.Many2one('res.branch', string="Branch")
    user_name = fields.Many2many('res.users', string="Approve Admin")
    active = fields.Boolean(default=True, string='Active')
