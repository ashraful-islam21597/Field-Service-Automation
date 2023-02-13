from odoo import api, fields, models, _
from datetime import date


class ItemReceive(models.Model):
    _name="order.item.receive"
    _description = 'Service Order Item Receive'


    receive_serial = fields.Char(string="Receive Serial no")


    _rec_name = 'receive_serial'

    receive_serial = fields.Char(string="Receive Serial no")

    delivery_no = fields.Char(string='Delivery No')
    item_receive_date = fields.Date(string="item Receive Date",default=fields.Date.context_today, tracking=True)
    # remarks = fields.Char(string="Remarks")
    receive_order_id = fields.Many2one('field.service', string="Service Order no")
    branch = fields.Many2one('res.branch', related="receive_order_id.branch_name", string='Branch')
    order_receive_ids = fields.One2many('order.receive.lines', 'receive_id',
                                         string="Order receive Details")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('item_received', 'Item Received'),
        ('approved', 'Approved'),
        ('cancelled', 'cancelled')], default="draft", string="Status", required=True, tracking=True)
    is_received= fields.Boolean(string='Is REceived From Branch')

    def action_receive(self):

        for rec in self:
            if rec.state == 'draft':
                self.stock_quant_query_after_recieve_item(self.order_receive_ids)
                rec.state = "item_received"

    @api.model
    def create(self, vals):
        vals['receive_serial'] = self.env['ir.sequence'].next_by_code('order.item.receive')

        return super().create(vals)


    def stock_quant_query_after_recieve_item(self,data):
        for x in data:
            user = self.env['res.users'].browse(self._context.get('uid'))
            warehouse_data = self.env['stock.warehouse'].search([
                ('branch_id', '=', x.order_item_id.branch_name.id),
                ('company_id', '=', user.company_id.id),

            ])

            stock_location_data = self.env['stock.location'].search([
                ('location_id', '=', warehouse_data.code),
                ('name', '=', 'Stock'),
                ('branch_id', '=', x.order_item_id.branch_name.id),
                ('company_id', '=', user.company_id.id),
                ('warehouse_id', '=', warehouse_data.id),
            ])

            t = x.order_item_id.product_id
            stock_quant_data = self.env['stock.quant'].search([
                ('location_id', '=', stock_location_data.id),
                ('company_id', '=', user.company_id.id),
                ('product_id', '=', t.id),

            ])

            stock_quant_data.quantity = stock_quant_data.quantity + 1
            #stock_quant_data.reserved_quantity = stock_quant_data.reserved_quantity + 1






    def stock_quant_query_after_recieve_item(self):
        user = self.env['res.users'].browse(self._context.get('uid'))

        warehouse_data = self.env['stock.warehouse'].search([
            ('branch_id', '=', self.branch.id),
            ('company_id', '=', user.company_id.id),

        ])



        stock_location_data = self.env['stock.location'].search([
            ('location_id', '=', warehouse_data.code),
            ('name','=','Stock'),
            ('branch_id', '=', self.branch.id),
            ('company_id', '=', user.company_id.id),
            ('warehouse_id', '=', warehouse_data.id),
        ])

        stock_quant_data = self.env['stock.quant'].search([
            ('location_id', '=',stock_location_data.id),
            ('company_id', '=', user.company_id.id),
            ('product_id', '=', self.receive_order_item_id.product_id.id),

        ])

        return stock_quant_data



class service_order_receive_lines(models.Model):
    _name = 'order.receive.lines'
    _description = 'Service Order receive Lines'

    item = fields.Char(string='Item')
    receive_date = fields.Date(string="receive Date")
    model = fields.Char(string="Model")
    quantity = fields.Integer(string="Quantitay")
    receive_id = fields.Many2one('order.item.receive', string="Service Order receive")
    order_item_id = fields.Many2one('field.service', string="Service Order item no")

    serial_no = fields.Char(string="Serial No")

    @api.onchange('order_item_id')
    def onchange_order_receive(self):

        self.serial_no = self.order_item_id.imei_no.serial_no

        def stock_quant_query_after_recieve_item(self):
            user = self.env['res.users'].browse(self._context.get('uid'))

            warehouse_data = self.env['stock.warehouse'].search([
                ('branch_id', '=', self.branch.id),
                ('company_id', '=', user.company_id.id),

            ])
            stock_location_data = self.env['stock.location'].search([
                ('branch_id', '=', self.branch.id),
                ('company_id', '=', user.company_id.id),
                ('warehouse_id', '=', warehouse_data.id),
            ])

            stock_quant_data = self.env['stock.quant'].search([
                ('location_id', '=', stock_location_data.id),
                ('company_id', '=', user.company_id.id),
                ('product_id', '=', self.order_id.product_id.id),

            ])
            # print(stock_quant_data.quantity, stock_quant_data.reserved_quantity, stock_quant_data.product_id.name)

            return stock_quant_data