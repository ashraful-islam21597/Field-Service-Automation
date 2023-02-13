

from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import ValidationError
from datetime import  datetime


class AssignEngineerDetails(models.Model):
    _name = 'assign.engineer.details'
    _description = 'Assign Engineer Details'
    _rec_name = "assign_no"

    assign_no = fields.Char(string='Assign No', required=True, copy=False, readonly=True,
                            default=lambda self: _('New'))
    assign_engineer_lines_ids = fields.One2many('assign.engineer.lines', 'engineer_id', string="Assign Engineer")
    order_id = fields.Many2one('field.service', string="Service Order", readonly=True)
    customer = fields.Many2one(related='order_id.customer_id', string='Customer')
    contact = fields.Char(related="order_id.phone", string='Contact No', readonly=True)
    item = fields.Many2one(related="order_id.product_id", string="Item")
    priority = fields.Selection(related="order_id.priority", string="Priority")
    priority_lavel_duration = fields.Char(related="order_id.priority_lavel_duration", string='Priority Level Duration')
    warranty = fields.Many2one(related='order_id.warranty_status')
    # assign_engineer_lines_id = fields.Many2one('assign.engineer.lines', string="Engineer")
    is_qa = fields.Boolean(string="Is QA?", default=False, compute="_compute_is_qa")
    qa_result = fields.Char(string="QA Result")
    qa = fields.Char(string="QA")
    test = fields.Char(string="Test")

    @api.depends('assign_no')
    def _compute_is_qa(self):
        for rec in self:
            if rec.order_id:
                get_wanted_repair_status = self.env['repair.status'].sudo().search(
                    [('repair_status', '=', 'Ready For QC')], limit=1)
                if rec.order_id.repair_status1.id == get_wanted_repair_status.id:
                    rec.is_qa = True
                else:
                    rec.is_qa = False

    @api.model
    def create(self, vals):
        if vals.get('assign_no', _('New')) == _('New'):
            vals['assign_no'] = self.env['ir.sequence'].next_by_code('assign.engineer.details') or _('New')
        res = super(AssignEngineerDetails, self).create(vals)

        return res

    @api.onchange('assign_engineer_lines_ids')
    def set_engineer_domain(self):
        if self.order_id:
            get_branch = self.order_id.branch_name
            get_enginners = self.env.ref("usl_service_erp.group_service_engineer").users
            get_related_engineer = self.env['res.users'].sudo().search(
                [('branch_id', '=', get_branch.id), ('id', 'in', get_enginners.ids)])
            return {'domain': {'assign_engineer_lines_ids.engineer_name': [('id', 'in', get_related_engineer.ids)]}}


        else:
            return {'domain': {'assign_engineer_lines_ids.engineer_name': [('id', 'in', False)]}}

    # @api.onchange('assign_engineer_lines_ids')
    # def assign_state(self):
    #     for rec in self:
    #         for i in rec.assign_engineer_lines_ids:
    #             if i.engineer_name != '':
    #                 i.assign_status2.name = 'Assigned'
    #             else:
    #                 rec.order_id.assign_status1 = ''
    # if i.assign_status1 == 'assigned':
    #     rec.order_id.assign_status1 = 'assigned'
    # elif i.assign_status1 == 'pending':
    #     rec.order_id.assign_status1 = 'pending'
    # else:
    #     rec.order_id.assign_status1 = ''


class AssignEngineerLines(models.Model):
    _name = "assign.engineer.lines"
    _description = "Assign Engineer Lines"
    _rec_name = "engineer_name"

    engineer_name = fields.Many2one('res.users', string="Engineer", domain="[('id','in',engineer_name_domain)]")
    assign_date = fields.Date(string='Assign Date', default=fields.Datetime.now)
    assign_status1 = fields.Selection([('assigned', 'Assigned'), ('pending', 'Pending')], string="Assign Status")
    assign_status2 = fields.Many2one('repair.status', string="Assign Status",
                                     domain=lambda self: self._get_assigned_domain(),
                                     default=lambda self: self.env['repair.status'].search(
                                         [('repair_status', '=', 'Assigned')]))
    assign_for = fields.Selection(
        [('diagnosis and repair', 'Diagnosis and Repair'), ('quality assurance', 'Quality Assurance'),
         ('over phone communication', 'Over Phone Communication')], string="Assigned For")
    # is_qa = fields.Char(string="Is QA?")
    is_qa1 = fields.Boolean( string="Is QA?", default=False)
    qa_result = fields.Many2one('repair.status', string="QA Status")
    qa = fields.Char(string="QA Comment")
    remarks = fields.Char(string="Remarks")
    delivery_date = fields.Date(string="Delivery Date", readonly=True)

    engineer_id = fields.Many2one('assign.engineer.details', string="Assign")

    task_count = fields.Integer(string='Task Count', compute='_compute_task_count')
    engineer_name_domain = fields.Many2many('res.users',
                                            compute="_compute_engineer_domain",
                                            readonly=True,
                                            store=False,
                                            )
    possible_delivery_date = fields.Date(string='Possible Diagnosis Date', readonly=True)

    def create(self, vals):
        res = super(AssignEngineerLines, self).create(vals)
        res.engineer_id.order_id.engr_count +=  1
        for rec in res:
            if rec.remarks:
                if not self.env['remarks.history'].search([('order_id', '=', rec.engineer_id.order_id.id)]).id:
                    remark1 = self.env['remarks.history'].create({'order_id': rec.engineer_id.order_id.id})
                else:
                    remark1 = self.env['remarks.history'].search([('order_id', '=', rec.engineer_id.order_id.id)])
                self.env['remarks.lines'].create({'remark_id': remark1.id, 'remarks': rec.remarks,
                                                  'remarked_by': self.env.user.id,
                                                  'remarked_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                  'remarked_place': 'Assigning Engineer'})
            if rec.assign_for == 'quality assurance':
                rec.engineer_id.order_id.qa = True

            if rec.assign_for == 'diagnosis and repair':
                self.env['diagnosis.repair'].create(
                    {'order_id': rec.engineer_id.order_id.id, 'engineer': rec.engineer_name.id, 'x': rec.id,
                     'contact': rec.engineer_id.contact, 'priority': rec.engineer_id.priority,
                     'priority_lavel_duration': rec.engineer_id.priority_lavel_duration,
                     'warranty': rec.engineer_id.warranty})

            # Section Create Monitoring Report Data start
            monitoring_line = rec.env['field.service.monitoring.data'].search(
                [('so_number', '=', res.engineer_id.order_id.id)])

            if monitoring_line:
                monitoring_line.assign_by = self.env.user.id
                monitoring_line.remarks = res.remarks
                monitoring_line.assign_for = res.engineer_name
                monitoring_line.assign_date = res.assign_date
                monitoring_line.assign_status = res.assign_status2
                monitoring_line.assign_f = res.assign_for
                monitoring_line.dpt_diff_days = (res.assign_date - monitoring_line.service_order_date).days or 0
                # monitoring_line.assign_by = self.env.user.id
                # monitoring_line.remarks = vals[0]['remarks']
                # monitoring_line.assign_for = vals[0]['engineer_name']
                # monitoring_line.assign_date = vals[0]['assign_date']
                # monitoring_line.assign_status = vals[0]['assign_status2']
                # monitoring_line.assign_f = vals[0]['assign_for']

            # Section Create Monitoring Report Data End

            # Section Create Monitoring Report History start
            if not self.env['field.service.monitoring.report'].search(
                    [('so_number', '=', res.engineer_id.order_id.id)]).id:
                monitoring_report = self.env['field.service.monitoring.report'].create(
                    {'so_number': res.engineer_id.order_id.id})
            else:
                monitoring_report = self.env['field.service.monitoring.report'].search(
                    [('so_number', '=', res.engineer_id.order_id.id)])

            self.env['field.service.monitoring.report.lines'].create({'monitoring_report_id': monitoring_report.id,
                                                                      'so_number': res.engineer_id.order_id.id,
                                                                      'assign_by': self.env.user.id,
                                                                      'assign_for': res.engineer_name.id,
                                                                      'assign_date': res.assign_date,
                                                                      'assign_status': res.assign_status2.id,
                                                                      'qa_status': res.qa_result.id,
                                                                      'remarks': res.remarks,
                                                                      'delivery_date': res.delivery_date,
                                                                      'qa_comment': res.qa,

                                                                      })
            # Section Create Monitoring Report History End

        return res

    @api.model
    def write(self, vals):
        res = super(AssignEngineerLines, self).write(vals)

        # Section Write Monitoring Report Data Start
        monitoring_line = self.env['field.service.monitoring.data'].search(
            [('so_number', '=', self.engineer_id.order_id.id)])

        if monitoring_line:
            if 'remarks' in vals.keys() and monitoring_line.remarks != vals['remarks']:
                monitoring_line.remarks = vals['remarks']
            elif 'engineer_name' in vals.keys() and monitoring_line.assign_for != vals['engineer_name']:
                monitoring_line.assign_for = vals['engineer_name']
            elif 'assign_status2' in vals.keys() and monitoring_line.assign_status != vals['assign_status2']:
                monitoring_line.assign_status = vals['assign_status2']
            elif 'assign_date' in vals.keys() and monitoring_line.assign_date != vals['assign_date']:
                monitoring_line.assign_date = vals['assign_date']
            elif 'assign_for' in vals.keys() and monitoring_line.assign_f != vals['assign_for']:
                monitoring_line.assign_f = vals['assign_for']
        # Section Write Monitoring Report Data End

        # # Section Write Monitoring Report  Start
        # monitoring_report = self.env['field.service.monitoring.report'].search([('so_number', '=', self.engineer_id.order_id.id)])
        # if not monitoring_report.id:
        #     monitoring_report = self.env['field.service.monitoring.report'].create(
        #         {'so_number': self.engineer_id.order_id.id})
        #     self.env['field.service.monitoring.report.lines'].create({'monitoring_report_id': monitoring_report.id,
        #                                                               'so_number': res.engineer_id.order_id,
        #                                                               'assign_by': self.env.user.id,
        #                                                               'assign_for': res.engineer_name.id,
        #                                                               'assign_date': res.assign_date,
        #                                                               'assign_status': res.assign_status2.id,
        #                                                               'qa_status': res.qa_result.id,
        #                                                               'remarks': res.remarks,
        #                                                               'delivery_date': res.delivery_date,
        #                                                               'qa_comment': res.qa,
        #                                                               })
        # else:
        #     val = []
        #     vals = (0, 0, {
        #         'monitoring_report_id': monitoring_report.id,
        #         'so_number': res.engineer_id.order_id.id,
        #         'assign_by': self.env.user.id,
        #         'assign_for': res.engineer_name.id,
        #         'assign_date': res.assign_date,
        #         'assign_status': res.assign_status2.id,
        #         'qa_status': res.qa_result.id,
        #         'remarks': res.remarks,
        #         'delivery_date': res.delivery_date,
        #         'qa_comment': res.qa,
        #     })
        #     val.append(vals)
        #     monitoring_report.monitoring_report_lines_ids = val

        # Section Write Monitoring Report  End

        try:
            if vals['remarks']:
                remarks = self.env['remarks.history'].search([('order_id', '=', self.engineer_id.order_id.id)])
                if not remarks.id:
                    remark1 = self.env['remarks.history'].create({'order_id': self.engineer_id.order_id.id})
                    self.env['remarks.lines'].create({'remark_id': remark1.id,
                                                      'remarks': self.remarks
                                                      })
                else:
                    value = []
                    vals = (0, 0, {
                        'remarks': self.remarks,
                        'remark_id': remarks.id,
                        'remarked_by': self.env.user.id,
                        'remarked_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'remarked_place': 'Assigning Engineer',
                    })
                    value.append(vals)
                    remarks.remarks_lines_ids = value

                return res

        except:
            return res

    @api.onchange('assign_status2')
    def so_repair_status(self):
        for rec in self:

            get_assigned_domain = self.env['repair.status'].sudo().search(
                [('repair_status', '=', 'Ready For QC')])
            if rec.engineer_id.order_id.repair_status1.id == get_assigned_domain.id:
                rec.engineer_id.order_id.repair_status1 = get_assigned_domain.id
            else:
                rec.engineer_id.order_id.repair_status1 = rec.assign_status2

    #
    def _get_assigned_domain(self):
        get_assigned_domain = self.env['repair.status'].sudo().search(
            [('repair_status', '=', 'Assigned')])
        domain = [('id', 'in', get_assigned_domain.ids)]
        return domain

    @api.depends('engineer_id')
    def _compute_engineer_domain(self):
        if self.env.user.has_group('usl_service_erp.group_service_engineer'):
            if self.engineer_id.order_id:
                get_branch = self.engineer_id.order_id.branch_name
                get_enginners = self.env.ref("usl_service_erp.group_service_engineer").users
                get_related_engineer = self.env['res.users'].sudo().search(
                    [('branch_id', '=', get_branch.id), ('id', '=', self.env.user.id)])
                self.engineer_name_domain = get_related_engineer
            else:
                self.engineer_name_domain = None
        if self.env.user.has_group('usl_service_erp.group_service_manager'):
            if self.engineer_id.order_id:
                get_branch = self.engineer_id.order_id.branch_name
                get_enginners = self.env.ref("usl_service_erp.group_service_engineer").users
                get_related_engineer = self.env['res.users'].sudo().search(
                    [('branch_id', '=', get_branch.id), ('id', 'in', get_enginners.ids)])
                self.engineer_name_domain = get_related_engineer
            else:
                self.engineer_name_domain = None

    def _compute_task_count(self):
        for rec in self:
            task_count = self.env['diagnosis.repair'].search_count([('engineer', '=', rec.engineer_name.id)])
            rec.task_count = task_count


    # @api.onchange('assign_for')
    # def onchange_assign_for(self):
    #     if self.assign_for == 'diagnosis and repair':
    #         self.env['diagnosis.repair'].create(
    #             {'order_id': self.engineer_id.order_id.id, 'engineer': self.engineer_name.id,
    #              'contact': self.engineer_id.contact, 'priority': self.engineer_id.priority,
    #              'priority_lavel_duration': self.engineer_id.priority_lavel_duration,
    #              'warranty': self.engineer_id.warranty})
            # self.env['diagnosis.repair.lines'].create({'symptoms': self.engineer_id.order_id.symptoms_lines_id.symptoms})

    def name_get(self):
        list = []
        for rec in self:
            name = str(rec.engineer_name.name) + ' ' + str(rec.task_count)
            list.append((rec.id, name))
        return list





