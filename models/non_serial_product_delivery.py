from odoo import api, fields, models, _
import datetime
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class NonSerialProductDeliveryInherit(models.Model):
    _inherit = "stock.picking"
    _order = 'name desc'

    non_serial_delivery = fields.Boolean(default=False)
    delivery_sl = fields.Char(readonly=True, default=lambda self: _('New'), string="Delivery Serial No.")
    receive_date = fields.Date(default=fields.Datetime.now, string="Receive Date", tracking=True)
    branch_id = fields.Many2one('res.branch', string='Branch', tracking=True)
    currency = fields.Many2one('res.currency', string="Currency")
    delivery_count = fields.Integer(string='Delivery Count')
    remark = fields.Text(string="Remark")

    @api.model
    def create(self, values):
        if 'move_ids_without_package' in values.keys():
            for val in values['move_ids_without_package']:
                val[2]['location_dest_id'] = values['location_dest_id'] if values['location_dest_id'] else None
                val[2]['location_id'] = values['location_id'] if values['location_id'] else None
        res = super(NonSerialProductDeliveryInherit, self).create(values)
        if values.get('delivery_sl', _('New')) == _('New'):
            if res.picking_type_id.code == 'outgoing' \
                    and res.non_serial_delivery == True:
                val = self.env['ir.sequence'].next_by_code('non.serial.product.delivery') or _('New')
                res.name = val
        return res

    class StockBackorderConfirmationInherit(models.TransientModel):
        _inherit = 'stock.backorder.confirmation'

        def process(self):
            pickings_to_do = self.env['stock.picking']
            pickings_not_to_do = self.env['stock.picking']
            for line in self.backorder_confirmation_line_ids:
                if "default_move_ids_without_package" in self._context.keys():
                    ctx = dict(self.env.context)
                    ctx.pop('default_move_ids_without_package', None)
                    self = self.with_context(ctx)

                if line.to_backorder is True:
                    pickings_to_do |= line.picking_id
                else:
                    pickings_not_to_do |= line.picking_id

            for pick_id in pickings_not_to_do:
                moves_to_log = {}
                for move in pick_id.move_lines:
                    if float_compare(move.product_uom_qty,
                                     move.quantity_done,
                                     precision_rounding=move.product_uom.rounding) > 0:
                        moves_to_log[move] = (move.quantity_done, move.product_uom_qty)
                pick_id._log_less_quantities_than_expected(moves_to_log)

            pickings_to_validate = self.env.context.get('button_validate_picking_ids')
            if pickings_to_validate:
                pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate).with_context(
                    skip_backorder=True)
                if pickings_not_to_do:
                    pickings_to_validate = pickings_to_validate.with_context(
                        picking_ids_not_to_backorder=pickings_not_to_do.ids)
                return pickings_to_validate.button_validate()
            return True
