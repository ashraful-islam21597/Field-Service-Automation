from odoo import api, fields, models, _
from datetime import date

list1 = list(range(31))
list2 = list(range(31))
tuple = [(str(list1[i]), str(list2[i])) for i in range(0, len(list1))]

class ClaimaManagement(models.Model):
    _name = 'claim.management'
    _description = 'Claim Management'
    _rec_name = "name"
    name=fields.Char(string='Department/Brand',compute='create_name')
    dept = fields.Many2one('field.service.department', string='Department')
    brand = fields.Many2one('product.brand', string='Brand')
    claim_date1 = fields.Selection(tuple, string='Schedule Day of the Month',required=True,)
    periods = fields.Selection([
        ('1', '1 month'),
        ('2', '2 months'),
        ('3', '3 months'),
        ('6', '6 months')], default='1', string='Period',required=True,)
    unite_price = fields.Integer(string="Unit Price",required=True,)
    type = fields.Selection([('splc', 'Serial Product Labour Claim'),
                             ('nsplc', 'Non Serial Product Labour Claim')],string='Claim Type',required=True,)
    duration = fields.Integer(string="Claim Date")
    claim_date = fields.Integer(string='Schedule Day of the Month')

    property_account_creditor_price_difference = fields.Many2one(
        'account.account', string="Price Difference Account", company_dependent=True,required=True,
        help="This account is used in automated inventory valuation to " \
             "record the price difference between a purchase order and its related vendor bill when validating this vendor bill.")

    property_account_income_id = fields.Many2one('account.account', company_dependent=True,
                                                 string="Income Account", required=True,

                                                 help="Keep this field empty to use the default value from the product category.")
    property_account_expense_id = fields.Many2one('account.account', company_dependent=True,
                                                  string="Expense Account",required=True,

                                                  help="Keep this field empty to use the default value from the product category. If anglo-saxon accounting with automated valuation method is configured, the expense account on the product category will be used.")


    @api.depends('dept','brand')
    def create_name(self):
        for rec in self:
            if rec.type == 'splc':
                rec.name=rec.dept.name
            else:
                rec.name=rec.brand.name

    @api.onchange("claim_date1")
    def _onchange_schedule_time(self):
        self.claim_date = int(self.claim_date1)

    @api.onchange("periods")
    def _onchange_periods(self):
        self.duration = int(self.periods) * 30

    @api.onchange("dept")
    def _onchange_dept_name(self):
        product=self.env['product.product'].search([('name','=',self.dept.name),('detailed_type','=','service'),('product_type','=','sp')])
        self.unite_price = product.list_price
# from odoo import api, fields, models, _
# from datetime import date
#
# list1 = list(range(31))
# list2 = list(range(31))
# tuple = [(str(list1[i]), str(list2[i])) for i in range(0, len(list1))]
#
#
# class ClaimaManagement(models.Model):
#     _name = 'claim.management'
#     _description = 'Claim Management'
#     _rec_name = "dept"
#
#     dept = fields.Many2one('field.service.department', string='Department')
#     brand = fields.Many2one('product.brand', string='Brand')
#     claim_date1 = fields.Selection(tuple, string='Schedule Day of the Month')
#     periods = fields.Selection([
#         ('1', '1 month'),
#         ('2', '2 months'),
#         ('3', '3 months'),
#         ('6', '6 months')], default='1', string='Period')
#     unite_price = fields.Integer(string="Unit Price")
#     type = fields.Selection([('splc', 'Serial Product Labour Claim'),
#                              ('nsplc', 'Non Serial Product Labour Claim')], default='splc', string='Claim Type')
#     duration = fields.Integer(string="Claim Date")
#     claim_date = fields.Integer(string='Schedule Day of the Month')
#
#     @api.onchange("claim_date1")
#     def _onchange_schedule_time(self):
#         self.claim_date = int(self.claim_date1)
#
#     @api.onchange("periods")
#     def _onchange_periods(self):
#         self.duration = int(self.periods) * 30
#
#     # @api.onchange("dept")
#     # def _onchange_dept_name(self):
#     #     product = self.env['product.product'].search([('name', '=', self.dept.name),('detailed_type', '=', 'service'),('product_type','=','sp')])
#     #     print(product)
#     #     self.unite_price = product.list_price
#     #
#     # @api.onchange("dept")
#     # def _onchange_dept_name(self):
#     #     product = self.env['product.product'].search(
#     #         [('name', '=', self.dept.name), ('detailed_type', '=', 'service'), ('product_type', '=', 'sp')])
#     #     print(product)
#     #     self.unite_price = product.list_price
#
#
# # from odoo import api, fields, models, _
# # from datetime import date
# #
# # list1 = list(range(31))
# # list2 = list(range(31))
# # tuple = [(str(list1[i]), str(list2[i])) for i in range(0, len(list1))]
# #
# #
# #
# # class ClaimaManagement(models.Model):
# #     _name = 'claim.management'
# #     _description = 'Claim Management'
# #     _rec_name = "name"
# #     name=fields.Char(string='Department/Brand',compute='create_name')
# #     dept = fields.Many2one('field.service.department', string='Department')
# #     brand = fields.Many2one('product.brand', string='Brand')
# #     claim_date1 = fields.Selection(tuple, string='Schedule Day of the Month')
# #     periods = fields.Selection([
# #         ('1', '1 month'),
# #         ('2', '2 months'),
# #         ('3', '3 months'),
# #         ('6', '6 months')], default='1', string='Period')
# #     unite_price = fields.Integer(string="Unit Price")
# #     type = fields.Selection([('splc', 'Serial Product Labour Claim'),
# #                              ('nsplc', 'Non Serial Product Labour Claim')], default='splc', string='Claim Type')
# #     duration = fields.Integer(string="Claim Date")
# #     claim_date = fields.Integer(string='Schedule Day of the Month')
# #     @api.depends('dept','brand')
# #     def create_name(self):
# #         print(self.type)
# #         if self.type == 'splc':
# #             self.name=self.dept.name
# #         else:
# #             self.name=self.brand.name
# #
# #     @api.onchange("claim_date1")
# #     def _onchange_schedule_time(self):
# #         self.claim_date = int(self.claim_date1)
# #
# #     @api.onchange("periods")
# #     def _onchange_periods(self):
# #         self.duration = int(self.periods) * 30
# #
# #     @api.onchange("dept")
# #     def _onchange_dept_name(self):
# #         product=self.env['product.product'].search([('name','=',self.dept.name),('detailed_type','=','service')])
# #         self.unite_price = product.list_price

