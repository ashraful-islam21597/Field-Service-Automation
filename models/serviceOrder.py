# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date
from datetime import datetime
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_is_zero
from bs4 import BeautifulSoup


class FieldService(models.Model):
    _name = "field.service"
    _description = "Field Service"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'order_no'
    _order = 'order_no DESC'

    order_no = fields.Char(string='Order No', required=True, copy=False, readonly=True,
                           default=lambda self: _('New'), tracking=True)
    order_date = fields.Date(string="Order Date", default=fields.Datetime.now, readonly=True, tracking=True)
    retail = fields.Many2one(
        'res.partner',
        string='Dealer/Retail',
        domain=['|', ('category_id', '=', 'Dealer'), ('category_id', '=', 'Retailer')], tracking=True,required=True)
    communication_media = fields.Many2one('communication.media', string='Communication Media', tracking=True,required=True)

    service_type = fields.Many2one('service.type', string='Service Type', required=True, tracking=True)
    imei_no = fields.Char(string='IMEI/Serial No', readonly=False, state={'draft': [('readonly', False)]},required=True)
    product_id = fields.Many2one('product.product', string="Product", readonly=True,required=True,
                                 state={'draft': [('readonly', False)]}, tracking=True)
    invoice = fields.Char(string='Invoice No', readonly=True, state={'draft': [('readonly', False)]}, tracking=True)
    in_attachment = fields.Binary(string='Invoice Attachment', tracking=True)
    p_date = fields.Date(string='POP Date', tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True,required=True,
                                  state={'draft': [('readonly', False)]}, tracking=True)
    warranty_status = fields.Many2one('warranty.status', string=' Warranty Status', tracking=True)
    warranty_expiry_date_l = fields.Date(string='Warranty Expiry Date(L)',
                                         state={'draft': [('readonly', False)]}, readonly=True)
    warranty_expiry_date_p = fields.Date(string='Warranty Expiry Date(P)', readonly=True,
                                         state={'draft': [('readonly', False)]})
    warranty_void_reason_1 = fields.Many2one('warranty.void.reason', string="Warranty Void Reason", tracking=True)
    guaranty_expiry_date = fields.Date(string='Guaranty Expiry Date')
    departments = fields.Many2one('field.service.department', required=True, string='Department', tracking=True, )
    priority_lavel_duration = fields.Char(string='Priority Level Duration', tracking=True)
    phone = fields.Char(string='Phone', tracking=True,required=True,size=11)
    user_id = fields.Many2one('res.users', string='users', default=lambda self: self.env.user, tracking=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')], string="Priority", tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('service_for_approval', 'Submitted For Approval'),
        ('approval', 'Approved'),
        ('cancel', 'Canceled'),
    ], default='draft', string="Status", required=True)

    priority_levels = fields.Many2one('field.service.priority.level', string='Priority Level', tracking=True)
    p_delivery_date = fields.Date(string='Possible Delivery Date', tracking=True,required=True)
    customer_remark = fields.Html(string='Customer Remark', tracking=True)
    remark = fields.Html(string='Remark', tracking=True)

    symptoms_lines_ids = fields.One2many('symptoms.lines', 'order_id', string="Symptoms", tracking=True)
    symptoms_lines_id = fields.Many2one('symptoms.lines', string="Symptoms", tracking=True)
    special_notes_ids = fields.One2many('special.notes', 'order_id', string="Special Notes", tracking=True)

    repair_status = fields.Selection([
        ('repaired', 'Repaired'),
        ('pending', 'Pending'),
        ('not_repaired', 'Not-repaired'),
        ('repairing', 'Repairing'),

    ], string='Repair Status', default='pending', tracking=True)

    repair_status1 = fields.Many2one('repair.status', string='Repair Status',
                                     readonly=True, tracking=True)
    product_receive_date = fields.Date(string='Product Receive Date', tracking=True)
    delivery_date = fields.Date(string='Delivery Date', readonly=True, tracking=True)
    item_receive_branch = fields.Many2one('res.branch', string='Item Receive Branch', tracking=True)
    item_receive_status = fields.Char(string='Item Receive Status', readonly=True)
    receive_customer = fields.Boolean(string='Is Receive From Customer', tracking=True)
    so_transfer = fields.Boolean(string='Is So Transfer', tracking=True)
    is_sms = fields.Boolean(string='Is SMS', tracking=True)
    special_note = fields.Char(string="Special Note", tracking=True)
    branch_name = fields.Many2one('res.branch', required=True, tracking=True,default=lambda self: self.env.user.branch_id)
    active = fields.Boolean(string='Active', default=True, copy=False, tracking=True)
    current_branch = fields.Many2one('res.branch', tracking=True)
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count', tracking=True)
    so_approve = fields.Boolean(compute='_so_approve', string='approve', default=False)
    hide_invoice = fields.Boolean(compute="_hide_button_invoice", string="", )
    user_branch = fields.Many2one('res.branch', string="User Branch")
    #receive_creted = fields.Boolean(string='Receive')
    is_transferable = fields.Boolean(string='Transfer',default=True)

    claim_tag = fields.Boolean(string="Has Claim")
    origin_branch = fields.Many2one('res.branch', default=lambda self: self.env.user.branch_id)
    engr_count=fields.Integer(string="Assigned Engineers")
    diagnosis_repair_count = fields.Integer(string="Total Number of Diagnosis & Repair")

    @api.onchange('warranty_void_reason_1')
    def _onchange_warranty_void_reason_1(self):

        if self.warranty_void_reason_1.id != False:
            warranty_status = self.env['warranty.status'].search([('name', '=', 'Non Warranty')])
            self.warranty_status=warranty_status.id
        else:
            warranty_status = self.env['warranty.status'].search([('name', '=', 'Warranty')])
            self.warranty_status = warranty_status.id


    def server_action_so_tree_filter_by_branch(self):
        form_id = self.env.ref('usl_service_erp.view_field_service_form').id,
        tree_id = self.env.ref('usl_service_erp.view_field_service_tree').id,
        user = self.env['res.users'].browse(self._context.get('uid'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Service Order'),
            'view_mode': 'tree,form',
            'res_model': 'field.service',
            'domain': [('branch_name', '=', user.branch_id.id)],
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'target': 'current',
        }


    def _so_approve(self):
        for rec in self:
            x = self.env['so.approval.config'].search([('user_branch', '=', rec.branch_name.id)])
            if self.env.user.id in x.user_name.ids:
                if self.env.user.department_id.id == rec.departments.id:
                    rec.so_approve = True
                else:
                    rec.so_approve = False
            else:
                rec.so_approve = False

    def set_line_number(self):
        sl_no = 0
        for line in self.symptoms_lines_ids:
            sl_no += 1
            line.sl_no = sl_no
        return sl_no

    @api.model
    def create(self, vals):
        if vals.get('order_no', ('New')) == ('New'):
            x = datetime.now()
            s = str(x.year)[2:] + str(x.month) + str(x.day)
            s1 = str(self.env['ir.sequence'].next_by_code('field.service') or _('New'))
            s2 = s1[:2] + s + s1[2:]

            vals['order_no'] = s2
            if vals.get('symptoms_lines_ids') != []:
                res = super(FieldService, self).create(vals)
                if res.warranty_status.name == 'Warranty':
                    res.claim_tag = True
                res.set_line_number()
                self.env['assign.engineer.details'].create({'order_id': res.id})

                # Section Create Monitoring Report Data Start
                self.env['field.service.monitoring.data'].create({
                    'so_number': res.id,
                    'retailer': res.retail.id,
                    'imei_no': res.imei_no,
                    'mobile': res.phone,
                    'cost_center': res.branch_name.id,
                    'brand': res.departments.id,
                    'product': res.product_id.id,
                    'customer': res.customer_id.id,
                    'warranty_status': res.warranty_status.id,
                    'so_created_by': self.env.user.id,
                    'state': res.state,
                    'so_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'service_order_date': res.order_date,
                    'service_type': res.service_type.id,
                    'repair_status': res.repair_status1.id,
                    'item_receive_branch': res.item_receive_branch.id,
                    'item_receive_status': res.item_receive_status,
                    'warranty_expiry_date_p': res.warranty_expiry_date_p,
                    'warranty_expiry_date_l': res.warranty_expiry_date_l,
                    'delivery_date': res.delivery_date,
                    'product_receive_date': res.product_receive_date,
                })
                # Section Create Monitoring Report Data End

                # Section Create Monitoring Report  Start
                monitoring_report = self.env['field.service.monitoring.report'].create({'so_number': res.id})
                self.env['field.service.monitoring.report.lines'].create({
                    'monitoring_report_id': monitoring_report.id,
                    'so_number': res.id,
                    'retailer': res.retail.id,
                    'imei_no': res.imei_no,
                    'mobile': res.phone,
                    'cost_center': res.branch_name.id,
                    'brand': res.departments.id,
                    'product': res.product_id.id,
                    'customer': res.customer_id.id,
                    'warranty_status': res.warranty_status.id,
                    'so_created_by': self.env.user.id,
                    'state': res.state,
                    'so_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'service_order_date': res.order_date,
                    'service_type': res.service_type.id,
                    'repair_status': res.repair_status1.id,
                    'item_receive_branch': res.item_receive_branch.id,
                    'item_receive_status': res.item_receive_status,
                    'product_receive_date': res.product_receive_date,
                })
                # Section Create Monitoring Report  End

                soup = BeautifulSoup(res.remark)
                if soup.get_text() != '':
                    remark1 = self.env['remarks.history'].create({'order_id': res.id})
                    self.env['remarks.lines'].create({'remark_id': remark1.id,
                                                      'remarks': soup.get_text(),
                                                      'remarked_by': self.env.user.id,
                                                      'remarked_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                      'remarked_place': 'Service Order'})
                return res
            else:
                raise ValidationError("Service Order will not be created with blank symptoms line")

    @api.onchange("imei_no")
    def _onchange_imei_number(self):
        for rec in self:
            if rec.imei_no:
                if rec.env['field.service.data'].search([('serial_no', '=', rec.imei_no)]):
                    imei_number = rec.env['field.service.data'].search([('serial_no', '=', rec.imei_no)])
                    vals={
                        'product_id':imei_number.product_id,
                        'customer_id':imei_number.customer_id,
                        'warranty_status':imei_number.warranty_status,
                        'invoice':imei_number.invoice,
                        'warranty_expiry_date_l':imei_number.warranty_expiry_date_l,
                        'warranty_expiry_date_p':imei_number.warranty_expiry_date_p,
                        'current_branch':self.env.user.branch_id.id,
                        'p_date':imei_number.p_date
                    }
                    self.update(vals)
                else:
                    raise UserError(_("Serial number invalid"))

    def write(self, vals):
        if vals.get('repair_status1'):
            if self.env['repair.status'].search([('id','=',vals.get('repair_status1'))]).is_transfer == False:
                vals.update({'is_transferable': False})
        self.set_line_number()

        # Section Write Monitoring Report Data Start
        for rec in self:
            fs_monitoring_line = rec.env['field.service.monitoring.data'].search(
                [('so_number', '=', rec.id)])
            if fs_monitoring_line:
                if 'repair_status1' in vals.keys() and fs_monitoring_line.repair_status != vals['repair_status1']:
                    fs_monitoring_line.repair_status = vals['repair_status1']
                elif 'item_receive_branch' in vals.keys() and fs_monitoring_line.item_receive_branch != vals[
                    'item_receive_branch']:
                    fs_monitoring_line.item_receive_branch = vals['item_receive_branch']
                elif 'item_receive_status' in vals.keys() and fs_monitoring_line.item_receive_status != vals[
                    'item_receive_status']:
                    fs_monitoring_line.item_receive_status = vals['item_receive_status']
                elif 'product_receive_date' in vals.keys() and fs_monitoring_line.product_receive_date != vals[
                    'product_receive_date']:
                    fs_monitoring_line.product_receive_date = vals['product_receive_date']
                elif 'state' in vals.keys() and fs_monitoring_line.state != vals['state']:
                    fs_monitoring_line.state = vals['state']

        try:
            if vals['remark']:

                remarks = self.env['remarks.history'].search([('order_id', '=', self.id)])
                if not remarks.id:
                    remark1 = self.env['remarks.history'].create({'order_id': self.id})
                    self.env['remarks.lines'].create({'remark_id': remark1.id,
                                                      'remarks': str(self.remark)[3:-4],
                                                      'remark_id': remarks.id,
                                                      'remarked_by': self.env.user.id,
                                                      'remarked_date': date.today(),
                                                      'remarked_place': 'Service Order', })
                else:
                    value = []
                    soup = BeautifulSoup(self.remark)
                    vals = (0, 0, {
                        'remarks': soup.get_text(),
                        'remark_id': remarks.id,
                        'remarked_by': self.env.user.id,
                        'remarked_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'remarked_place': 'Service Order',
                    })
                    value.append(vals)
                    remarks.remarks_lines_ids = value
            return super(FieldService, self).write(vals)
        except:
            return super(FieldService, self).write(vals)

    def action_invoice(self):
        line = []
        for rec in self:
            for so in rec:
                dr = self.env['diagnosis.repair'].search([('order_id', '=', so.ids[0])])
                sts = self.env['service.type.setup'].search([('so_service_type', '=', rec.service_type.id)])
                for pr in sts.service_item:
                    line.append({
                        'product_id': pr.id,
                        'price_unit': pr.list_price,
                        'quantity': 1,
                    })
                for i in dr.diagnosis_repair_lines_ids:
                    line.append({
                        'product_id': i.part.id,
                        'account_id': i.part.property_account_expense_id.id,
                        'price_unit': i.part.list_price,
                        'quantity': 1,
                        'discount': 0.0,
                    })

        move_create = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'service_invoice_flag': True,
            'partner_id': self.customer_id.id,
            'branch_id': self.branch_name.id,
            'service_type': self.service_type.id,
            'so_number': self.id,
            'invoice_line_ids': line
        })

        return {
            'name': _('Service Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move_create.id,
            'target': 'current',
            'context': {'service_invoice_flag': True},
            'domain': [('id', '=', move_create.id)],

        }

    def actions_delivery(self):

        for rec in self:
            delivery = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
                 ('code', '=', 'outgoing')])
            result = self.env["ir.actions.actions"]._for_xml_id('usl_service_erp.action_field_service_delivery')
            query = """select stock_picking_id from stock_picking_rel where field_service_id={}""".format(
                rec.id)
            self._cr.execute(query=query)
            get_relevant_picking = self._cr.fetchall()
            relevant_picking = []
            if get_relevant_picking:
                for res in get_relevant_picking:
                    relevant_picking.append(res[0])
            picking = self.env['stock.picking'].search(
                [(
                    'picking_type_id', 'in',
                    self.env['stock.picking.type'].sudo().search([('code', '=', 'outgoing')]).ids),
                    ('id', 'in', relevant_picking)])
            result['domain'] = [('id', 'in', picking.ids)]

            result['context'] = {'default_picking_type_id': delivery.id,
                                 'default_partner_id': rec.customer_id.id,
                                 'default_service_ids': rec.ids,
                                 'default_is_create': True,
                                 'default_picking_delivery': True
                                 }
        return result

    def _compute_invoice_count(self):
        for rec in self:
            invoice_count = self.env['account.move'].search_count([('so_number', '=', rec.id)])
            rec.invoice_count = invoice_count

    @api.depends('invoice_count')
    def _hide_button_invoice(self):
        for rec in self:
            count = 0
            get_invoices = self.env['account.move'].search([('so_number', '=', rec.id)])
            for line in get_invoices:
                if line.state != 'cancel' and line.state == 'posted':
                    count = 1
            if count == 1:
                rec.hide_invoice = True
            else:
                rec.hide_invoice = False

    def action_view_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'View Invoice',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('so_number', '=', self.id)],
            'context': {'service_invoice_flag': True},
        }

    def actions_test(self):
        for rec in self:
            if rec.state != "approval":
                # raise exec("Service Order is not approved")
                raise ValidationError("Service Order is not approved yet")
            else:
                return

    def transfer_button(self):
        for rec in self:
            if rec.state != "approval":
                raise ValidationError("Service Order is not approved yet")
            elif self.repair_status1.is_transfer == False:
                raise ValidationError(
                    "Service Order is not permitted when Repair status is in '" + self.repair_status1.repair_status + "'")
            else:
                if rec.receive_customer != True:
                    raise ValidationError("Service Order Item is not received yet")
                else:
                    user = self.env['res.users'].browse(self._context.get('uid'))
                    if rec.so_transfer == True:
                        warehouse_data = self.env['stock.warehouse'].search([
                            ('branch_id', '=', rec.item_receive_branch.id),
                            ('company_id', '=', user.company_id.id),
                        ], limit=1)
                    else:
                        warehouse_data = self.env['stock.warehouse'].search([
                            ('branch_id', '=', rec.branch_name.id),
                            ('company_id', '=', user.company_id.id),
                        ], limit=1)
                    result = self.env["ir.actions.actions"]._for_xml_id('usl_service_erp.action_order_transfer')
                    picking_type = self.env['stock.picking.type'].search(
                        [('warehouse_id', '=', warehouse_data.id),
                         ('code', '=', 'internal')], limit=1)
                    picking = self.env['stock.picking'].search(
                        [('picking_type_id', '=', picking_type.id),
                         ('service_order_id', '=', rec.ids)]).ids
                    if picking:
                        result['domain'] = [('id', '=', picking)]
                    else:
                        result['context'] = {'default_service_order_id': rec.ids,
                                             'default_custom_operation_transfer': True,
                                             'default_picking_type_id': picking_type.id}

                        res = self.env.ref('usl_service_erp.view_picking_form_field_service_transfer', False)
                        form_view = [(res and res.id or False, 'form')]
                        result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if
                                                       view != 'form']
                    return result

    def receive_button(self):

        for rec in self:

            user = self.env['res.users'].browse(self._context.get('uid'))
            if rec.receive_customer == True:
                location_id_returnable_damage = self.env['stock.location'].search(
                    [('branch_id', '=', rec.branch_name.id),
                     ('is_returnable_damage', '=', True)], limit=1)
                warehouse_data = self.env['stock.warehouse'].search([
                    ('branch_id', '=', rec.item_receive_branch.id),
                    ('company_id', '=', user.company_id.id),
                    ('lot_stock_id', '=', location_id_returnable_damage.location_id.id),


                ])


            else:
                location_id_returnable_damage = self.env['stock.location'].search(
                    [('branch_id', '=', rec.branch_name.id),
                     ('is_returnable_damage', '=', True)], limit=1)

                warehouse_data = self.env['stock.warehouse'].search([
                    ('branch_id', '=', rec.branch_name.id),
                    ('company_id', '=', user.company_id.id),
                    ('lot_stock_id', '=', location_id_returnable_damage.location_id.id),

                ])

            picking_type = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', warehouse_data.id),
                 ('code', '=', 'incoming')], limit=1)
            picking = self.env['stock.picking'].search(
                [('picking_type_id', '=', picking_type.id),
                 ('service_order_id', '=', rec.id)]).id
            if rec.state != "approval":
                raise ValidationError("Service Order is not approved yet")
            else:
                result = self.env["ir.actions.actions"]._for_xml_id('usl_service_erp.action_order_receive')
                if picking:
                    result['domain'] = [('id', '=', picking)]

                else:

                    result['context'] = {'default_service_order_id': rec.ids,
                                         'default_custom_operation_receive': True,
                                         'default_picking_type_id': picking_type.id,
                                         'default_partner_id': self.customer_id.id,

                                         #'default_location_dest_id': picking_type.default_location_dest_id.id,
                                         'default_location_dest_id': location_id_returnable_damage.id,
                                         'default_location_id': 4,
                                         }

                    res = self.env.ref('usl_service_erp.view_picking_form_field_service_receive', False)
                    form_view = [(res and res.id or False, 'form')]
                    result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if
                                                   view != 'form']
                return result

    def action_remarks(self):
        if self.state != "approval":
            # raise exec("Service Order is not approved")
            raise ValidationError("Service Order is not approved yet")
        else:
            if self.receive_customer != True:
                raise ValidationError("Service Order Item is not received yet")
            else:

                engineers = self.env['remarks.history'].search([('order_id', '=', self.id)])
                result = self.env["ir.actions.actions"]._for_xml_id('usl_service_erp.action_remarks_history')
                # override the context to get rid of the default filtering on operation type
                result['context'] = {'default_order_id': self.id}
                # choose the view_mode accordingly
                if not engineers or len(engineers) > 1:
                    result['domain'] = [('id', 'in', engineers.ids)]
                elif len(engineers) == 1:
                    res = self.env.ref('usl_service_erp.view_remarks_history_form', False)
                    form_view = [(res and res.id or False, 'form')]
                    result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if
                                                   view != 'form']
                    result['res_id'] = engineers.id
                return result

    def reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_service_for_approval(self):
        for rec in self:
            rec.state = 'service_for_approval'


    def action_approval(self):
        for rec in self:
            pending = self.env['repair.status'].search(
                [('repair_status', '=', 'Pending')])
            rec.state = 'approval'
            rec.repair_status1 = pending.id

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_symptoms(self):
        return

    def action_view_assign(self):
        if self.state != "approval":
            # raise exec("Service Order is not approved")
            raise ValidationError("Service Order is not approved yet")
        else:
            if self.receive_customer != True:
                raise ValidationError("Service Order Item is not received yet")
            else:

                engineers = self.env['assign.engineer.details'].search([('order_id', '=', self.id)])
                result = self.env["ir.actions.actions"]._for_xml_id('usl_service_erp.action_assign_engineer_details')
                # override the context to get rid of the default filtering on operation type
                result['context'] = {'default_order_id': self.id}
                # choose the view_mode accordingly
                if not engineers or len(engineers) > 1:
                    result['domain'] = [('id', 'in', engineers.ids)]
                elif len(engineers) == 1:
                    res = self.env.ref('usl_service_erp.view_assign_engineer_details_form', False)
                    form_view = [(res and res.id or False, 'form')]
                    result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if
                                                   view != 'form']
                    result['res_id'] = engineers.id
                return result

    def action_diagnosis_repair(self):
        if self.state != "approval":
            # raise exec("Service Order is not approved")
            raise ValidationError("Service Order is not approved yet")
        else:
            if self.receive_customer != True:
                raise ValidationError("Service Order Item is not received yet")
            else:

                return {
                    'name': _('Diagnosis Repair'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'diagnosis.repair',
                    'view_mode': 'tree,form',
                    'context': {'default_order_id': self.id},
                    'target': 'current',
                    'domain': [('order_id', '=', self.id)],
                }

    def action_item_consumption(self):
        orderid = self.env['item.consumption'].search([('order_id', '=', self.id)])
        result = self.env["ir.actions.actions"]._for_xml_id('usl_service_erp.action_item_consumption')
        result['context'] = {'default_order_id': self.id}
        if not orderid or len(orderid) > 1:
            result['domain'] = [('id', 'in', orderid.ids)]
        elif len(orderid) == 1:
            res = self.env.ref('usl_service_erp.view_item_consumption_form', False)
            form_view = [(res and res.id or False, 'form')]
            result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if
                                           view != 'form']
            result['res_id'] = orderid.id
        return result


class ResUsers(models.Model):
    _inherit = "res.users"
    _rec_name = "name"

    task_count = fields.Integer(string='Task Count', compute='_compute_task_count', tracking=True)

    def _compute_task_count(self):
        for rec in self:
            task_count = self.env['diagnosis.repair'].search_count(
                ['&', '&', ('engineer', '=', rec.name), ('state', '!=', 'approved'), ('test1', '!=', True)
                 ])
            rec.task_count = task_count

    def name_get(self):
        list = []
        for rec in self:
            name = str(rec.name) + ' ' + '(' + str(rec.task_count) + ')'
            list.append((rec.id, name))
        return list

    def _get_domain(self):
        for rec in self:
            if rec.has_group('usl_service_erp.group_service_manager'):
                return []
            if rec.has_group('usl_service_erp.group_service_engineer'):
                return [('engineer', '=', rec.id)]
            else:
                return []

    def get_so_domain(self):
        logged_user_allowed_branches = self.env.user.branch_ids
        if logged_user_allowed_branches:
            return [('branch_name', 'in', logged_user_allowed_branches.ids)]
        else:
            return [('branch_name', '=', 0)]




class SymptomsLines(models.Model):
    _name = "symptoms.lines"
    _description = "Symptoms Lines"

    sl_no = fields.Integer(string='SLN.')
    symptoms = fields.Many2one('symptoms.type', string="Symptoms")
    reason = fields.Many2one("reasons.type", string="Reason")
    order_id = fields.Many2one('field.service', string="Order")


class SpecialNotes(models.Model):
    _name = "special.notes"
    _description = "Special Notes"

    sl_no = fields.Integer(string='SLN.', tracking=True)
    wui = fields.Char(string="Windows User Id")
    wup = fields.Char(string="Windows User Password")
    bui = fields.Char(string="BIOS User Id")
    bup = fields.Char(string="BIOS User Password")
    order_id = fields.Many2one('field.service', string="Order")
