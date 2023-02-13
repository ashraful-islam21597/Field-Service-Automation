from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    so_reference = fields.Many2one('field.service', string='Service Order')

    def _set_domain(self):
        get_approved_so = self.env['field.service'].sudo().search([('state', '=', 'approval')])
        get_domain_so = self.env['stock.picking'].sudo().search([('state', '!=', 'draft')])
        get_final_so = get_approved_so - get_domain_so.reference
        return [('id', 'in', get_final_so.ids)]

    # @api.onchange('so_reference')
    # def onchange_reference(self):
    #     self.move_ids_without_package = [(5, 0, 0)]
    #     val_list = []
    #     for rec in self.env['field.service'].sudo().search([('order_no', '=', self.so_reference.display_name)]):
    #         vals = (0, 0, {
    #             'product_id': rec.product_id.id,
    #             'description_picking': rec.product_id.product_tmpl_id.name,
    #             'name': rec.product_id.product_tmpl_id.name,
    #             'product_uom': rec.product_id.product_tmpl_id.uom_id.id,
    #             'location_id': self.location_id.id,
    #             'location_dest_id': self.location_dest_id.id,
    #
    #         })
    #         val_list.append(vals)
    #     self.move_ids_without_package = val_list
