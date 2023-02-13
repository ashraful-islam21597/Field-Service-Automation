import datetime

from odoo import api, fields, models, _
from datetime import date
from .diagnosis_repair import DiagnosisRepair, DiagnosisRepairLines
from odoo.exceptions import ValidationError, UserError


class QualityAssurance(models.Model):
    _inherit = "field.service"

    qc_line_ids = fields.One2many('quality.assurance.lines', 'qa_id', string='QC Check List')
    qa_result = fields.Float(string="QA Result")
    qa_check_list_id = fields.Many2one('quality.list', string='QC Category')
    repair_and_diagnosis_id = fields.Many2one('diagnosis.repair', string="Repair and diagonis")
    qa_details_ids = fields.One2many('quality.assurance.details', 'so_id', store=True, string='QA Details',
                                     readonly=False)
    qa_history_ids = fields.One2many('quality.assurance.history', 'order_id', string='QA History',
                                     readonly=False)
    qa = fields.Boolean(string="QA")
    qa_check = fields.Boolean(default=False)
    assigned_engineer = fields.Many2many('res.users', 'user_id', string="Assigned Engineer")
    current_engineer = fields.Many2one('res.users', string="Current Engineer", compute='_get_current_engineer')
    qa_flag1 = fields.Boolean(string="QA Flag")
    qa_flag2 = fields.Boolean(string="QA Flag2",compute='get_qa_flag')


    def get_qa_flag(self):
        if 'default_qa_flag1' in self.env.context.keys() and self.env.context.get(
                'default_qa_flag1') == True:
            self.qa_flag2 = True

        else:
            self.qa_flag2 = False

    def _get_current_engineer(self):
        for rec in self.assigned_engineer:
            if self.env.user.id == rec.id:
                self.current_engineer = rec.id
                break
            else:
                None

    def quality_aasurance_smart_button(self):
        result = self.env["ir.actions.actions"]._for_xml_id('usl_service_erp.action_service_order_quality')
        if self.repair_status1 == 'Ready For QC':
            result['domain'] = [('id', '=', self.id)]
        return result

    def action_qa_assign(self):
        engnr = self.env['assign.engineer.details'].search([('order_id', '=', self.id)])
        val_list = []
        vals = (0, 0, {
            'engineer_name': self.env.user.id,
            'assign_for': 'quality assurance'
        })
        val_list.append(vals)
        engnr.assign_engineer_lines_ids = val_list
        self.qa = True
        return self.qa
    def assign_qa(self):
        engnr = self.env['assign.engineer.details'].search([('order_id', '=', self.id)])
        val_list = []
        vals = (0, 0, {
            'engineer_name': self.env.user.id,
            'assign_for': 'quality assurance'
        })
        val_list.append(vals)
        engnr.assign_engineer_lines_ids = val_list
        self.qa = True
        return self.qa

    def action_qa_assign_cancel(self):
        return self._quality_assurance_view_render()
    def not_assign_qa(self):
        return self._quality_assurance_view_render()


    def _quality_assurance_view_render(self):
        tree_id = self.env.ref("usl_service_erp.view_service_order_quality_tree")
        form_id = self.env.ref("usl_service_erp.view_service_order_quality_form")
        user = self.env['res.users'].browse(self._context.get('uid'))
        if user.has_group('usl_service_erp.group_service_engineer'):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Quality Assurance',
                'view_type': 'form',
                # 'view_mode': 'tree,form',
                'res_model': 'field.service',
                'domain': [
                    '|',
                    ('repair_status1', '=', 'Ready For QC'),
                    ('repair_status1', '=', 'Under QC'),
                    ('branch_name', '=', self.env['res.users'].browse(self._context.get('uid')).branch_id.id)],
                'views': [(tree_id.id, 'tree'), (form_id.id, 'form')],
                'context': {'default_qa_flag1': True},
                'target': 'current'
            }
        else:
            assign_engineer_lines = self.env['assign.engineer.lines'].search([

                ('engineer_name', '=', self.env['res.users'].browse(self._context.get('uid')).id),
                # ('assign_for', '=', 'quality assurance'),
            ])
            so_list_for_assigned_qa = []
            for i in assign_engineer_lines:
                so_list_for_assigned_qa.append(i.engineer_id.order_id.id)

            return {
                'type': 'ir.actions.act_window',
                'name': 'Quality Assurance',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'field.service',
                'domain': [
                    '|',
                    ('repair_status1', '=', 'Ready For QC'),
                    ('repair_status1', '=', 'Under QC'),
                    ('id', 'in', so_list_for_assigned_qa),
                    ('branch_name', '=', self.env['res.users'].browse(self._context.get('uid')).branch_id.id)],
                'views': [(tree_id.id, 'tree'), (form_id.id, 'form')],
                'target': 'current',
            }

    @api.onchange('qc_line_ids')
    def _onchange_qc_line_ids1(self):
        c = 0

        for i in self.qc_line_ids:
            if i.checked == True:
                c += 1
        len_qc_line_ids = len(self.qc_line_ids)

        if len_qc_line_ids != 0:
            self.qa_result = (c / len_qc_line_ids) * 100
            self.qa_details_ids.qa_result = (c / len_qc_line_ids) * 100

    @api.onchange('qa_check_list_id')
    def _onchange_qc_line_ids(self):
        qc_check = self.env['quality.list'].search([('id', '=', self.qa_check_list_id.id)])
        if qc_check.id != False:
            self.qc_line_ids = [(5, 0, 0)]
            for i in qc_check.category_ids:
                val_list = []
                vals = (0, 0, {
                    'description1': i.name,
                    'name': qc_check.category,
                })
                val_list.append(vals)
                self.qc_line_ids = val_list


class QAHistory(models.Model):
    _name = 'quality.assurance.history'

    repair_status = fields.Many2one('repair.status', string="SO Repair Status", ondelete='cascade')
    qa_status = fields.Many2one('repair.status', string="QA Status",
                                ondelete='cascade')
    qa_remarks = fields.Char(string="Remarks(QA)")
    qa_comments = fields.Char(string="Comments")
    qa_date = fields.Datetime(string='QA Date')
    order_id = fields.Many2one('field.service', string='Service Order', ondelete='cascade')
    qa_delivery_date = fields.Datetime(string='QA Delivery Date')
    create_date = fields.Datetime(string='Create Date')
    created_by = fields.Many2one('res.users', string='Created BY')
    rep_seq = fields.Char(string='Token')


class QualityAssuranceDetails(models.Model):
    _name = "quality.assurance.details"
    _description = "Quality Assurance Details"
    order_id = fields.Char(string="Order No")
    product_id = fields.Many2one('product.product', readonly=False, string="Part")
    warranty_status = fields.Many2one('warranty.status', readonly=False)
    symptoms = fields.Char(string="Symptoms")
    problem = fields.Many2one('symptoms.lines', readonly=False)
    diagnosis_date = fields.Date(string="Diagnosis Date")
    order_date = fields.Date(string="Order Date")
    service_charge = fields.Integer(string="Service Charge")
    total_amount = fields.Integer(string="Total Amount")
    customer_confirmaation = fields.Char(string="Cost")
    qa_status = fields.Many2one('repair.status', string="QA Status", domain=lambda self: self._get_repair_status(),
                                readonly='make_field_readonly',
                                ondelete='cascade')
    remarks = fields.Char(string='remarks')
    task_status = fields.Many2one('repair.status', string="Task Status", ondelete='cascade')
    qa_comments = fields.Char(string="QA Comments")
    qa_result = fields.Float(string="QA Result (%)")
    learner_id = fields.Char(string="Learner_id")
    rep_seq = fields.Char(string='Token')
    diagnosis_repair_id = fields.Many2one('diagnosis.repair', string="Diagnosis && Repair", ondelete='cascade')
    diagnosis_repair_lines_id = fields.Many2one('diagnosis.repair.lines', string="Diagnosis && Repair Lines",
                                                ondelete='cascade')
    engineer = fields.Many2one('res.users', string="Engineer", ondelete='cascade')
    so_id = fields.Many2one('field.service', string='SO', ondelete='cascade')
    approval = fields.Boolean(string="Approval")
    qa_remarks = fields.Char(string="Remarks(QA)")
    qa_delivery_date = fields.Datetime(string='QA Delivery Date')
    qa_date = fields.Datetime(string='QA Date')
    create_date = fields.Datetime(string='Create Date')
    qa_flag = fields.Boolean(default=False)

    # def _make_field_readonly(self):
    #     print(">>>>>>>>>",self.qa_status)
    #     if self.qa_status == "Under QC":
    #         print(self.qa_status)
    #         return True
    @api.onchange('qa_status')
    def _onchange_qa_status(self):
        self.task_status = self.qa_status

    def _get_repair_status(self):
        get_repair_status = self.env['repair.status'].sudo().search(
            ['|',
             ('repair_status', '=', 'Ready To Deliver'),
             ('repair_status', '=', 'QA Return')])
        domain = [('id', 'in', get_repair_status.ids)]
        return domain

    def write(self, val):
        qa_status = self.env['repair.status'].search([('id', '=', val.get("qa_status"))])
        for rec in self:
            monitoring_line = rec.env['field.service.monitoring.data'].search(
                [('so_number', '=', rec.so_id.id)])
            if monitoring_line:
                if 'engineer' in val.keys() and monitoring_line.assign_eng_qa != val['engineer']:
                    monitoring_line.assign_eng_qa = val['engineer']
                elif 'qa_date' in val.keys() and monitoring_line.assign_date_qa != val['qa_date']:
                    monitoring_line.assign_date_qa = val['qa_date']
            if val.get("qa_comments"):
                val.update({'qa_comments': val.get("qa_comments")})
                self.diagnosis_repair_lines_id.qa_comments = val.get("qa_comments")
            if val.get("qa_remarks"):
                val.update({'qa_remarks': val.get("qa_remarks")})
        if qa_status.repair_status in ("QA Return", "Ready To Deliver", "Under QC"):

            self.diagnosis_repair_id.order_id.repair_status1 = qa_status.id
            self.diagnosis_repair_lines_id.qa_status = qa_status
            self.diagnosis_repair_lines_id.diagnosis_repair.x.is_qa1 = True
            if qa_status.repair_status in ("Ready To Deliver", "QA Return"):
                val.update({'qa_delivery_date': fields.Datetime.now()})
            values = []
            vals = (0, 0, {
                'order_id': self.so_id.id,
                'qa_status': qa_status.id,
                'repair_status': self.so_id.repair_status1.id,
                'qa_delivery_date': datetime.datetime.now(),
                'qa_date': datetime.datetime.now(),
                'qa_remarks': val.get("qa_remarks"),
                'create_date': self.create_date,
                'created_by': self.env.user.id,
                'rep_seq': self.rep_seq,
                'qa_comments': val.get("qa_comments")
            })

            values.append(vals)
            self.so_id.qa_history_ids = values
        res = super(QualityAssuranceDetails, self).write(val)
        return res


class diagnosisRepairForquality(models.Model):
    _inherit = 'diagnosis.repair.lines'

    @api.model
    def create(self, val):
        if val.get('serial', _('New')) == _('New'):
            val['rep_seq'] = self.env['ir.sequence'].next_by_code('diagnosis.repair.lines') or _('New')
        res = super(diagnosisRepairForquality, self).create(val)
        status=self.env['repair.status'].search([('repair_status','=','Under QC')])

        for rec in self:
            monitoring_line = rec.env['field.service.monitoring.data'].search(
                [('so_number', '=', rec.so_id.id)])

            if monitoring_line:
                if 'engineer' in val.keys() and monitoring_line.assign_eng_qa != val['engineer']:
                    monitoring_line.assign_eng_qa = val['engineer']
                elif 'qa_date' in val.keys() and monitoring_line.assign_date_qa != val['qa_date']:
                    monitoring_line.assign_date_qa = val['qa_date']
        if res.task_status1.repair_status == 'Ready For QC':
            values = []
            vals = (0, 0, {
                'order_id': res.diagnosis_repair.order_id.order_no,
                'order_date': res.diagnosis_repair.order_id.order_date,
                'product_id': res.part.id,
                'warranty_status': res.diagnosis_repair.order_id.warranty_status.id,
                'service_charge': res.diagnosis_repair.service_charge,
                'diagnosis_date': res.diagnosis_date,
                'qa_status': status.id,
                'task_status': status.id,
                'total_amount': res.total_amount,
                'symptoms': res.symptoms.symptom,
                'learner_id': res.learner_id,
                'diagnosis_repair_id': res.diagnosis_repair.id,
                'diagnosis_repair_lines_id': res.id,
                'rep_seq': res.rep_seq,
                'create_date': datetime.datetime.now()
            })
            values.append(vals)
            res.diagnosis_repair.order_id.qa_details_ids = values
        return res

    # def write(self, vals):
    #     res = super(diagnosisRepairForquality, self).write(vals)
    #     print('yyy', vals.get('task_status1'))
    #     qa_details_lines = self.env['quality.assurance.details'].search([('diagnosis_repair_lines_id', '=', self.id)])
    #
    #     if qa_details_lines:
    #         try:
    #             print('dr edit',vals['task_status1'])
    #             p=self.env['repair.status'].search([('repair_status','=','Ready For QC')]).id
    #             print(p)
    #             if vals['task_status1'] == p :
    #                 print(qa_details_lines)
    #                 values = [(5,0,0)]
    #                 values1=[]
    #                 vals = (0, 0, {
    #                     'order_id': self.diagnosis_repair.order_id.order_no,
    #                     'order_date': self.diagnosis_repair.order_id.order_date,
    #                     'product_id': self.part.id,
    #                     'warranty_status': self.diagnosis_repair.order_id.warranty_status.id,
    #                     'service_charge': self.diagnosis_repair.service_charge,
    #                     'diagnosis_date': self.diagnosis_date,
    #                     'qa_status': self.task_status1.id,
    #                     'task_status': self.task_status1.id,
    #                     'total_amount': self.total_amount,
    #                     'symptoms': self.symptoms.symptom,
    #                     'learner_id': self.learner_id,
    #                     'diagnosis_repair_id': self.diagnosis_repair.id,
    #                     'diagnosis_repair_lines_id': self.id,
    #                     'rep_seq': self.rep_seq
    #                 })
    #                 values.append(vals)
    #                 values1.append(vals)
    #                 self.diagnosis_repair.order_id.qa_details_ids = values
    #                 self.diagnosis_repair.order_id.qa_history_ids = values1
    #                 return  res
    #         except:
    #             return res
    #     else:
    #
    #         values = []
    #         if self.task_status1.repair_status == 'Ready For QC':
    #             vals = (0, 0, {
    #                 'order_id': self.diagnosis_repair.order_id.order_no,
    #                 'order_date': self.diagnosis_repair.order_id.order_date,
    #                 'product_id': self.part.id,
    #                 'warranty_status': self.diagnosis_repair.order_id.warranty_status.id,
    #                 'service_charge': self.diagnosis_repair.service_charge,
    #                 'diagnosis_date': self.diagnosis_date,
    #                 'qa_status': self.task_status1.id,
    #                 'task_status': self.task_status1.id,
    #                 'total_amount': self.total_amount,
    #                 'symptoms': self.symptoms.symptom,
    #                 'learner_id': self.learner_id,
    #                 'diagnosis_repair_id': self.diagnosis_repair.id,
    #                 'diagnosis_repair_lines_id': self.id,
    #                 'rep_seq': self.rep_seq
    #             })
    #             values.append(vals)
    #             self.diagnosis_repair.order_id.qa_details_ids = values
    #             self.diagnosis_repair.order_id.qa_history_ids = values
    #
    #         return res
    def write(self, val):
        qa_status = self.env['repair.status'].search([('id', '=', val.get("task_status1"))])
        if qa_status.repair_status == 'Ready For QC':
            values = []
            vals = (0, 0, {
                'order_id': self.diagnosis_repair.order_id.order_no,
                'order_date': self.diagnosis_repair.order_id.order_date,
                'product_id': self.part.id,
                'warranty_status': self.diagnosis_repair.order_id.warranty_status.id,
                'service_charge': self.diagnosis_repair.service_charge,
                'diagnosis_date': self.diagnosis_date,
                'qa_status': val.get("task_status1"),
                'task_status': val.get("task_status1"),
                'total_amount': self.total_amount,
                'symptoms': self.symptoms.symptom,
                'learner_id': self.learner_id,
                'diagnosis_repair_id': self.diagnosis_repair.id,
                'diagnosis_repair_lines_id': self.id,
                'rep_seq': self.rep_seq
            })
            values.append(vals)
            self.diagnosis_repair.order_id.qa_details_ids = values
        res = super(diagnosisRepairForquality, self).write(val)
        return res


class QualityCheckListLines(models.Model):
    _name = "quality.assurance.lines"
    _rec_name = "name"
    name = fields.Char(string="Name")
    description1 = fields.Char(string="Description")
    sl_no = fields.Integer(string="serial number")
    description = fields.Many2one("quality.list.lines", name="Description", domain=[('category_id', 'ilike', 'name')])
    qa_id = fields.Many2one('field.service', string='QA Line')
    checked = fields.Boolean(string="Is Checked")


class ResUsers(models.Model):
    _inherit = 'res.users'
    department_id = fields.Many2one('field.service.department', string='Department')
