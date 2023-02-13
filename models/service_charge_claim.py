from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tests.common import Form
from odoo.exceptions import ValidationError
from datetime import datetime
import time


class ServiceChargeClaim(models.Model):
    _inherit = 'account.move'

    claim_flag = fields.Boolean(default=False)
    claim_no = fields.Char(string="Claim No. ", default=lambda self: _('New'))
    claim_date = fields.Datetime(string="Claim Date")
    description = fields.Char(string="Description")
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    dept = fields.Many2one('field.service.department', string='Department' ,domain=lambda  self:self.get_department())
    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,
                               default=lambda self: self._get_invoice_data(),
                               states={'draft': [('readonly', False)]})
    per_unit_cost = fields.Integer(string="Per Unit Cost")
    claim_approve = fields.Boolean(compute='_claim_approve', string='approve', default=False)
    claim_type = fields.Selection([('splc', 'Serial Product Labour Claim'),
                                   ('nsplc', 'Non Serial Product Labour Claim')], string='Claim Type')
    nspr_labour_claim_flag = fields.Boolean(default=False)
    nspr_claim_approve = fields.Boolean(compute='_claim_approve', string='approve', default=False)
    brand = fields.Many2one('product.brand', string='Brand',domain=lambda self:self.get_brand())
    part_claim_flag = fields.Boolean(default=False)



    def get_department(self):
            d=self.env['claim.management'].search([('type','=','splc')])
            list=[]
            for rec in d:
                list.append(rec.dept.id)
            domain=[('id','in',list)]
            return domain

    def get_brand(self):
            d = self.env['claim.management'].search([('type', '=', 'nsplc')])
            domain = [('id', 'in', d.brand.ids)]
            return domain



    def _claim_approve(self):
        for rec in self:
            x = self.env['claim.approval.config'].search([('user_branch', '=', rec.branch_id.id)])
            if self.env.user.id in x.user_name.ids:
                rec.claim_approve = True
            else:
                rec.claim_approve = False

    def _get_invoice_data(self):

        if 'default_claim_flag' in self.env.context.keys() and self.env.context.get('default_claim_flag') == True or \
                'default_nspr_labour_claim_flag' in self.env.context.keys() and self.env.context.get(
            'default_nspr_labour_claim_flag') == True:
            return fields.Date.today()

    @api.model
    def create(self, vals):
        res = super(ServiceChargeClaim, self).create(vals)
        if 'default_claim_flag' in self.env.context.keys() and self.env.context.get('default_claim_flag') == True:
            for  rec in res.invoice_line_ids:
                if rec.id == False:
                    raise UserError(_('Null invoice'))
            # if vals.get('claim_no', ('New')) == ('New'):
            #     if res.claim_type == 'splc':
            #         val = self.env['ir.sequence'].next_by_code('so.claim') or _('New')
            #         res.name = val
            #     elif res.claim_type == 'nsplc':
            #         val = self.env['ir.sequence'].next_by_code('nspr.claim') or _('New')
            #         res.name = val


        return res

    @api.model
    def _move_autocomplete_invoice_lines_create(self, vals_list):
        if 'claim_flag' in vals_list[0].keys():
            new_vals_list = []
            if vals_list[0]['claim_type'] == 'nsplc':
                if vals_list[0].get('invoice_line_ids') != None:
                    for line in vals_list[0].get('line_ids'):

                        for inv_line in vals_list[0].get('invoice_line_ids'):
                            if inv_line[2]['nspr_id'] == line[2]['nspr_id']:
                                line[2]['brand'] = inv_line[2]['brand']
                                line[2]['nspr_id'] = inv_line[2]['nspr_id']
                                line[2]['received_date'] = inv_line[2]['received_date']
                if vals_list[0].get('line_ids'):
                    vals_list[0].pop('invoice_line_ids', None)
                    new_vals_list.append(vals_list[0])
                return new_vals_list
            elif vals_list[0]['claim_type'] == 'splc':
                if vals_list[0].get('invoice_line_ids') != None:
                    for line in vals_list[0].get('line_ids'):
                        for inv_line in vals_list[0].get('invoice_line_ids'):
                            if inv_line[2]['order_id'] == line[2]['order_id']:

                                line[2]['brand'] = inv_line[2]['brand']
                                line[2]['order_id'] = inv_line[2]['order_id']
                                line[2]['service_order_date'] = inv_line[2]['service_order_date']

                if vals_list[0].get('line_ids') != None:
                    vals_list[0].pop('invoice_line_ids', None)
                    new_vals_list.append(vals_list[0])

                return new_vals_list
            else:
                return super(ServiceChargeClaim, self)._move_autocomplete_invoice_lines_create(vals_list)
        else:
            return super(ServiceChargeClaim, self)._move_autocomplete_invoice_lines_create(vals_list)


    @api.onchange('brand', 'partner_id', 'from_date', 'to_date')
    def _onchange_brand(self):
        if self.claim_type == 'nsplc':
            for rec in self:
                brand = self.env['claim.management'].search(
                    [('type', '=', 'nsplc'), ('brand', '=', rec.brand.id)])
                service_orders = self.env['stock.picking'].search([
                    ('scheduled_date', '>=', self.from_date),
                    ('scheduled_date', '<=', self.to_date),
                    ('name', 'ilike', 'NSPR'),
                    ('is_claimed', '=', False),
                    ('branch_id', '=', self.env.user.branch_id.id),
                ])
                self.per_unit_cost = brand.unite_price
                rec.invoice_line_ids = [(5, 0, 0)]
                rec.line_ids = [(5, 0, 0)]
                line = [(5, 0, 0)]
                line1 = [(5, 0, 0)]
                x = 0
                for i in service_orders:
                    for service in i.move_ids_without_package:
                        if service.product_brand == self.brand:
                            x = x + brand.unite_price
                            line.append((0, 0, {
                                'product_id': service.product_id.id,
                                'account_id': brand.property_account_income_id.id,
                                'brand': service.product_brand.id,
                                'branch_id': self.env.user.branch_id.id,
                                'price_unit': brand.unite_price,
                                'nspr_id': i.id,
                                'nspr_name': i.name,
                                'received_date': i.scheduled_date,
                                'price_subtotal': brand.unite_price,
                                'credit': brand.unite_price,
                            }))
                if self.partner_id:
                    line1.append((0, 0, {
                        'account_id': self.partner_id.property_account_receivable_id.id,
                        'branch_id': self.env.user.branch_id.id,
                        'debit': x,
                        'exclude_from_invoice_tab': True,

                    }))
                    rec.line_ids = line1
                rec.invoice_line_ids = line

    @api.onchange('dept', 'partner_id', 'from_date', 'to_date')
    def _onchange_dept(self):
        if self.claim_type == 'splc':
            if self.partner_id and self.dept and self.from_date and self.to_date:
                for rec in self:
                    department = self.env['claim.management'].search(
                        [('type', '=', 'splc'), ('dept', '=', rec.dept.id)])

                    service_orders = self.env['field.service'].search([
                        ('order_date', '>=', self.from_date),
                        ('order_date', '<=', self.to_date),
                        ('branch_name', '=', self.env.user.branch_id.id),
                        ('departments', '=', rec.dept.id),
                        ('claim_tag', '=', True)])

                    self.per_unit_cost = department.unite_price

                    # self.to_date = (fields.Date.today() - relativedelta(
                    #     days=+fields.Date.today().day)) + relativedelta(days=+department.claim_date)
                    # self.to_date = (fields.Date.today() - relativedelta(
                    #     days=+fields.Date.today().day)) + relativedelta(days=+department.claim_date)
                    rec.invoice_line_ids = [(5, 0, 0)]
                    rec.line_ids = [(5, 0, 0)]
                    line = [(5, 0, 0)]
                    line1 = [(5, 0, 0)]
                    x = 0
                    for service in service_orders:
                        # self.from_date = (fields.Date.today() - relativedelta(
                        # days=+fields.Date.today().day))
                        if self.from_date < service.order_date < self.to_date:
                            x = x + department.unite_price
                            line.append((0, 0, {
                                'product_id': service.product_id.id,
                                'brand': service.product_id.brand.id,
                                'account_id': department.property_account_income_id.id,
                                'branch_id': self.env.user.branch_id.id,
                                'price_unit': department.unite_price,
                                'order_id': service.id,
                                'price_subtotal': department.unite_price,
                                'service_order_date': service.order_date,
                                'credit': department.unite_price,
                            }))

                    if self.partner_id:
                        line1.append((0, 0, {
                            'account_id': self.partner_id.property_account_receivable_id.id,
                            'branch_id': self.env.user.branch_id.id,
                            'debit': x,
                            'exclude_from_invoice_tab': True,

                        }))
                        rec.line_ids = line1
                    rec.invoice_line_ids = line




class ServiceChargeMoveline(models.Model):
    _inherit = 'account.move.line'
    branch_id = fields.Many2one('res.branch', string="Branch", store=True)
    order_id = fields.Many2one('field.service', string="Service Order", store=True)
    service_order_date = fields.Date(string="Service Order Date", store=True)
    nspr_id = fields.Many2one('stock.picking', string="Description", store=True)
    brand = fields.Many2one('product.brand', string="Brand", store=True,ondelete='cascade')
    received_date = fields.Date(string="Received Date", store=True)
    nspr_name = fields.Char(string="Non Serial Product Label")
    nspr_tree_flag = fields.Boolean(related='move_id.nspr_labour_claim_flag', default=False)

    def create(self, vals):
        res = super(ServiceChargeMoveline, self).create(vals)
        for rec in res:
            if rec.move_id.claim_type == 'splc':
                rec.order_id.claim_tag = False
            elif rec.move_id.claim_type == 'nsplc':
                rec.nspr_id.is_claimed = True
        return res


class NonserialProductClaim(models.Model):
    _inherit = "stock.picking"
    _order = 'name desc'
    is_claimed = fields.Boolean(string="is_claimed", default=False)


class NonSerialProductReceiveFromCustomerInherit(models.Model):
    _inherit = "stock.move"
    _order = 'name desc'
    nspr_labour_claim_tag = fields.Boolean(string="NSPR Labour Claim", default=False)
    product_brand = fields.Many2one(related='product_id.brand', string="Brand",ondelete='cascade',required=True)
    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            if self.product_id.brand:
                self.product_brand = self.product_id.brand
            # else:
            #     raise UserError(_("Serial number invalid"))
# from dateutil.relativedelta import relativedelta
# from odoo import api, fields, models, _
# from odoo.tests.common import Form
# from odoo.exceptions import ValidationError
# from datetime import datetime
#
# import time
#
#
# class ServiceChargeClaim(models.Model):
#     _inherit = 'account.move'
#
#     claim_flag = fields.Boolean(default=False)
#     claim_no = fields.Char(string="Claim No. ", default=lambda self: _('New'))
#     claim_date = fields.Datetime(string="Claim Date")
#     description = fields.Char(string="Description")
#     from_date = fields.Date(string="From Date")
#     to_date = fields.Date(string="To Date")
#     # partner = fields.Many2one('res.partner', string='Supplier/Principle')
#     partner_id = fields.Many2one('res.partner', string='Supplier/Principle')
#     dept = fields.Many2one('field.service.department', string='Department', domain=lambda self: self.get_department())
#     invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,
#                                default=lambda self: self._get_invoice_data(),
#                                states={'draft': [('readonly', False)]})
#     per_unit_cost = fields.Integer(string="Per Unit Cost")
#     claim_approve = fields.Boolean(compute='_claim_approve', string='approve', default=False)
#     claim_type = fields.Selection([('splc', 'Serial Product Labour Claim'),
#                                    ('nsplc', 'Non Serial Product Labour Claim')], default='splc', string='Claim Type')
#     nspr_labour_claim_flag = fields.Boolean(default=False)
#     nspr_claim_approve = fields.Boolean(compute='_claim_approve', string='approve', default=False)
#     brand = fields.Many2one('product.brand', string='Brand', domain=lambda self: self.get_brand())
#
#     def get_department(self):
#         d = self.env['claim.management'].search([('type', '=', 'splc')])
#         list = []
#         for rec in d:
#             list.append(rec.dept.id)
#
#         domain = [('id', 'in', list)]
#         print('splc', domain)
#         return domain
#
#     def get_brand(self):
#         d = self.env['claim.management'].search([('type', '=', 'nsplc')])
#         domain = [('id', 'in', d.brand.ids)]
#         print('nsplc', domain)
#         return domain
#
#     def _claim_approve(self):
#         for rec in self:
#             x = self.env['claim.approval.config'].search([('user_branch', '=', rec.branch_id.id)])
#             if self.env.user.id in x.user_name.ids:
#                 rec.claim_approve = True
#             else:
#                 rec.claim_approve = False
#
#     def _get_invoice_data(self):
#
#         if 'default_claim_flag' in self.env.context.keys() and self.env.context.get('default_claim_flag') == True or \
#                 'default_nspr_labour_claim_flag' in self.env.context.keys() and self.env.context.get(
#             'default_nspr_labour_claim_flag') == True:
#             return fields.Date.today()
#
#     # @api.model
#     # def create(self, vals):
#     #
#     #     if 'default_claim_flag' in self.env.context.keys() and self.env.context.get('default_claim_flag') == True:
#     #         res = super(ServiceChargeClaim, self).create(vals)
#     #         if vals.get('claim_no', ('New')) == ('New'):
#     #             if res.claim_type == 'splc':
#     #                 val = self.env['ir.sequence'].next_by_code('so.claim') or _('New')
#     #                 res.name = val
#     #             elif vals.get('claim_no', ('New')) == ('New'):
#     #                 if res.claim_type == 'nsplc':
#     #                     val = self.env['ir.sequence'].next_by_code('nspr.claim') or _('New')
#     #                     res.name = val
#     #         return res
#     #     else:
#     #         None
#
#     @api.model
#     def _move_autocomplete_invoice_lines_create(self, vals_list):
#         if 'claim_flag' in vals_list[0].keys():
#             new_vals_list = []
#             if vals_list[0]['claim_type'] == 'nsplc':
#                 if vals_list[0].get('invoice_line_ids') != None:
#                     for line in vals_list[0].get('line_ids'):
#
#                         for inv_line in vals_list[0].get('invoice_line_ids'):
#                             if inv_line[2]['nspr_id'] == line[2]['nspr_id']:
#                                 line[2]['brand'] = inv_line[2]['brand']
#                                 line[2]['nspr_id'] = inv_line[2]['nspr_id']
#                                 line[2]['received_date'] = inv_line[2]['received_date']
#                 if vals_list[0].get('line_ids'):
#                     vals_list[0].pop('invoice_line_ids', None)
#                     new_vals_list.append(vals_list[0])
#                 return new_vals_list
#             elif vals_list[0]['claim_type'] == 'splc':
#                 if vals_list[0].get('invoice_line_ids') != None:
#                     for line in vals_list[0].get('line_ids'):
#                         for inv_line in vals_list[0].get('invoice_line_ids'):
#                             if inv_line[2]['order_id'] == line[2]['order_id']:
#                                 print(inv_line[2]['order_id'])
#                                 line[2]['brand'] = inv_line[2]['brand']
#                                 line[2]['order_id'] = inv_line[2]['order_id']
#                                 line[2]['service_order_date'] = inv_line[2]['service_order_date']
#                 # return super(ServiceChargeClaim, self)._move_autocomplete_invoice_lines_create(vals_list)
#                 # if not vals_list[0].get('invoice_line_ids'):
#                 #     new_vals_list.append(vals_list[0])
#
#                 if vals_list[0].get('line_ids'):
#                     vals_list[0].pop('invoice_line_ids', None)
#                     new_vals_list.append(vals_list[0])
#                 return new_vals_list
#             else:
#                 return super(ServiceChargeClaim, self)._move_autocomplete_invoice_lines_create(vals_list)
#         else:
#             return super(ServiceChargeClaim, self)._move_autocomplete_invoice_lines_create(vals_list)
#
#     @api.onchange('dept', 'brand', 'partner_id', 'from_date', 'to_date')
#     def _onchange_dept(self):
#         if self.claim_type == 'splc':
#             for rec in self:
#                 department = self.env['claim.management'].search(
#                     [('type', '=', 'splc'), ('dept', '=', rec.dept.id)])  # query for department and product
#                 dept_as_product = self.env['product.product'].search(
#                     [('name', '=', department.dept.name),
#                      ('product_type', '=', 'sp')
#                      ])  # query for  product
#                 service_orders = self.env['field.service'].search([
#                     ('order_date', '>=', self.from_date),
#                     ('order_date', '<=', self.to_date),
#                     ('branch_name', '=', self.env.user.branch_id.id),
#                     ('departments', '=', rec.dept.id),
#                     ('claim_tag', '=', True)])  # query for  field service
#
#                 self.per_unit_cost = department.unite_price
#
#                 # self.to_date = (fields.Date.today() - relativedelta(
#                 #     days=+fields.Date.today().day)) + relativedelta(days=+department.claim_date)
#                 # self.to_date = (fields.Date.today() - relativedelta(
#                 #     days=+fields.Date.today().day)) + relativedelta(days=+department.claim_date)
#                 rec.invoice_line_ids = [(5, 0, 0)]
#                 rec.line_ids = [(5, 0, 0)]
#                 line = [(5, 0, 0)]
#                 line1 = [(5, 0, 0)]
#                 x = 0
#                 for service in service_orders:
#                     print(">>", department.unite_price, )
#                     # self.from_date = (fields.Date.today() - relativedelta(
#                     # days=+fields.Date.today().day))
#                     # if self.from_date < service.order_date < self.to_date:
#                     x = x + department.unite_price
#                     line.append((0, 0, {
#                         'product_id': service.product_id.id,
#                         'brand': service.product_id.brand.id,
#                         'account_id': dept_as_product.property_account_income_id.id,
#                         'branch_id': self.env.user.branch_id.id,
#                         'price_unit': department.unite_price,
#                         'order_id': service.id,
#                         'price_subtotal': department.unite_price,
#                         'service_order_date': service.order_date,
#                         'credit': department.unite_price,
#                     }))
#
#                 if self.partner_id:
#                     line1.append((0, 0, {
#                         'account_id': self.partner_id.property_account_receivable_id.id,
#                         'branch_id': self.env.user.branch_id.id,
#                         'debit': x,
#                         'exclude_from_invoice_tab': True,
#
#                     }))
#                     rec.line_ids = line1
#                 rec.invoice_line_ids = line
#         elif self.claim_type == 'nsplc':
#             for rec in self:
#                 department = self.env['claim.management'].search(
#                     [('type', '=', 'nsplc'), ('brand', '=', rec.brand.id)])  # query for department and product
#                 dept_as_product = self.env['product.template'].search(
#                     [('brand', '=', department.brand.id),
#                      ('product_type', '=', 'nsp')
#                      ])  # query for  product
#                 service_orders = self.env['stock.picking'].search([
#                     ('scheduled_date', '>=', self.from_date),
#                     ('scheduled_date', '<=', self.to_date),
#                     ('name', 'ilike', 'NSPR'),
#                     ('is_claimed', '=', False),
#                     ('branch_id', '=', self.env.user.branch_id.id),
#                 ])
#                 self.per_unit_cost = department.unite_price
#                 rec.invoice_line_ids = [(5, 0, 0)]
#                 rec.line_ids = [(5, 0, 0)]
#                 line = [(5, 0, 0)]
#                 line1 = [(5, 0, 0)]
#                 x = 0
#                 for i in service_orders:
#                     for service in i.move_ids_without_package:
#                         if service.product_brand == self.brand:
#                             x = x + department.unite_price
#                             line.append((0, 0, {
#                                 'product_id': service.product_id.id,
#                                 'account_id': dept_as_product.property_account_income_id.id,
#                                 'brand': service.product_brand.id,
#                                 'branch_id': self.env.user.branch_id.id,
#                                 'price_unit': department.unite_price,
#                                 'nspr_id': i.id,
#                                 'nspr_name': i.name,
#                                 'received_date': i.scheduled_date,
#                                 'price_subtotal': department.unite_price,
#                                 'credit': department.unite_price,
#                             }))
#                 if self.partner_id:
#                     line1.append((0, 0, {
#                         'account_id': self.partner_id.property_account_receivable_id.id,
#                         'branch_id': self.env.user.branch_id.id,
#                         'debit': x,
#                         'exclude_from_invoice_tab': True,
#
#                     }))
#                     rec.line_ids = line1
#                 rec.invoice_line_ids = line
#
#
# class ServiceChargeMoveline(models.Model):
#     _inherit = 'account.move.line'
#     branch_id = fields.Many2one('res.branch', string="Branch", store=True)
#     order_id = fields.Many2one('field.service', string="Service Order", store=True)
#     service_order_date = fields.Date(string="Service Order Date", store=True)
#     nspr_id = fields.Many2one('stock.picking', string="Non Serial Product Label", store=True)
#     brand = fields.Many2one('product.brand', string="Brand", store=True)
#     received_date = fields.Date(string="Received Date", store=True)
#     nspr_name = fields.Char(string="Non Serial Product Label")
#     nspr_tree_flag = fields.Boolean(related='move_id.nspr_labour_claim_flag', default=False)
#
#     def create(self, vals):
#         res = super(ServiceChargeMoveline, self).create(vals)
#         for rec in res:
#             if rec.move_id.claim_type == 'splc':
#                 rec.order_id.claim_tag = False
#             elif rec.move_id.claim_type == 'nsplc':
#                 rec.nspr_id.is_claimed = True
#         return res
#
#
# class NonserialProductClaim(models.Model):
#     _inherit = "stock.picking"
#     _order = 'name desc'
#     is_claimed = fields.Boolean(string="is_claimed", default=False)
#
#
# class NonSerialProductReceiveFromCustomerInherit(models.Model):
#     _inherit = "stock.move"
#     _order = 'name desc'
#     nspr_labour_claim_tag = fields.Boolean(string="NSPR Labour Claim", default=False)
#     product_brand = fields.Many2one(related='product_id.brand', string="Product Brand")
#
#     @api.onchange('product_id')
#     def _onchange_product(self):
#         self.product_brand = self.product_id.brand
# #
# #
# # # from dateutil.relativedelta import relativedelta
# # # from odoo import api, fields, models, _
# # # from odoo.tests.common import Form
# # # from odoo.exceptions import ValidationError
# # # from datetime import datetime
# # # import schedule
# # # import schedule
# # # import time
# # #
# # #
# # # class ServiceChargeClaim(models.Model):
# # #     _inherit = 'account.move'
# # #
# # #     claim_flag = fields.Boolean(default=False)
# # #     claim_no = fields.Char(string="Claim No. ", default=lambda self: _('New'))
# # #     claim_date = fields.Datetime(string="Claim Date")
# # #     description = fields.Char(string="Description")
# # #     from_date = fields.Date(string="From Date")
# # #     to_date = fields.Date(string="To Date")
# # #     dept = fields.Many2one('field.service.department', string='Department')
# # #     invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,
# # #                                default=lambda self: self._get_invoice_data(),
# # #                                states={'draft': [('readonly', False)]})
# # #     per_unit_cost=fields.Integer(string="Per Unit Cost")
# # #
# # #     claim_approve = fields.Boolean(compute='_claim_approve', string='approve', default=False)
# # #
# # #
# # #     def _claim_approve(self):
# # #         for rec in self:
# # #             x = self.env['claim.approval.config'].search([('user_branch', '=', rec.branch_id.id)])
# # #             if self.env.user.id in x.user_name.ids:
# # #                 rec.claim_approve = True
# # #             else:
# # #                 rec.claim_approve = False
# # #
# # #
# # #     def _get_invoice_data(self):
# # #         if 'default_claim_flag' in self.env.context.keys() and self.env.context.get('default_claim_flag') == True:
# # #             return fields.Date.today()
# # #
# # #     @api.model
# # #     def create(self, vals):
# # #         res = super(ServiceChargeClaim, self).create(vals)
# # #         if vals.get('name', ('New')) == ('New'):
# # #
# # #             if res.claim_flag == True:
# # #                 val = self.env['ir.sequence'].next_by_code('so.claim') or _('New')
# # #                 res.name = val
# # #
# # #         return res
# # #
# # #     @api.model
# # #     def _move_autocomplete_invoice_lines_create(self, vals_list):
# # #         if 'claim_flag' in vals_list[0].keys():
# # #             new_vals_list = []
# # #             if vals_list[0]['claim_flag'] == True:
# # #                 if vals_list[0].get('invoice_line_ids') != None:
# # #                     for line in vals_list[0].get('line_ids'):
# # #                         for inv_line in vals_list[0].get('invoice_line_ids'):
# # #                             print(line)
# # #                             print(line[2]['product_id'])
# # #                             if inv_line[2]['order_id'] == line[2]['order_id']:
# # #                                 print(inv_line[2]['order_id'])
# # #                                 line[2]['brand'] = inv_line[2]['brand']
# # #                                 line[2]['order_id'] = inv_line[2]['order_id']
# # #                                 line[2]['service_order_date'] = inv_line[2]['service_order_date']
# # #                 # return super(ServiceChargeClaim, self)._move_autocomplete_invoice_lines_create(vals_list)
# # #                 # if not vals_list[0].get('invoice_line_ids'):
# # #                 #     new_vals_list.append(vals_list[0])
# # #
# # #                 if vals_list[0].get('line_ids'):
# # #                     vals_list[0].pop('invoice_line_ids', None)
# # #                     new_vals_list.append(vals_list[0])
# # #                 return new_vals_list
# # #             else:
# # #                 return super(ServiceChargeClaim,self)._move_autocomplete_invoice_lines_create(vals_list)
# # #
# # #
# # #     @api.onchange('dept','partner_id','from_date','to_date')
# # #     def _onchange_dept(self):
# # #         for rec in self:
# # #             department = self.env['claim.management'].search(
# # #                 [('dept', '=', rec.dept.name)])  # query for department and product
# # #
# # #             dept_as_product = self.env['product.product'].search(
# # #                 [('id', '=', department.dept.id)])  # query for  product
# # #             service_orders = self.env['field.service'].search([
# # #
# # #                ('order_date', '>=', self.from_date),
# # #                ('order_date', '<=', self.to_date),
# # #
# # #                ('departments', '=', rec.dept.id),
# # #                ('claim_tag', '=', True)])  # query for  field service
# # #
# # #             self.per_unit_cost = department.unite_price
# # #
# # #             # self.to_date = (fields.Date.today() - relativedelta(
# # #             #     days=+fields.Date.today().day)) + relativedelta(days=+department.claim_date)
# # #             # self.to_date = (fields.Date.today() - relativedelta(
# # #             #     days=+fields.Date.today().day)) + relativedelta(days=+department.claim_date)
# # #             rec.invoice_line_ids = [(5, 0, 0)]
# # #             rec.line_ids = [(5, 0, 0)]
# # #             line = [(5,0,0)]
# # #             line1 = [(5,0,0)]
# # #             x = 0
# # #             for service in service_orders:
# # #                 # self.from_date = (fields.Date.today() - relativedelta(
# # #                 # days=+fields.Date.today().day))
# # #                 # if self.from_date < service.order_date < self.to_date:
# # #                     x = x + department.unite_price
# # #                     line.append((0, 0, {
# # #                         'product_id': service.product_id.id,
# # #                         'brand': service.product_id.brand,
# # #                         'account_id': dept_as_product.property_account_income_id.id,
# # #                         'branch_id': self.env.user.branch_id.id,
# # #                         'price_unit': department.unite_price,
# # #                         'order_id': service.id,
# # #                         'price_subtotal': department.unite_price,
# # #                         'service_order_date': service.order_date,
# # #                         'credit': department.unite_price,
# # #                     }))
# # #             if self.partner_id:
# # #                 line1.append((0, 0, {
# # #                     'account_id': self.partner_id.property_account_receivable_id.id,
# # #                     'branch_id': self.env.user.branch_id.id,
# # #                     'debit': x,
# # #                     'exclude_from_invoice_tab':True,
# # #
# # #                 }))
# # #                 rec.line_ids = line1
# # #             rec.invoice_line_ids = line
# # #
# # #
# # # class ServiceChargeMoveline(models.Model):
# # #     _inherit = 'account.move.line'
# # #     branch_id = fields.Many2one('res.branch', string="Branch", store=True)
# # #     order_id = fields.Many2one('field.service', string="Service Order", store=True)
# # #     brand = fields.Char(string="Brand", store=True)
# # #     service_order_date = fields.Date(string="Service Order Date", store=True)
# # #
# # #     def create(self,vals):
# # #         res= super(ServiceChargeMoveline,self).create(vals)
# # #         for rec in res:
# # #             rec.order_id.claim_tag = False
# # #         return res
