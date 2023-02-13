from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ItemRequisitionInherit(models.Model):
    _inherit = 'stock.picking'
    _order = 'name DESC'

    picking_user = fields.Boolean(default=False)
    requisition_no = fields.Char(string='Requisition NO', required=True, copy=False, readonly=True,
                                 default=lambda self: _('New'))
    branch_id = fields.Many2one('res.branch', string='Branch', tracking=True)
    reference = fields.Many2many('field.service', string='Service Order', domain="[('id','in', defaul_reference_id)]")
    defaul_reference_id = fields.Many2many('field.service', compute="_get_default_reference")
    warehouse_map = fields.Many2one('warehouse.mapping', string='Warehouse Mapping')
    iv_approve = fields.Boolean(compute='_iv_approve', string='approve', default=False)
    # item_type = fields.Selection(
    #     [('warranty', 'Warranty'),
    #      ('non_warranty', 'Non Warranty')],
    #     string="Stock type")
    # currency = fields.Many2one('res.currency', string='Currency')
    # remark = fields.Text(string='Remark')
    # location_dest_id = fields.Many2one(
    #     'stock.location', "Destination Location",
    #     default=lambda self: self._set_destination_warehouse(),
    #     check_company=True, readonly=True, required=True,
    #     states={'draft': [('readonly', False)]})
    # location_id = fields.Many2one(
    #     'stock.location', "Source Location",
    #     default=lambda self: self._get_default_location_id(),
    #     check_company=True, readonly=True, required=True,
    #     states={'draft': [('readonly', False)]}
    # )

    # show_submit_for_approval = fields.Boolean(
    #     compute='_compute_show_submit_for_approval',
    #     help='Technical field used to compute whether the button "Request For Approve" should be displayed.')

    # state = fields.Selection(selection_add=[
    #     ('submitted_for_approval', 'Submitted For Approval'),
    #     ('approved', 'Approved'),
    #     ('waiting',)
    # ])
    def _iv_approve(self):
        for rec in self:
            x = self.env['iv.approval.config'].search([('user_branch', '=', rec.branch_id.id)])
            if self.env.user.id in x.user_name.ids:
                if self.env.user.department_id.id == rec.reference.departments.id:
                    rec.iv_approve = True
                else:
                    rec.iv_approve = False
            else:
                rec.iv_approve = False

    # picking_type_id = fields.Many2one(
    #     'stock.picking.type', 'Operation Type',
    #     required=True, readonly=True,
    #     default=lambda self: self._set_operation_type_id(),
    #     states={'draft': [('readonly', False)]})

    # partner_id = fields.Many2one('res.partner', default=lambda self: self._get_default_user())

    # def _get_default_partner(self):
    #     if 'default_picking_user' in self.env.context.keys() and self.env.context.get('default_picking_user') == True:
    #         print('Item Requisition', self.env.user.partner_id)
    #         return self.env.user.partner_id
    #     else:
    #         None

    @api.depends('state')
    def _get_default_reference(self):
        get_approved_so = self.env['field.service'].sudo().search([('state', '=', 'approval')])
        get_domain_so = self.env['stock.picking'].sudo().search([('state', '!=', 'draft')])
        get_final_so = get_approved_so - get_domain_so.reference
        self.defaul_reference_id = get_final_so.ids


    @api.model
    def create(self, vals):
        res = super(ItemRequisitionInherit, self).create(vals)
        if vals.get('requisition_no', _('New')) == _('New'):
            if res.picking_type_id.code == 'internal' \
                    and res.picking_user == True:
                val = self.env['ir.sequence'].next_by_code('item.requisition') or _('New')
                res.name = val
        return res

    @api.onchange('reference')
    def onchange_reference(self):
        for rec in self:
            rec.move_ids_without_package = [(6, 0, [])]
            line = [(5, 0, 0)]
            for so in rec.reference:
                dr = self.env['diagnosis.repair'].search([('order_id', '=', so.ids[0])])
                for i in dr.diagnosis_repair_lines_ids:
                    line.append((0, 0, {
                        'product_id': i.part.id,
                        'so_reference': so.ids[0],
                        'description_picking': i.part.product_tmpl_id.name,
                        'name': i.part.product_tmpl_id.name,
                        'product_uom': i.part.product_tmpl_id.uom_id.id,
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                    }))
                rec.move_ids_without_package = line

    def write(self, vals):
        res = super(ItemRequisitionInherit, self).write(vals)
        return res

    # @api.onchange('picking_type_id')
    # def _onchange_picking_type(self):
    #     super(ItemRequisitionInherit, self)._onchange_picking_type()
    #     if self.picking_user == True:
    #         self.location_id = None
