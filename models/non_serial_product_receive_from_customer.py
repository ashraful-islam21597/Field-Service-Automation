from odoo import api, fields, models, _
import datetime
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class NonSerialProductReceiveFromCustomerInherit(models.Model):
    _inherit = "stock.picking"
    _order = 'name desc'

    sale_returned = fields.Boolean(default=False)
    non_serial_custom = fields.Boolean(default=False)
    non_serial_receive = fields.Char(readonly=True, default=lambda self: _('New'), string="Non Serial Receive Sl. No")
    receive_date = fields.Date(default=fields.Datetime.now, string="Receive Date", tracking=True)
    branch_id = fields.Many2one('res.branch', string='Branch', tracking=True)
    currency = fields.Many2one('res.currency', string="Currency")
    delivery_count = fields.Integer(string='Delivery Count', compute="_compute_delivery_count")
    reference_1 = fields.Char(string="Reference")
    remark = fields.Text(string="Remark")
    is_receive = fields.Char(readonly=True, default=lambda self: _('New'), string="Is Receive")
    nspr_claim_tag = fields.Boolean(default=False)
    nsp_status = fields.Selection([
        ('pending', 'Pending'),
        ('nsp_received', 'NSP Received'),
        ('sales_returned', 'Sales Returned'),
        ('return_to_customer', 'Return To Customer'),
        ('delivered', 'Delivered')], default='pending',
        string="NSP Status", tracking=True)

    @api.model
    def create(self, vals):
        res = super(NonSerialProductReceiveFromCustomerInherit, self).create(vals)
        if vals.get('non_serial_receive', _('New')) == _('New'):
            if res.picking_type_id.code == 'incoming' \
                    and res.non_serial_custom == True:
                val = self.env['ir.sequence'].next_by_code('non.serial.product.receive') or _('New')
                res.name = val
        return res

    # def button_validate(self):
    #     # Clean-up the context key at validation to avoid forcing the creation of immediate
    #     # transfers.
    #     if self.non_serial_custom == True:
    #             self.nsp_status = 'nsp_received'
    #     ctx = dict(self.env.context)
    #     ctx.pop('default_immediate_transfer', None)
    #     self = self.with_context(ctx)
    #
    #     # Sanity checks.
    #     pickings_without_moves = self.browse()
    #     pickings_without_quantities = self.browse()
    #     pickings_without_lots = self.browse()
    #     products_without_lots = self.env['product.product']
    #     for picking in self:
    #         if not picking.move_lines and not picking.move_line_ids:
    #             pickings_without_moves |= picking
    #
    #         picking.message_subscribe([self.env.user.partner_id.id])
    #         picking_type = picking.picking_type_id
    #         precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #         no_quantities_done = all(
    #             float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in
    #             picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
    #         no_reserved_quantities = all(
    #             float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for
    #             move_line in picking.move_line_ids)
    #         if no_reserved_quantities and no_quantities_done:
    #             pickings_without_quantities |= picking
    #
    #         if picking_type.use_create_lots or picking_type.use_existing_lots:
    #             lines_to_check = picking.move_line_ids
    #             if not no_quantities_done:
    #                 lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0,
    #                                                                                     precision_rounding=line.product_uom_id.rounding))
    #             for line in lines_to_check:
    #                 product = line.product_id
    #                 if product and product.tracking != 'none':
    #                     if not line.lot_name and not line.lot_id:
    #                         pickings_without_lots |= picking
    #                         products_without_lots |= product
    #
    #     if not self._should_show_transfers():
    #         if pickings_without_moves:
    #             raise UserError(_('Please add some items to move.'))
    #         if pickings_without_quantities:
    #             raise UserError(self._get_without_quantities_error_message())
    #         if pickings_without_lots:
    #             raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(
    #                 products_without_lots.mapped('display_name')))
    #     else:
    #         message = ""
    #         if pickings_without_moves:
    #             message += _('Transfers %s: Please add some items to move.') % ', '.join(
    #                 pickings_without_moves.mapped('name'))
    #         if pickings_without_quantities:
    #             message += _(
    #                 '\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(
    #                 pickings_without_quantities.mapped('name'))
    #         if pickings_without_lots:
    #             message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (
    #             ', '.join(pickings_without_lots.mapped('name')),
    #             ', '.join(products_without_lots.mapped('display_name')))
    #         if message:
    #             raise UserError(message.lstrip())
    #
    #     # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
    #     # moves and/or the context and never call `_action_done`.
    #     if not self.env.context.get('button_validate_picking_ids'):
    #         self = self.with_context(button_validate_picking_ids=self.ids)
    #     res = self._pre_action_done_hook()
    #     if res is not True:
    #         return res
    #
    #     # Call `_action_done`.
    #     if self.env.context.get('picking_ids_not_to_backorder'):
    #         pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
    #         pickings_to_backorder = self - pickings_not_to_backorder
    #     else:
    #         pickings_not_to_backorder = self.env['stock.picking']
    #         pickings_to_backorder = self
    #     pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
    #     pickings_to_backorder.with_context(cancel_backorder=False)._action_done()
    #
    #     if self.user_has_groups('stock.group_reception_report') \
    #             and self.user_has_groups('stock.group_auto_reception_report') \
    #             and self.filtered(lambda p: p.picking_type_id.code != 'outgoing'):
    #         lines = self.move_lines.filtered(lambda
    #                                              m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
    #         if lines:
    #             # don't show reception report if all already assigned/nothing to assign
    #             wh_location_ids = self.env['stock.location']._search(
    #                 [('id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.id),
    #                  ('usage', '!=', 'supplier')])
    #             if self.env['stock.move'].search([
    #                 ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
    #                 ('product_qty', '>', 0),
    #                 ('location_id', 'in', wh_location_ids),
    #                 ('move_orig_ids', '=', False),
    #                 ('picking_id', 'not in', self.ids),
    #                 ('product_id', 'in', lines.product_id.ids)], limit=1):
    #                 action = self.action_view_reception_report()
    #                 action['context'] = {'default_picking_ids': self.ids}
    #                 return action
    #     return True


    @api.depends('state')
    def _compute_delivery_count(self):
        for rec in self:
            delivery_count = self.env['stock.picking'].search_count([('origin', '=', rec.name)])
            rec.delivery_count = delivery_count


    @api.onchange("partner_id")
    def onchange_partner(self):
        if 'default_non_serial_custom' in self.env.context.keys() and self.env.context.get(
                'default_non_serial_custom') == True:
            val = self.env['stock.location'].search(
                [('branch_id', '=', self.branch_id.id),
                 ('is_returnable_damage', '=', True)], limit=1).id
            self.location_dest_id = val
        elif 'default_non_serial_delivery' in self.env.context.keys() and self.env.context.get(
                'default_non_serial_delivery') == True:
            get_warranty_warehouse = self.env['warehouse.mapping'].search(
                [('branch_id', '=', self.branch_id.id),
                 ('stock_type', '=', 'warranty')], limit=1).default_location.id
            self.location_id = get_warranty_warehouse
        else:
            return super().onchange_partner()

    def action_sales_return(self):
        self.sale_returned = True
        return

    def action_non_serial_delivery(self):
        self.ensure_one()
        line = []
        for rec in self:
            non_serial_product_receive_id = self.env['stock.picking'].search(
                [('name', '=', rec.name)])
            user = self.env['res.users'].browse(self._context.get('uid'))
            warehouse_data = self.env['stock.warehouse'].search([
                ('branch_id', '=', rec.branch_id.id),
                ('company_id', '=', user.company_id.id)])
            picking_type = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', warehouse_data.id),
                 ('code', '=', 'outgoing')], limit=1)
            get_warranty_warehouse = self.env['warehouse.mapping'].search(
                [('branch_id', '=', self.branch_id.id),
                 ('stock_type', '=', 'warranty')], limit=1).default_location.id
            line = [(5, 0, 0)]
            for i in rec.move_ids_without_package:
                vals = (0, 0, {
                    'product_id': i.product_id.id,
                    'description_picking': rec.product_id.product_tmpl_id.name,
                    'name': rec.product_id.product_tmpl_id.name,
                    'product_uom': rec.product_id.product_tmpl_id.uom_id.id,
                    'product_uom_qty': i.quantity_done,
                    'picking_type_id': rec.picking_type_id.id,
                    'location_id': get_warranty_warehouse,
                    'location_dest_id': 5,
                    'branch_id': rec.branch_id.id,
                })
                line.append(vals)

        return {
            'name': _('Delivery'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'views': [(self.env.ref('usl_service_erp.view_non_serial_product_delivery_form').id, 'form'),
                      (False, 'list')],
            'type': 'ir.actions.act_window',
            'context': {
                'default_partner_id': non_serial_product_receive_id.partner_id.id,
                'default_picking_type_id': picking_type.id,
                'default_origin': non_serial_product_receive_id.name,
                'default_move_ids_without_package': line,
                'default_non_serial_delivery': True,
            },
        }

    def action_test(self):

        engineers = self.env['nsp.sales.return'].search([('nsp_id', '=', self.id)])
        if engineers:
            engineers = self.env['nsp.sales.return'].search([('nsp_id', '=', self.id)])
            result = self.env["ir.actions.actions"]._for_xml_id('usl_service_erp.action_nsp_sales_return')
            # override the context to get rid of the default filtering on operation type
            result['context'] = {'default_nsp_id': self.id}
            # choose the view_mode accordingly
            if not engineers or len(engineers) > 1:
                result['domain'] = [('id', 'in', engineers.ids)]
            elif len(engineers) == 1:
                res = self.env.ref('usl_service_erp.view_nsp_sales_return_form', False)
                form_view = [(res and res.id or False, 'form')]
                result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if
                                               view != 'form']
                result['res_id'] = engineers.id
            return result
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'nsp.sales.return',
                'view_mode': 'form',
                'view_id': self.env.ref('usl_service_erp.view_nsp_sales_return_form').id,
                'context': {'default_nsp_id': self.id}
            }

    def action_delivery(self):
        self.ensure_one()
        for rec in self:
            get_delivered_non_serial_product_list = self.env['stock.picking'].search([('origin', '=', rec.name)]).ids
            result = self.env["ir.actions.actions"]._for_xml_id('usl_service_erp.action_non_serial_product_delivery')
            if get_delivered_non_serial_product_list:
                result['domain'] = [('id', 'in', get_delivered_non_serial_product_list)]
                return result
            else:
                None

class StockLocationInherit(models.Model):
    _inherit = 'stock.location'

    is_returnable_damage = fields.Boolean(string="Is a Returnable Damage?")





