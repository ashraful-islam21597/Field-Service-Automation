from odoo import api, fields, models, _
import datetime
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class FieldServiceDelivery(models.Model):
    _inherit = "stock.picking"

    picking_delivery = fields.Boolean(default=False)
    service_ids = fields.Many2many('field.service', 'stock_picking_rel', string='Service Order')
    partner_id = fields.Many2one('res.partner', string='Customer')
    is_create = fields.Boolean(string='Is Create')


    def _action_done(self):
        res = super(FieldServiceDelivery, self)._action_done()

        if 'default_picking_delivery' in self.env.context.keys() and self.env.context.get('default_picking_delivery') == True:
            get_status = self.env['repair.status'].sudo().search(
                [('repair_status', '=', 'Closed/Delivered')])
            for rec in self.service_ids:

                rec.repair_status1 = get_status.id
        return res






    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            return {'domain': {
                'service_ids': [('customer_id', '=', rec.partner_id.id), ('repair_status1', '=', 'Ready To Deliver')]}}

    @api.onchange('service_ids')
    def onchange_service_ids(self):
        user = self.env['res.users'].browse(self._context.get('uid'))
        self.move_ids_without_package = [(6, 0, [])]
        line = [(5, 0, 0)]
        for service in self.service_ids:
            for rec in self.env['field.service'].search([('order_no', '=', service.display_name)]):
                vals = (0, 0, {
                    'product_id': rec.product_id.id,
                    'so_reference': rec.ids[0],
                    'description_picking': rec.product_id.product_tmpl_id.name,
                    'name': rec.product_id.product_tmpl_id.name,
                    'product_uom': rec.product_id.product_tmpl_id.uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'branch_id': user.branch_id.id,
                })
                line.append(vals)
        self.move_ids_without_package = line

