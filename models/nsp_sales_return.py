from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import ValidationError
from datetime import datetime


class NSP_Sales_Return(models.Model):
    _name = 'nsp.sales.return'
    _description = 'NSP Sales Return'
    _rec_name = "nsp_id"
    # contact = fields.Char(related="order_id.phone", string='Contact No', readonly=True)


    nsp_id = fields.Many2one('stock.picking', readonly=True)
    receive_date = fields.Date(related="nsp_id.receive_date", string="Receive Date", tracking=True)
    branch_id = fields.Many2one(related="nsp_id.branch_id", string='Branch', tracking=True)
    currency = fields.Many2one(related="nsp_id.branch_id", string="Currency")
    delivery_count = fields.Integer(related="nsp_id.delivery_count",string='Delivery Count')
    reference_1 = fields.Char(related="nsp_id.reference_1",string="Reference")
    remark = fields.Text(related="nsp_id.remark",string="Remark")
    nspr_claim_tag = fields.Boolean(related="nsp_id.nspr_claim_tag")
    customer = fields.Many2one(related="nsp_id.partner_id", string='Customer')
    destination_location = fields.Many2one(related="nsp_id.location_dest_id")
    received_date = fields.Datetime(related="nsp_id.scheduled_date", string="Receive Date", tracking=True)
    effective_date = fields.Datetime(related="nsp_id.date_done", string="Receive Date", tracking=True)
    nsp_sales_return_ids = fields.One2many('nsp.sales.return.lines', 'nsp_sales_return_id', string='NSP Sales Return Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit_for_approval', 'Submitted For Approval'),
        ('approved', 'Approved'),
        ('cancel', 'Canceled')], default='draft', string="Status", required=True)

    nsp_approve = fields.Boolean(compute='_nsp_approve', string='approve', default=False)

    def _nsp_approve(self):
        for rec in self:
            x = self.env['nsp.approval.config'].search([('user_branch', '=', rec.branch_id.id)])
            if self.env.user.id in x.user_name.ids:
                rec.nsp_approve = True
            else:
                rec.nsp_approve = False


    def action_submit_for_approval(self):
        self.state = 'submit_for_approval'
        return

    def action_approval(self):
        sales_return = self.env['stock.picking'].search([('id', '=', self.nsp_id.id)])
        sales_return.sale_returned = True
        self.state = 'approved'
        return
    def action_cancel(self):
        self.state = 'cancel'
        return

    def action_draft(self):
        self.state = 'draft'
        return





    @api.onchange('nsp_id')
    def _onchange_nsp_id(self):
        for rec in self:
            service_orders = self.env['stock.picking'].search([
                ('name', '=', self.nsp_id.name),
            ])
            rec.nsp_sales_return_ids = [(5, 0, 0)]
            line = [(5, 0, 0)]
            for i in service_orders:
                for service in i.move_ids_without_package:
                    line.append((0, 0, {
                        'product': service.product_id.id,
                        'demand': service.product_id.product_tmpl_id.uom_id.id,
                        'done': service.quantity_done
                    }))
            rec.nsp_sales_return_ids = line



class NSP_Sales_Return_Lines(models.Model):
    _name = 'nsp.sales.return.lines'
    _description = 'NSP Sales Return Lines'

    nsp_sales_return_id = fields.Many2one('nsp.sales.return')
    product = fields.Many2one('product.product', string='Product')
    demand = fields.Float(string='Demand')
    done = fields.Float(string='Done')


