from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tests.common import Form
from odoo.exceptions import ValidationError
from datetime import datetime

import time



class NspClaim(models.Model):
    _inherit = 'sale.order'
    p_type=fields.Selection([('sp', 'Serial Product'),
                                   ('nsp', 'Non Serial Product')], string='Product Type')
    dept = fields.Many2one('field.service.department', string='Department')


    def _action_confirm(self):
        if self.part_claim == True and self.p_type == 'sp':
            for i in self.order_line:
                x = i.consu_id
                consu = self.env['item.consumption.lines'].search([('id', '=', x.id)])
                consu.spr_claim_tag = True
            self.order_line._action_launch_stock_rule()
        return super(NspClaim, self)._action_confirm()

    def _claim_approve(self):
        for rec in self:
            x = self.env['claim.approval.config'].search([('user_branch', '=', rec.branch_id.id)])
            if self.env.user.id in x.user_name.ids:
                rec.claim_approve = True
            else:
                rec.claim_approve = False


    @api.model
    def create(self, vals):
        res = super(NspClaim, self).create(vals)
        if vals.get('claim_no', ('New')) == ('New'):
            if res.part_claim == True and res.p_type == 'sp':
                val = self.env['ir.sequence'].next_by_code('serial.product.claim') or _('New')
                res.name = val
        return res

    @api.onchange('dept', 'partner_id', 'from_date', 'to_date')
    def _onchange_dept(self):
        if self.dept and self.partner_id and self.from_date and self.to_date:
            for rec in self:
                service_orders = self.env['field.service'].search([
                    ('order_date', '>=', self.from_date),
                    ('order_date', '<=', self.to_date),
                    ('branch_name', '=', self.env.user.branch_id.id),
                    ('departments', '=', rec.dept.id),
                ])
                item_consu=[]
                for j in service_orders:
                    x=self.env['item.consumption'].search([('order_id','=',j.id)])
                    if x.id != False:
                        item_consu.append(x)
                rec.order_line = [(5, 0, 0)]
                rec.sale_order_option_ids = [(5, 0, 0)]
                line = [(5, 0, 0)]
                line1 = [(5, 0, 0)]
                x = 0
                for i in item_consu:
                    for service in i.item_consumption_line_ids:
                        if service.spr_claim_tag == False:
                            x = x + service.part.list_price
                            line.append((0, 0, {
                                'product_id': service.part.id,
                                'product_uom': service.part.product_tmpl_id.uom_id.id,
                                'brand': service.part.brand.id,
                                'branch_id': self.env.user.branch_id.id,
                                'price_unit': service.part.list_price,
                                'name': service.part.product_tmpl_id.name,
                                'consu_id':service.id,
                                'service_order_id': service.item_consumption_id.order_id.id,
                                'price_subtotal': service.part.list_price,
                                'bad_ct':service.bad_ct_serial_no
                            }))
                            if self.partner_id:
                                line1.append((0, 0, {
                                    'product_id': service.part.id,
                                    'price_unit': service.part.list_price,
                                    'name': service.part.product_tmpl_id.uom_id.name,
                                    'uom_id': service.part.product_tmpl_id.uom_id.id,
                                }))
                                rec.sale_order_option_ids = line1
                            rec.order_line = line

    def action_view_invoice(self):
        res=super(NspClaim, self).action_view_invoice()
        if 'default_part_claim' in self.env.context.keys() and self.env.context.get(
                'default_part_claim') == True:
                res['context'].update({
                    'default_part_claim_flag': True,

                })
        return  res






class NspServiceChargeMoveline(models.Model):
    _inherit = 'sale.order.line'
    bad_ct= fields.Char(string="Defective Serial")
    service_order_id = fields.Many2one('field.service', string="Service Order")



# from dateutil.relativedelta import relativedelta
# from odoo import api, fields, models, _
# from odoo.tests.common import Form
# from odoo.exceptions import ValidationError
# from datetime import datetime
#
# import time
#
#
# class NspClaim(models.Model):
#     _inherit = 'sale.order'
#     p_type=fields.Selection([('sp', 'Serial Product'),
#                                    ('nsp', 'Non Serial Product')], string='Product Type')
#     dept = fields.Many2one('field.service.department', string='Department')
#     brand=fields
#
#     def _get_user_branch(self):
#         if 'default_nspr_claim_flag' in self.env.context.keys() and self.env.context.get(
#                 'default_nspr_claim_flag') == True:
#             return self.env.user.branch_id.id
#
#
#     def _action_cancel(self):
#
#         if self.nspr_claim_flag == True:
#             for i in self.order_line:
#                 x = i.nspr_id
#                 nspr = self.env['stock.picking'].search([('id', '=', x.id)])
#                 nspr.nspr_claim_tag = False
#
#
#         documents = None
#         for sale_order in self:
#             if sale_order.state == 'sale' and sale_order.order_line:
#                 sale_order_lines_quantities = {order_line: (order_line.product_uom_qty, 0) for order_line in
#                                                sale_order.order_line}
#                 documents = self.env['stock.picking'].with_context(
#                     include_draft_documents=True)._log_activity_get_documents(sale_order_lines_quantities, 'move_ids',
#                                                                               'UP')
#         self.picking_ids.filtered(lambda p: p.state != 'done').action_cancel()
#         if documents:
#             filtered_documents = {}
#             for (parent, responsible), rendering_context in documents.items():
#                 if parent._name == 'stock.picking':
#                     if parent.state == 'cancel':
#                         continue
#                 filtered_documents[(parent, responsible)] = rendering_context
#             self._log_decrease_ordered_quantity(filtered_documents, cancel=True)
#         return super()._action_cancel()
#
#     def _action_confirm(self):
#         if self.nspr_claim_flag == True and self.p_type == 'sp':
#             for i in self.order_line:
#                 x = i.consu_id
#                 consu = self.env['item.consumption.lines'].search([('id', '=', x.id)])
#                 consu.spr_claim_tag = True
#             self.order_line._action_launch_stock_rule()
#             return super(NspClaim, self)._action_confirm()
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
#         if 'default_nspr_claim_flag ' in self.env.context.keys() and self.env.context.get(
#                 'default_nspr_claim_flag ') == True:
#             return fields.Date.today()
#
#     @api.model
#     def create(self, vals):
#         res = super(NspClaim, self).create(vals)
#         if vals.get('claim_no', ('New')) == ('New'):
#             if res.nspr_claim_flag == True and res.p_type == 'sp':
#                 val = self.env['ir.sequence'].next_by_code('serial.product.claim') or _('New')
#                 res.name = val
#         return res
#
#     @api.onchange('dept', 'partner_id', 'from_date', 'to_date')
#     def _onchange_dept(self):
#         if self.dept and self.partner_id and self.from_date and self.to_date:
#             for rec in self:
#                 user = self.env['res.users'].browse(self._context.get('uid'))
#                 location_id_returnable_damage = self.env['stock.location'].search(
#                     [('branch_id', '=', self.branch_id.id),
#                      ('is_returnable_damage', '=', True)], limit=1)
#                 print(location_id_returnable_damage.location_id,location_id_returnable_damage,user.branch_id.id,user.company_id.id)
#                 warehouse_data = self.env['stock.warehouse'].search([
#                     ('branch_id', '=', user.branch_id.id),
#                     ('company_id', '=', user.company_id.id),
#                     ('lot_stock_id', '=', location_id_returnable_damage.location_id.id)
#
#                 ])
#
#                 rec.warehouse_id = warehouse_data.id
#                 service_orders = self.env['field.service'].search([
#                     ('order_date', '>=', self.from_date),
#                     ('order_date', '<=', self.to_date),
#                     ('branch_name', '=', self.env.user.branch_id.id),
#                     ('departments', '=', rec.dept.id),
#                 ])
#                 item_consu=[]
#                 for j in service_orders:
#                     x=self.env['item.consumption'].search([('order_id','=',j.id)])
#                     if x.id != False:
#                         item_consu.append(x)
#                 rec.order_line = [(5, 0, 0)]
#                 rec.sale_order_option_ids = [(5, 0, 0)]
#                 line = [(5, 0, 0)]
#                 line1 = [(5, 0, 0)]
#                 x = 0
#                 for i in item_consu:
#                     for service in i.item_consumption_line_ids:
#
#                         if service.spr_claim_tag == False:
#                             x = x + service.part.list_price
#
#                             s = self.env['stock.move'].search([
#                                 ('location_dest_id', '=', location_id_returnable_damage.id),
#                                 ('product_id', '=', service.part.id),
#                                 # ('consump_serial', '=', service.bad_ct_serial_no)
#                             ])
#
#                             line.append((0, 0, {
#                                 'product_id': service.part.id,
#                                 'product_uom': service.part.product_tmpl_id.uom_id.id,
#                                 'brand': service.part.brand.id,
#                                 # 'account_id': service.product_id.property_account_income_id.id,
#                                 'branch_id': self.env.user.branch_id.id,
#                                 'price_unit': service.part.list_price,
#                                 'name': service.part.product_tmpl_id.name,
#                                 'consu_id':service.id,
#                                 'service_order_id': service.item_consumption_id.order_id.id,
#                                 'price_subtotal': service.part.list_price,
#
#
#
#                                 #'credit': service.product_id.list_price,
#                             }))
#
#                             if self.partner_id:
#                                 line1.append((0, 0, {
#                                     'product_id': service.part.id,
#                                     'price_unit': service.part.list_price,
#                                     'name': service.part.product_tmpl_id.uom_id.name,
#                                     'uom_id': service.part.product_tmpl_id.uom_id.id,
#
#
#                                 }))
#                                 rec.sale_order_option_ids = line1
#                             rec.order_line = line
#
#
# class NspServiceChargeMoveline(models.Model):
#     _inherit = 'sale.order.line'
#     #model = fields.Many2one('stock.picking', string="Model")
#     service_order_id = fields.Many2one('field.service', string="Service Order")
#
#
#     # @api.model
#     # def create(self, vals):
#     #     res = super(NspServiceChargeMoveline, self).create(vals)
#     #     for rec in res:
#     #         nspr = self.env['stock.picking'].search([('id', '=', rec.nspr_id.id)])
#     #         nspr.nspr_claim_tag = True
#     #     return res
