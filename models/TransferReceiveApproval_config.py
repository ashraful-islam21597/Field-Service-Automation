from odoo import api, fields, models, _
from datetime import date

class TransferReceiveApproval(models.Model):
    _name = 'receive.approval.config'
    _description = 'Transfer Order Receive Approval'
    _rec_name = "user_branch"

    user_branch = fields.Many2one('res.branch', string="Branch")
    user_name = fields.Many2many('res.users', string="Approve Admin")
    active = fields.Boolean(default=True, string='Active')
    # partner_id=fields.Many2many('res.partner', string="Approve Admin")

    # @api.onchange(user_name)
    # def _onchange_username(self):
    #     self.partner_id=self.user_name.id

class TransferConfirmApproval(models.Model):
    _name = 'transfer.confirm.approval.config'
    _description = 'Transfer Order Confirm Approval'
    _rec_name = "user_branch"

    user_branch = fields.Many2one('res.branch', string="Branch")
    user_name = fields.Many2many('res.users', string="Approve Admin")
    active = fields.Boolean(default=True, string='Active')
    #partner_id=fields.Many2many('res.partner', string="Approve Admin")

    # @api.onchange(user_name)
    # def _onchange_username(self):
    #     self.partner_id=self.user_name.id