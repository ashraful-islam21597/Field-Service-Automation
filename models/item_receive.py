from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError


class StockPickingOperation(models.Model):
    _inherit = "stock.picking"
    _order = 'name desc'
    serial = fields.Char(string='Order No', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    service_order_id = fields.Many2many('field.service', 'service_id', string="Service Order", ondelete='cascade')
    to_branch = fields.Many2one('res.branch', string="To Branch", Tracking=True)
    contact_person = fields.Many2one('res.partner', string="Contact Person", Tracking=True)
    custom_operation_receive = fields.Boolean(default=False)
    custom_operation_transfer = fields.Boolean(default=False)
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', readonly=False,
                                      default=lambda self: self._set_operation_type_id(),
                                      states={'draft': [('readonly', False)]})
    received = fields.Boolean(related='service_order_id.receive_customer', string="received status")
    branch_id = fields.Many2one('res.branch', default=lambda self: self.env.user.branch_id)
    dest_type = fields.Selection([('branch', 'Branch'), ('department', 'Department')], string="Destination Type")
    dept = fields.Many2one('field.service.department', string='Department', tracking=True)
    picking_created_user = fields.Many2one('res.users', string='Contact Person', default=lambda self: self.env.user.id)
    receive_approve = fields.Boolean(compute='_transfer_receive_approve', string='approve', default=False)
    transfer_confirmation_approval = fields.Boolean(compute='_transfer_confirmation_approval', string='confirm',
                                                    default=False)
    remarks = fields.Html(string="Reamrks")

    def waiting_for_receive(self):
        return

    def _transfer_confirmation_approval(self):
        for rec in self:
            config_ids = self.env['transfer.confirm.approval.config'].search(
                [('user_branch', '=', rec.branch_id.id), ('user_name', '=', self.env.user.id)])

            if self.env.user.id in config_ids.user_name.ids:
                rec.transfer_confirmation_approval = True
            else:
                rec.transfer_confirmation_approval = False

    def _transfer_receive_approve(self):
        for rec in self:
            user = self.env['res.users'].search([('partner_id', '=', rec.partner_id.id)])
            config_ids = self.env['receive.approval.config'].search(
                [('user_branch', '=', rec.to_branch.id), ('user_name', '=', user.id)])
            if self.env.user.id in config_ids.user_name.ids:
                rec.receive_approve = True
            else:
                rec.receive_approve = False

    @api.onchange('dest_type')
    def _onchange_dest_type(self):
        domain = []
        if self.dest_type == 'branch':
            self.to_branch = False
            get_branch = self.env['res.branch'].sudo().search(
                [('id', '!=', self.env.user.branch_id.id)])
            a = [('id', 'in', get_branch.ids)]
            domain = {'to_branch': a}
        elif self.dest_type == 'department':
            get_branch = self.env['res.branch'].sudo().search([])
            a = [('id', 'in', get_branch.ids)]
            self.to_branch = self.env.user.branch_id.id
            self.dept = self.service_order_id.departments.id
            domain = {'to_branch': a}
        return {'domain': domain}

    def _action_done(self):
        res = super(StockPickingOperation, self)._action_done()
        for rec in self.service_order_id:
            if self.picking_type_id.code == 'internal' and self.custom_operation_transfer == True:
                if self.branch_id != self.to_branch:
                    rec.so_transfer = True
                    rec.current_branch = self.to_branch.id
                    rec.branch_name = self.to_branch.id
                    rec.item_receive_status = "Transfered"
            elif self.picking_type_id.code == 'incoming' and self.custom_operation_receive == True:
                rec.receive_customer = True
                rec.item_receive_branch = self.branch_id.id
                rec.product_receive_date = self.scheduled_date
                rec.item_receive_status = "Received"
        return res

    @api.onchange('service_order_id')
    def onchange_service_order(self):

        user = self.env['res.users'].browse(self._context.get('uid'))
        self.move_ids_without_package = [(6, 0, [])]
        line = [(5, 0, 0)]
        for service in self.service_order_id:
            for rec in self.env['field.service'].search([('order_no', '=', service.display_name)]):
                line.append((0, 0, {
                    'product_id': rec.product_id.id,
                    'description_picking': rec.product_id.product_tmpl_id.name,
                    'name': rec.product_id.product_tmpl_id.name,
                    'order_ref': rec.customer_id.id,
                    'product_uom': rec.product_id.product_tmpl_id.uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'serial_no': rec.imei_no,
                    'branch_id': user.branch_id.id,
                    'order_id': rec.id,
                }))
        self.move_ids_without_package = line

    # ***********changing location_dest_id depends on to_branch************
    @api.onchange("to_branch")
    def onchange_to_branch(self):
        if self.to_branch.id != False:
            warehouse_data = self.env['stock.warehouse'].search([
                ('branch_id', '=', self.to_branch.id)])
            picking_type = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', warehouse_data.id),
                 ('code', '=', 'incoming')])
            self.location_dest_id = picking_type.default_location_dest_id
            if self.to_branch:
                config_ids = self.env['receive.approval.config'].search(
                    [('user_branch', '=', self.to_branch.id)])
                partner_user = [('id', 'in', config_ids.user_name.partner_id.ids)]
                if self.picking_type_id.code == 'internal' and self.custom_operation_transfer == True:
                    self.location_dest_id = picking_type.default_location_dest_id
                    self.partner_id = False
                    return {'domain': {'partner_id': partner_user}}
        else:
            self.location_dest_id = False

    # ************to prevent the changes of  location_dest_id by changing partner_id*********
    @api.onchange("partner_id")
    def onchange_partner(self):
        if self.picking_type_id.code == 'internal' and self.custom_operation_transfer == True:
            user = self.env['res.users'].search([('partner_id', '=', self.partner_id.id)])
            warehouse_data = self.env['stock.warehouse'].search([
                ('branch_id', '=', self.to_branch.id)
            ])
            self.picking_created_user = user.id
            picking_type = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', warehouse_data.id),
                 ('code', '=', 'incoming')], limit=1)
            self.location_dest_id = picking_type.default_location_dest_id

    @api.model
    def create(self, vals):
        res = super(StockPickingOperation, self).create(vals)
        if vals.get('serial', _('New')) == _('New'):
            if res.picking_type_id.code == 'incoming' and res.custom_operation_receive == True:
                val = self.env['ir.sequence'].next_by_code('so.receive') or _('New')
                res.name = val
            elif res.picking_type_id.code == 'internal' and res.custom_operation_transfer == True:
                val = self.env['ir.sequence'].next_by_code('so.transfer') or _('New')
                user = self.env['res.users'].search([('partner_id', '=', res.partner_id.id)])
                res.picking_created_user = user.id
                res.name = val
                config_ids = self.env['transfer.confirm.approval.config'].search(
                    [('user_branch', '=', self.env.user.branch_id.id),
                     ('user_name', '=', self.env.user.id),
                     ('active', '=', True)])
                if config_ids:
                    pass
                else:
                    self.env['transfer.confirm.approval.config'].create(
                        {'user_branch': self.env.user.branch_id.id,
                         'user_name': self.env.user,
                         'active': True})

        # abdur rahman
        monitoring_data = self.env['field.service.monitoring.data'].search(
            [('so_number', '=', self.service_order_id.id)])

        if monitoring_data:
            if self.custom_operation_receive:
                monitoring_data.rbt_no = self.name
                monitoring_data.tdr_by = self.env.user.id
                monitoring_data.to_branch = res.to_branch
                monitoring_data.assign_date = res.create_date
            if self.custom_operation_transfer:
                monitoring_data.rbt_no = self.name
                monitoring_data.tbt_by = self.env.user.id
                monitoring_data.rbr_date = res.create_date

        return res

    def action_transfer_order_receive_operation(self):
        form_id = self.env.ref('usl_service_erp.view_picking_form_field_service_transfer_order_receive').id,
        tree_id = self.env.ref('usl_service_erp.view_picking_tree_field_service_transfer_order_receive').id,
        user = self.env['res.users'].browse(self._context.get('uid'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transfered Orders Receive'),
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('to_branch', '=', user.branch_id.id), ('state', '=', 'assigned')],
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'target': 'current',
        }


class stockmove(models.Model):
    _inherit = 'stock.move'
    order_ref = fields.Many2one('res.partner', string="Receive from")
    order_id = fields.Many2one('field.service', string="Service Order No.")
    serial_no = fields.Char(string="Serial No")
    contact_person = fields.Many2one('res.partner', string="Contact Person")
