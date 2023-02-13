from odoo import api, fields, models, _
import datetime
from odoo.exceptions import ValidationError


class AdvanceItemRequisitionInherit(models.Model):
    _inherit = "stock.picking"
    _order = 'name desc'

    picking_custom = fields.Boolean(default=False)
    partner_id = fields.Many2one('res.partner', default=lambda self: self._get_default_partner())
    requisition_no_1 = fields.Char(readonly=True,
                                   default=lambda self: _('New'), string="Requisition No")
    requisition_date = fields.Date(default=fields.Datetime.now, string="Requisition Date", tracking=True)
    item_type = fields.Selection(
        [('warranty', 'Warranty'),
         ('non_warranty', 'Non Warranty')],
        string="Stock type")
    branch_id = fields.Many2one('res.branch', string='Branch', tracking=True)
    currency = fields.Many2one('res.currency', string="Currency")
    remark = fields.Text(string="Remark")

    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True, readonly=True,
        default=lambda self: self._set_operation_type_id(),
        states={'draft': [('readonly', False)]}
    )
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self._get_default_location_id(),
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)]}
    )
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self._set_destination_warehouse(),
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)]}
    )
    show_submit_for_approval = fields.Boolean(
        compute='_compute_show_submit_for_approval',
        help='Technical field used to compute whether the button "Request For Approve" should be displayed.')

    state = fields.Selection(selection_add=[
        ('submitted_for_approval', 'Submitted For Approval'),
        ('approved', 'Approved'),
        ('waiting',)
    ])

    @api.model
    def create(self, vals):
        res = super(AdvanceItemRequisitionInherit, self).create(vals)
        if vals.get('requisition_no_1', ('New')) == ('New'):
            if res.picking_type_id.code == 'internal' \
                    and res.picking_custom == True:
                val = self.env['ir.sequence'].next_by_code('advance.item.requisition') or _('New')
                res.name = val
        return res

    def _get_default_partner(self):
        if 'default_picking_custom' in self.env.context.keys() and self.env.context.get(
                'default_picking_custom') == True:
            return self.env.user.partner_id
        elif 'default_picking_user' in self.env.context.keys() and self.env.context.get(
                'default_picking_user') == True:
            return self.env.user.partner_id
        elif 'default_item_return_custom' in self.env.context.keys() and self.env.context.get(
                'default_item_return_custom') == True:
            return self.env.user.partner_id
        elif 'default_non_serial_custom' in self.env.context.keys() and self.env.context.get(
                'default_non_serial_custom') == True:
            return None
        else:
            None

    @api.onchange('branch_id', 'item_type')
    def onchange_branch_id(self):
        if 'default_picking_custom' in self.env.context.keys() and self.env.context.get(
                'default_picking_custom') == True:
            for rec in self:
                src_location = self.env['warehouse.mapping'].search(
                    [('branch_id', '=', rec.branch_id.id), ('stock_type', '=', rec.item_type)]).allowed_location.ids
                return {'domain': {
                    'location_id': [('id', 'in', src_location), ('id', 'not in', [self.location_dest_id.id])]}}
        elif 'default_picking_user' in self.env.context.keys() and self.env.context.get(
                'default_picking_user') == True:
            for rec in self:
                src_location = self.env['warehouse.mapping'].search(
                    [('branch_id', '=', rec.branch_id.id), ('stock_type', '=', rec.item_type)]).allowed_location.ids
                return {'domain': {
                    'location_id': [('id', 'in', src_location), ('id', 'not in', [self.location_dest_id.id])]}}
        elif 'default_item_return_custom' in self.env.context.keys() and self.env.context.get(
                'default_item_return_custom') == True:
            for rec in self:
                src_location = self.env['warehouse.mapping'].search(
                    [('branch_id', '=', rec.branch_id.id), ('stock_type', '=', rec.item_type)]).allowed_location.ids
                return {'domain': {
                    'location_dest_id': [('id', 'in', src_location), ('id', 'not in', [self.location_id.id])]}}
        elif 'default_non_serial_custom' in self.env.context.keys() and self.env.context.get(
                'default_non_serial_custom') == True:
            for rec in self:
                val = self.env['stock.location'].search([('branch_id', '=', rec.branch_id.id), ('is_returnable_damage', '=', 'true')], limit=1)
                self.location_dest_id = val
        else:
            None

    def _get_default_location_id(self):
        if 'default_picking_custom' in self.env.context.keys() and self.env.context.get(
                'default_picking_custom') == True:
            None
        elif 'default_picking_user' in self.env.context.keys() and self.env.context.get(
                'default_picking_user') == True:
            None
        elif 'default_item_return_custom' in self.env.context.keys() and self.env.context.get(
                    'default_item_return_custom') == True:
            logged_user_warehouse = self.env.user.context_default_warehouse_id.lot_stock_id.id
            self.location_id = logged_user_warehouse
        elif 'default_picking_delivery' in self.env.context.keys() and self.env.context.get(
                'default_picking_delivery') == True:
            logged_user_warehouse = self.env.user.context_default_warehouse_id.lot_stock_id.id
            self.location_id = logged_user_warehouse
        elif 'default_custom_operation_receive' in self.env.context.keys() and self.env.context.get(
                'default_custom_operation_receive') == True:
            self.location_id = 4
        else:
            self.location_id = self.env['stock.picking.type'].search(
                [('id', '=', self.picking_type_id.id)]).default_location_src_id

    def _set_destination_warehouse(self):
        if 'default_picking_custom' in self.env.context.keys() and self.env.context.get(
                'default_picking_custom') == True:
            logged_user_warehouse = self.env.user.context_default_warehouse_id.lot_stock_id.id
            self.location_dest_id = logged_user_warehouse
        elif 'default_picking_user' in self.env.context.keys() and self.env.context.get(
                    'default_picking_user') == True:
            logged_user_warehouse = self.env.user.property_warehouse_id.lot_stock_id
            self.location_dest_id = logged_user_warehouse
        elif 'default_non_serial_custom' in self.env.context.keys() and self.env.context.get(
                'default_non_serial_custom') == True:
            for rec in self:
                val = self.env['stock.location'].search(
                    [('branch_id', '=', rec.branch_id.id), ('is_returnable_damage', '=', 'true')], limit=1)
                self.location_dest_id = val
        elif 'default_item_return_custom' in self.env.context.keys() and self.env.context.get(
                'default_item_return_custom') == True:
            None
        elif 'default_custom_operation_receive' in self.env.context.keys() and self.env.context.get(
                'default_custom_operation_receive') == True:
            return self.picking_type_id.default_location_dest_id.id
        else:
            self.location_dest_id = self.env['stock.picking.type'].search(
                [('id', '=', self.picking_type_id.id)]).default_location_dest_id

    def _set_operation_type_id(self):
        if 'default_picking_custom' in self.env.context.keys() and self.env.context.get(
                'default_picking_custom') == True:
            return self.env['stock.picking.type'].search(
                [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
                 ('code', '=', 'internal')]).id
        elif 'default_picking_user' in self.env.context.keys() and self.env.context.get(
                'default_picking_user') == True:
            return self.env['stock.picking.type'].search(
                [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
                 ('code', '=', 'internal')]).id
        elif 'default_item_return_custom' in self.env.context.keys() and self.env.context.get(
                'default_item_return_custom') == True:
            return self.env['stock.picking.type'].search(
                [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
                 ('code', '=', 'internal')]).id
        elif 'default_picking_delivery' in self.env.context.keys() and self.env.context.get(
                'default_picking_delivery') == True:
            return self.env['stock.picking.type'].search(
                [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
                 ('code', '=', 'outgoing')]).id
        elif 'default_custom_operation_transfer' in self.env.context.keys() and self.env.context.get(
                'default_custom_operation_transfer') == True:
            return self.env['stock.picking.type'].search(
                [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
                 ('code', '=', 'internal')], limit=1).id
        elif 'default_custom_operation_receive' in self.env.context.keys() and self.env.context.get(
                'default_custom_operation_receive') == True:
            return self.env['stock.picking.type'].search(
                [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
                 ('code', '=', 'incoming')], limit=1).id
        elif 'default_non_serial_custom' in self.env.context.keys() and self.env.context.get(
                'default_non_serial_custom') == True:
            return self.env['stock.picking.type'].search(
                [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
                 ('code', '=', 'incoming')], limit=1).id
        else:
            None

    @api.depends('state', 'move_lines')
    def _compute_show_submit_for_approval(self):
        for picking in self:
            if not picking.move_lines and not picking.package_level_ids:
                picking.show_submit_for_approval = False
            elif not picking.immediate_transfer and picking.state == 'draft':
                picking.show_submit_for_approval = True
            elif picking.state != 'draft' or not picking.id:
                picking.show_submit_for_approval = False
            else:
                picking.show_submit_for_approval = True

    def action_submit_for_approval(self):
        for rec in self:
            rec.state = 'submitted_for_approval'

    def action_approved(self):
        for rec in self:
            rec.state = 'approved'

    @api.onchange('item_type')
    def _onchange_item_type(self):
        if 'default_picking_custom' in self.env.context.keys() and self.env.context.get(
                'default_picking_custom') == True:
            self.location_id = None
            dest_location = self.env['warehouse.mapping'].search(
                [('branch_id', '=', self.branch_id.id), ('stock_type', '=', self.item_type)]).is_engineer_warehouse.id
            self.location_dest_id = dest_location
        elif 'default_picking_user' in self.env.context.keys() and self.env.context.get(
                'default_picking_user') == True:
            self.location_id = None
            dest_location = self.env['warehouse.mapping'].search(
                [('branch_id', '=', self.branch_id.id), ('stock_type', '=', self.item_type)]).is_engineer_warehouse.id
            self.location_dest_id = dest_location

