from odoo import api, fields, models, _
from datetime import date


class AssignEngineer(models.Model):
    _name = 'assign.engineer'
    _description = 'Assign Engineer'
    _rec_name = "engineer_name"

    engineer_id = fields.Char(string='Engineer ID', required=True, copy=False, readonly=True,
                              default=lambda self: _('New'))
    # engineer_name = fields.Char(string="Engineer")
    engineer_contact = fields.Char(string="Contact")
    engineer_email = fields.Char(string="Email")
    engineer_branch = fields.Many2one('res.branch', string="Branch")
    assign_date = fields.Date(string="Assign Date")
    assign_status = fields.Selection([('assigned', 'Assigned'), ('pending', 'Pending')], string="Assign Status")
    assign_for = fields.Selection(
        [('diagnosis and repair', 'Diagnosis and Repair'), ('quality assurance', 'Quality Assurance'),
         ('over phone communication', 'Over Phone Communication')], string="Assigned For")
    is_qa = fields.Char(string="Is QA?")
    qa_result = fields.Char(string="QA Result")
    qa = fields.Char(string="QA")
    remarks = fields.Char(string="Remarks")
    delivery_date = fields.Date(string="Delivery Date")
    active = fields.Boolean(string='Active', default=True)


    # en=fields.Many2one('res.users', string="En", domain = lambda self: self._get_user_domain())

    # en = fields.Many2one('res.users', string="En", domain=lambda self: [("groups_id", "=", self.env.ref("usl_service_erp.group_service_engineer").id)])
    engineer_name = fields.Many2one('res.users', string="En", domain=lambda self: self._get_user_domain())

    task_count = fields.Integer(string='Task Count', compute='_compute_task_count')

    def _get_user_domain(self):
        all_users = self.env['res.users'].sudo().search([])
        get_users = self.env.ref("usl_service_erp.group_service_engineer").users
        if not isinstance(get_users, bool) and get_users:
            domain = [('id', 'in', get_users.ids)]
        else:
            domain = [('id', 'in', all_users.ids)]
        # domain = ["groups_id", "=", self.env.ref("usl_service_erp.group_service_engineer").id]
        return domain

    def _compute_task_count(self):
        for rec in self:
            task_count = self.env['diagnosis.repair'].search_count([('engineer', '=', rec.id)])
            rec.task_count = task_count

    def action_view_tasks(self):
        return {
            'name': _('Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'diagnosis.repair',
            'view_mode': 'tree,form',
            'context': {'default_engineer': self.id},
            'target': 'current',
            'domain': [('engineer', '=', self.id)],
        }

    @api.model
    def create(self, vals):
        if vals.get('engineer_id', _('New')) == _('New'):
            vals['engineer_id'] = self.env['ir.sequence'].next_by_code('assign.engineer') or _('New')
        res = super(AssignEngineer, self).create(vals)

        return res
