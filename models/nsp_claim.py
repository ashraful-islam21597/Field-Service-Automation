from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tests.common import Form
from odoo.exceptions import ValidationError
from datetime import datetime

import time


class NspClaim(models.Model):
    _inherit = 'sale.order'

    part_claim = fields.Boolean(default=False)
    claim_no = fields.Char(string="Claim No. ", default=lambda self: _('New'))
    claim_date = fields.Datetime(string="Claim Date", default=datetime.today())
    description = fields.Char(string="Description")
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    branch_id = fields.Many2one('res.branch', string='Branch', default=lambda self: self._get_user_branch())
    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,
                               default=lambda self: self._get_invoice_data(),
                               states={'draft': [('readonly', False)]})
    default_location_id = fields.Many2one('stock.location', default=lambda self: self._get_location_id(),
                                          string="Source Location")
    nspr_claim_approve = fields.Boolean(compute='_claim_approve', string='approve', default=False)

    def _get_user_branch(self):
        if 'default_part_claim' in self.env.context.keys() and self.env.context.get(
                'default_part_claim') == True:
            return self.env.user.branch_id.id

    def _get_location_id(self):
        location_id = self.env['stock.location'].search([('branch_id', '=', self.env.user.branch_id.id),
                                                         ('is_returnable_damage', '=', True)
                                                         ])
        return location_id.id

    def _action_cancel(self):
        if self.part_claim == True:
            for i in self.order_line:
                x = i.nspr_id
                nspr = self.env['stock.picking'].search([('id', '=', x.id)])
                nspr.nspr_claim_tag = False

        documents = None
        for sale_order in self:
            if sale_order.state == 'sale' and sale_order.order_line:
                sale_order_lines_quantities = {order_line: (order_line.product_uom_qty, 0) for order_line in
                                               sale_order.order_line}
                documents = self.env['stock.picking'].with_context(
                    include_draft_documents=True)._log_activity_get_documents(sale_order_lines_quantities, 'move_ids',
                                                                              'UP')
        self.picking_ids.filtered(lambda p: p.state != 'done').action_cancel()
        if documents:
            filtered_documents = {}
            for (parent, responsible), rendering_context in documents.items():
                if parent._name == 'stock.picking':
                    if parent.state == 'cancel':
                        continue
                filtered_documents[(parent, responsible)] = rendering_context
            self._log_decrease_ordered_quantity(filtered_documents, cancel=True)
        return super()._action_cancel()

    def _action_confirm(self):
        if self.part_claim == True and self.p_type == 'nsp':
            for i in self.order_line:
                x = i.nspr_id
                nspr = self.env['stock.picking'].search([('id', '=', x.id)])
                nspr.nspr_claim_tag = True
            self.order_line._action_launch_stock_rule()
        return super(NspClaim, self)._action_confirm()

    def _claim_approve(self):
        for rec in self:
            x = self.env['claim.approval.config'].search([('user_branch', '=', rec.branch_id.id)])
            if self.env.user.id in x.user_name.ids:
                rec.claim_approve = True
            else:
                rec.claim_approve = False

    def _get_invoice_data(self):
        if 'default_part_claim ' in self.env.context.keys() and self.env.context.get(
                'default_part_claim ') == True:
            return fields.Date.today()

    @api.model
    def create(self, vals):
        res = super(NspClaim, self).create(vals)
        if vals.get('claim_no', ('New')) == ('New'):
            if res.part_claim == True and res.p_type == 'nsp':
                val = self.env['ir.sequence'].next_by_code('non.serial.product.claim') or _('New')
                res.name = val
        return res

    @api.onchange('branch_id', 'partner_id', 'from_date', 'to_date')
    def _onchange_branch(self):
        if self.branch_id and self.partner_id and self.from_date and self.to_date:
            for rec in self:
                service_orders = self.env['stock.picking'].search([
                    ('scheduled_date', '>=', self.from_date),
                    ('scheduled_date', '<=', self.to_date),
                    ('name', 'ilike', 'NSPR'),
                    ('branch_id', '=', self.env.user.branch_id.id),
                    ('nspr_claim_tag', '=', False),
                    ('state', '=', 'done')
                ])
                rec.order_line = [(5, 0, 0)]
                rec.sale_order_option_ids = [(5, 0, 0)]
                line = [(5, 0, 0)]
                line1 = [(5, 0, 0)]
                x = 0
                for i in service_orders:
                    for service in i.move_ids_without_package:
                        x = x + service.product_id.list_price
                        line.append((0, 0, {
                            'product_id': service.product_id.id,
                            'product_uom': service.product_id.product_tmpl_id.uom_id.id,
                            'branch_id': self.env.user.branch_id.id,
                            'price_unit': service.product_id.list_price,
                            'name': i.name,
                            'nspr_id': i.id,
                            'price_subtotal': service.product_id.list_price,
                        }))

                        if self.partner_id:
                            line1.append((0, 0, {
                                'product_id': service.product_id.id,
                                'price_unit': service.product_id.list_price,
                                'name': i.name,
                                'uom_id': service.product_id.product_tmpl_id.uom_id.id,
                            }))
                            rec.sale_order_option_ids = line1
                        rec.order_line = line


class NspServiceChargeMoveline(models.Model):
    _inherit = 'sale.order.line'
    branch_id = fields.Many2one('res.branch', string="Branch", store=True)
    nspr_id = fields.Many2one('stock.picking', string="Service Order")
    consu_id = fields.Many2one('item.consumption.lines', string="Spare Parts From Consumption")
    brand = fields.Many2one('field.service.department', string="Brand", store=True)
    service_order_date = fields.Date(string="Service Order Date", store=True)
    nspr_name = fields.Char(string="Non Serial Product Label")
