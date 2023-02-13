from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'
    _rec_name = 'so_number'

    service_invoice_flag = fields.Boolean(default=False)
    so_number = fields.Many2one('field.service', string='So Number')
    service_item = fields.Many2one(related='so_number.product_id', string='Service Item')
    service_type = fields.Many2one(related='so_number.service_type', string='Service Type')
    branch_id = fields.Many2one('res.branch', default=lambda self: self._get_default_branch())
    communication_media = fields.Many2one(related='so_number.communication_media', string='Communication Media')
    department = fields.Many2one(related='so_number.departments', string='Department', )
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True,
                                 default=lambda self: self._get_default_so_user())
    order_date = fields.Date(related='so_number.order_date', string='Order Date', readonly=True)
    repair_status = fields.Many2one(related='so_number.repair_status1', string='Repair Status', readonly=True)
    remarks = fields.Html(related='so_number.remark', string='Remarks')
    ing_id = fields.Many2one('res.users', default=lambda self: self.env.user, string="Engineer Name")
    state = fields.Selection(selection_add=[
        ('submitted_for_approval', 'Submitted For Approval'),
        ('approved', 'Approved'),
        ('posted',)
    ], ondelete={'submitted_for_approval': 'set default', 'approved': 'set default'})

    iv1_approve = fields.Boolean(compute='_iv1_approve', string='approve', default=False)

    def _iv1_approve(self):
        for rec in self:
            x = self.env['iv1.approval.config'].search([('user_branch', '=', rec.branch_id.id)])
            if self.env.user.id in x.user_name.ids:
                if self.env.user.department_id.id == rec.so_number.departments.id:
                    rec.iv1_approve = True
                else:
                    rec.iv1_approve = False
            else:
                rec.iv1_approve = False

    @api.onchange('so_number')
    def _get_default_so_user(self):
        for rec in self:
            rec.partner_id = rec.so_number.customer_id

    @api.onchange('so_number')
    def _get_default_branch(self):
        for rec in self:
            if rec.nspr_labour_claim_flag == True or rec.claim_flag == True:
                rec.branch_id = self.env.user.branch_id.id
            else:
                rec.branch_id = rec.so_number.branch_name

    def action_submit_for_approval(self):
        for rec in self:
            rec.state = 'submitted_for_approval'

    def action_approved(self):
        for rec in self:
            rec.state = 'approved'
