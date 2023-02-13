from odoo import api, fields, models, _
from datetime import date
from datetime import datetime
from odoo.exceptions import ValidationError


class DiagnosisRepair(models.Model):
    _name = 'diagnosis.repair'
    _description = 'Diagnosis Repair'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "repair_no"

    x = fields.Many2one('assign.engineer.lines', string='test')

    userid = fields.Many2one("res.users", default=lambda self: self.env.user.id)

    repair_no = fields.Char(string='Assign No', required=True, copy=False, readonly=True,
                            default=lambda self: _('New'))
    diagnosis_repair_lines_ids = fields.One2many('diagnosis.repair.lines', 'diagnosis_repair',
                                                 string="Diagnosis Repair")
    order_id = fields.Many2one('field.service', string="Service Order", readonly=True, tracking=True)
    warranty = fields.Many2one(related='order_id.warranty_status')
    customer = fields.Many2one(related='order_id.customer_id', string='Customer')
    contact = fields.Char(related="order_id.phone", string='Contact No', readonly=True)
    item = fields.Many2one(related="order_id.product_id", string="Item")
    priority = fields.Selection(related="order_id.priority", string="Priority")
    priority_lavel_duration = fields.Char(related="order_id.priority_lavel_duration", string='Priority Level Duration')

    possible_solution = fields.Char(string="Possible Solution")
    service_charge = fields.Integer(string="Service Charge")
    qa_status = fields.Char(string="QA Status")
    qa_comments = fields.Char(string="QA Comments")
    engineer = fields.Many2one('res.users', string="Engineer", domain=lambda self: self._get_user_domain(),
                               readonly=True)
    approval = fields.Boolean(compute='_approval', default=False)
    permission = fields.Boolean(compute='_permission', default=False)
    requisition = fields.Boolean(compute='_requisition', string='requisition', default=False)
    test = fields.Boolean(compute='test_function', string="test", default=False)
    current_repair_status = fields.Many2one(related='order_id.repair_status1', string='Current Repair Status',
                                            readonly=True)
    test1 = fields.Boolean( string="test", default=False)

    # readonly = fields.Boolean(compute='_readonly', default=False)

    # def _readonly(self):
    #     for rec in self:
    #         get_wanted_repair_status = self.env['repair.status'].sudo().search(
    #             [('repair_status', '=', 'Ready For QC')], limit=1)
    #         if rec.diagnosis_repair_lines_ids.task_status1.id == get_wanted_repair_status.id:
    #             rec.readonly = True
    #         else:
    #             rec.readonly = False

    def test_function(self):
        for rec in self:
            if rec.diagnosis_repair_lines_ids.task_status1 == 'Ready For QC':

                rec.test = True
            else:
                rec.test = False

    def action_delete(self):
        for rec in self:
            rec.diagnosis_repair_lines_ids = [(5, 0, 0)]

    def _requisition(self):
        if self.diagnosis_repair_lines_ids:
            for rec in self.diagnosis_repair_lines_ids:
                if rec.part_check == 0:
                    if rec.customer_confirmation == 'confirmed':
                        self.requisition = True
                    else:
                        self.requisition = False
                else:
                    self.requisition = False
        else:
            self.requisition = False

    def requisition_button(self):

        delivery = self.env['stock.picking.type'].search(
            [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
             ('code', '=', 'internal')])

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'view_id': self.env.ref('usl_service_erp.stock_picking_inherit_form_view').id,
            'context': {'default_reference': self.order_id.ids,
                        'default_picking_type_id': delivery.id,
                        'default_partner_id': self.customer.id,
                        'default_picking_user': True,
                        },
        }

    @api.onchange('diagnosis_repair_lines_ids')
    def set_child_warranty(self):
        for rec in self.diagnosis_repair_lines_ids:
            if self.warranty.name == "Warranty":
                rec.customer_confirmation = 'confirmed'

    @api.depends('state')
    def _permission(self):
        for rec in self:
            if rec.approval == True:
                for i in rec.diagnosis_repair_lines_ids:
                    if self.env.user.id in i.task_status1.name.ids:
                        if self.env.user.branch_id in rec.order_id.branch_name:
                            rec.permission = True
                        else:
                            rec.permission = False
                    else:
                        rec.permission = False
            else:
                rec.permission = False

    @api.depends('state')
    def _approval(self):
        for rec in self:
            rec.approval = False
            for i in rec.diagnosis_repair_lines_ids:
                if i.task_status1.is_approval == False:
                    rec.approval = False
                else:
                    rec.approval = True

    def _get_user_domain(self):
        all_users = self.env['res.users'].sudo().search([])
        get_users = self.env.ref("usl_service_erp.group_service_engineer").users
        if not isinstance(get_users, bool) and get_users:
            domain = [('id', 'in', get_users.ids)]
        else:
            domain = [('id', 'in', all_users.ids)]
        return domain

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit_for_approval', 'Submitted For Approval'),
        ('approved', 'Approved'),
        ('cancel', 'Canceled')], default='draft', string="Status", required=True)

    def action_test(self):
        return

    def action_service_for_approval(self):
        for rec in self:
            rec.state = 'submit_for_approval'

    def action_approval(self):
        for rec in self:
            rec.state = 'approved'
            get_wanted_repair_status = self.env['repair.status'].sudo().search(
                [('repair_status', '=', 'Ready For QC')], limit=1)
            if rec.diagnosis_repair_lines_ids.task_status1.id == get_wanted_repair_status.id:
                rec.order_id.active = True
            else:
                rec.order_id.active = False

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.model
    def create(self, vals):
        if vals.get('repair_no', _('New')) == _('New'):
            vals['repair_no'] = self.env['ir.sequence'].next_by_code('diagnosis.repair') or _('New')
        res = super(DiagnosisRepair, self).create(vals)

        return res

    def action_in_consultation(self):
        return


class DiagnosisRepairLines(models.Model):
    _name = "diagnosis.repair.lines"
    _description = "Assign Engineer Lines"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    item = fields.Char(string="Item")

    engineer = fields.Many2one(related='diagnosis_repair.engineer', readonly=True)

    symptoms = fields.Many2one('symptoms.type', string="Symptoms", domain="[('id','in',symptoms_domain)]",
                               tracking=True)
    learner_id = fields.Char(string="Learner_id")
    engineer_observation = fields.Many2one('engineer.observation', string="Engineer Observation", tracking=True)
    attach_diagnosis_doc = fields.Image(string="Attach Diagnosis Doc")
    diagnosis_date = fields.Date(string="Diagnosis Date", default=fields.Datetime.now, tracking=True)
    part = fields.Many2one('product.product')
    price_unit = fields.Float(related='part.list_price', digits='Product Price')
    part_check = fields.Integer(string="Stock Availability", compute='_compute_available_part')
    defective_sno = fields.Char(string="Defective CT/Serial No")
    service_charge = fields.Integer(string="Total")
    total_amount = fields.Integer(string="Total Amount")
    customer_confirmation = fields.Selection(
        [('confirmed', 'Agree'), ('cancelled', 'Not Agree')],
        string="Customer Confirmation",
        tracking=True)
    faulty_tag = fields.Char(string="Faculty Tag")
    remarks = fields.Char(string="Remarks")
    task_status = fields.Selection(
        [('repaired', 'Repaired'), ('under-repair', 'Under-Repair'), ('under-diagnosis', 'Under-Diagnosis'),
         ('return-to-customer', 'Return-To-Customer')], string="Task Status",
        tracking=True)
    task_status1 = fields.Many2one('repair.status', string="Task Status",
                                   default=lambda self: self.env['repair.status'].search(
                                       [('repair_status', '=', 'Under Diagnosis')]),
                                   domain=lambda self: self._get_assigned_domain())
    name = fields.Many2many(related='task_status1.name')
    is_approval = fields.Boolean(related='task_status1.is_approval')
    possible_solution = fields.Many2one("possible.solution.lines", string="Possible Solution")
    qa_status = fields.Many2one('repair.status', string="QA Status", readonly=True)
    qa_comments = fields.Char(string="QA Comments", readonly=True)

    current_date = fields.Date(string='Today', default=datetime.today())

    diagnosis_repair = fields.Many2one('diagnosis.repair', string="Diagnosis & Repair", tracking=True)

    rep_seq = fields.Char(string='Token', default=lambda self: _('New'))
    symptoms_domain = fields.Many2many('symptoms.type',
                                       compute="_sym_cal",
                                       readonly=True,
                                       store=False,
                                       )

    is_consumed = fields.Boolean(string="Is Consumed", default=False, readonly=True)
    possible_delivery_date = fields.Date(string='Possible Diagnosis Date')

    @api.onchange('possible_delivery_date')
    def _possible_delivery_date(self):
        for rec in self:
            assign = self.env['assign.engineer.details'].search([('order_id', '=', rec.diagnosis_repair.order_id.id)])
            for i in assign.assign_engineer_lines_ids:
                if rec.diagnosis_repair.engineer.id == i.engineer_name.id:
                    i.possible_delivery_date = rec.possible_delivery_date



    def _get_assigned_domain(self):
        get_assigned_domain = self.env['repair.status'].sudo().search(
            ['|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|',
             ('repair_status', '=', 'Under Diagnosis'),
             ('repair_status', '=', 'Under Repair'),
             ('repair_status', '=', 'Ready For Replacement'),
             ('repair_status', '=', 'Onsite Support Complete'),
             ('repair_status', '=', 'Ready For QC'),
             ('repair_status', '=', 'Return Service Invoice'),
             ('repair_status', '=', 'Sales Return(STBL)'),
             ('repair_status', '=', 'Waiting for Customer Consent'),
             ('repair_status', '=', 'Canceled/Delivered'),
             ('repair_status', '=', 'Transfer To Branch'),
             ('repair_status', '=', 'Remote / online support complete'),
             ('repair_status', '=', 'Product Return To Customer')])
        domain = [('id', 'in', get_assigned_domain.ids)]
        return domain

    @api.depends('part')
    def _compute_available_part(self):
        for rec in self:
            location_id = rec.part.warehouse_id.lot_stock_id.id
            rec.part_check = rec.part.with_context({'location': location_id}).free_qty

    @api.onchange('symptoms')
    def onchange_symptoms(self):
        for rec in self:
            return {'domain': {'possible_solution': [('symptoms_type', '=', rec.symptoms.id)]}}

    @api.depends('diagnosis_repair')
    def _sym_cal(self):
        for rec in self:
            assigned_symptom = []
            get_assigned_symptoms = rec.diagnosis_repair.diagnosis_repair_lines_ids.symptoms.ids
            res = self.env['symptoms.lines'].sudo().search(
                [('order_id', '=', rec.diagnosis_repair.order_id.id)]).symptoms.ids

            sym = self.env['symptoms.type'].sudo().search([('id', 'in', res), ('id', 'not in', get_assigned_symptoms)])

            rec.symptoms_domain = sym

    @api.onchange('diagnosis_date')
    def onchange_date(self):
        t_day = date.today()
        if self.diagnosis_date and self.diagnosis_date > t_day:
            raise ValidationError(_("You Cannot Enter Future Dates"))

    @api.onchange('task_status1')
    def so_repair_status(self):
        for rec in self:
            rec.diagnosis_repair.order_id.repair_status1 = rec.task_status1

    @api.model
    def create(self, vals):
        res = super(DiagnosisRepairLines, self).create(vals)
        res.diagnosis_repair.order_id.diagnosis_repair_count += 1
        for rec in res:
            if rec.remarks != False:
                if self.env['remarks.history'].search(
                        [('order_id', '=', rec.diagnosis_repair.order_id.id)]).id == False:
                    remark1 = self.env['remarks.history'].create({'order_id': rec.diagnosis_repair.order_id.id})
                else:
                    remark1 = self.env['remarks.history'].search([('order_id', '=', rec.diagnosis_repair.order_id.id)])
                self.env['remarks.lines'].create({'remark_id': remark1.id, 'remarks': rec.remarks,
                                                  'remarked_by': self.env.user.id,
                                                  'remarked_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                  'remarked_place': 'Diagnosis and Repair Engineer'})
        return res

    def write(self, vals):
        res = super(DiagnosisRepairLines, self).write(vals)
        try:
            if self.env['repair.status'].search(
                    [('id', '=', vals.get('task_status1'))]).repair_status == "Ready For QC":
                self.diagnosis_repair.test1 = True
            if vals['remarks']:
                remarks = self.env['remarks.history'].search([('order_id', '=', self.diagnosis_repair.order_id.id)])
                if remarks.id == False:
                    remark1 = self.env['remarks.history'].create({'order_id': self.diagnosis_repair.order_id.id})
                    self.env['remarks.lines'].create({'remark_id': remark1.id, 'remarks': self.remarks})
                else:
                    value = []
                    vals = (0, 0, {
                        'remarks': self.remarks,
                        'remark_id': remarks.id,
                        'remarked_by': self.env.user.id,
                        'remarked_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'remarked_place': 'Diagnosis and Repair Engineer',
                    })
                    value.append(vals)
                    remarks.remarks_lines_ids = value
                    return res
        except:
            return res

    @api.onchange('task_status1')
    def end_date(self):
        for rec in self:
            get_wanted_repair_status = self.env['repair.status'].sudo().search(
                [('repair_status', '=', 'Ready For QC')], limit=1)
            assign = self.env['assign.engineer.details'].search([('order_id', '=', rec.diagnosis_repair.order_id.id)])
            for i in assign.assign_engineer_lines_ids:
                if rec.diagnosis_repair.engineer.id == i.engineer_name.id:
                    if rec.task_status1.id == get_wanted_repair_status.id:
                        i.delivery_date = date.today().strftime('%Y-%m-%d')
                    else:
                        i.delivery_date = None

#
# def actions_delivery(self):
#       delivery = self.env['stock.picking.type'].search(
#           [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
#            ('code', '=', 'outgoing')])
#       return {
#
#           'name': _('Delivery'),
#           'type': 'ir.actions.act_window',
#           'res_model': 'stock.picking',
#           'view_mode': 'form',
#           'view_id': self.env.ref('usl_service_erp.view_picking_delivery_form').id,
#           'context': {'default_picking_type_id': delivery.id, 'default_partner_id': self.customer_id.id,
#                       'default_service_ids': self.ids},
#           'target': 'current',
#
#       }
