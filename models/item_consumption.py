from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ItemConsumption(models.Model):
    _name = 'item.consumption'
    _description = 'Item Consumption'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ref'

    ref = fields.Char(readonly=True, default=lambda self: _('New'), string="Item Consumption")
    order_id = fields.Many2one('field.service', string="Service Order", default=lambda self: self.id, readonly=True)
    imei_no = fields.Char(string='IMEI/Serial No', readonly=False)
    order_date = fields.Datetime(string="Order Date", readonly=False)
    branch_id = fields.Many2one("res.branch", readonly=True)
    customer_id = fields.Char(string="Customer", readonly=True)
    current_branch = fields.Char(string="Current Branch", tracking=True, readonly=True)
    departments = fields.Char(string="Department", readonly=False)
    item_consumption_line_ids = fields.One2many('item.consumption.lines', 'item_consumption_id')
    diagnosis_repair_ids = fields.Many2one('diagnosis.repair')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')],
        default='draft', string="Status")
    repair_status1 = fields.Char(string='Repair Status', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('ref', ('New')) == ('New'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('item.consumption') \
                          or _('New')
        res = super(ItemConsumption, self).create(vals)
        return res

    def action_confirm(self):
        for rec in self:
            res = self.env['diagnosis.repair'].search([('order_id', '=', rec.order_id.id)])
            for line in rec.item_consumption_line_ids:
                if line.consumption_status != 'used' and line.consumption_status != 'unused':
                    location_id = rec.env.user.context_default_warehouse_id.lot_stock_id.id
                    product_id = line.part.id
                    lot_id = line.good_ct_serial_no.id
                    stock_quant_data = self.env['stock.quant'].search([
                        ('location_id', '=', location_id),
                        ('product_id', '=', product_id),
                        ('lot_id', '=', lot_id)
                    ])
                    stock_quant_data.reserved_quantity += line.qty
                    line.consumption_status = 'used'
                    # Parts storing on Returnable Damage Stock with lot
                    location_id_returnable_damage = self.env['stock.location'].search(
                        [('branch_id', '=', self.branch_id.id),
                         ('is_returnable_damage', '=', True)], limit=1).id
                    picking_type = self.env['stock.picking.type'].search(
                        [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
                         ('code', '=', 'internal')]).id
                    available_product_lot = self.env['stock.production.lot'].search([
                        ('product_id', '=', product_id),
                        ('product_uom_id', '=', line.part.product_tmpl_id.uom_id.id),
                        ('name', '=', line.bad_ct_serial_no),
                        ('company_id', '=', self.env.user.company_id.id)])
                    if available_product_lot:
                        available_bad_product = self.env['stock.quant'].search([
                            ('location_id', 'not in', [4, 5]),
                            ('product_id', '=', product_id),
                            ('lot_id', '=', available_product_lot.id)
                        ])
                        if available_bad_product:
                            raise ValidationError(_("Available Same Lot"))
                        else:
                            stock_quant_data_bad_ct_create = self.env['stock.quant'].create({
                                'location_id': location_id_returnable_damage,
                                'product_id': product_id,
                                'lot_id': available_product_lot.id,
                                'quantity': line.qty,
                            })
                            st_move = self.env['stock.move'].create({
                                'company_id': self.env.user.company_id.id,
                                'location_id': 5,
                                'location_dest_id': location_id_returnable_damage,
                                'product_id': product_id,
                                'product_uom_qty': line.qty,
                                'picking_type_id': picking_type,
                                'name': line.part.name,
                                'product_uom': line.part.product_tmpl_id.uom_id.id
                            })
                            st_move_line = self.env['stock.move.line'].create({
                                'company_id': self.env.user.company_id.id,
                                'location_id': 5,
                                'location_dest_id': location_id_returnable_damage,
                                'product_id': product_id,
                                'product_uom_qty': line.qty,
                                'lot_id': available_product_lot.id,
                                'picking_type_id': picking_type,
                                'product_uom_id': st_move.product_uom.id,
                                'bad_ct_serial_no': line.bad_ct_serial_no,
                                'move_id': st_move.id,
                            })
                    else:
                        production_lot_create = self.env['stock.production.lot'].create({
                            'product_id': product_id,
                            'product_uom_id': line.part.product_tmpl_id.uom_id.id,
                            'company_id': self.env.user.company_id.id
                        })
                        stock_quant_create_new_bad_ct_lot = self.env['stock.quant'].create({
                            'location_id': location_id_returnable_damage,
                            'product_id': product_id,
                            'lot_id': production_lot_create.id,
                            'quantity': line.qty,
                        })
                        st_move = self.env['stock.move'].create({
                            'company_id': self.env.user.company_id.id,
                            'location_id': 5,
                            'location_dest_id': location_id_returnable_damage,
                            'product_id': product_id,
                            'product_uom_qty': line.qty,
                            'picking_type_id': picking_type,
                            'name': line.part.name,
                            'product_uom': line.part.product_tmpl_id.uom_id.id,
                            'bad_ct_serial_no': line.bad_ct_serial_no,
                        })

                        # st_move_line = self.env['stock.move.line'].create({
                        #     'company_id': self.env.user.company_id.id,
                        #     'location_id': 5,
                        #     'location_dest_id': location_id_returnable_damage,
                        #     'product_id': product_id,
                        #     'product_uom_qty': line.qty,
                        #     'product_uom_id': st_move.product_uom.id,
                        #     'picking_type_id': picking_type,
                        #     'lot_id': production_lot_create.id,
                        #     'bad_ct_serial_no': line.bad_ct_serial_no,
                        #     'move_id': st_move.id
                        # })
                    for x in res.diagnosis_repair_lines_ids:
                        if x.rep_seq == line.rep_seq:
                            x.is_consumed = True
            self.state = 'confirmed'

    def action_reset_to_draft(self):
        self.state = 'draft'
        for line in self.item_consumption_line_ids:
            line.qty = 1


class ItemConsumptionLines(models.Model):
    _name = "item.consumption.lines"
    _description = "Item Consumption Lines"

    item_consumption_id = fields.Many2one('item.consumption')
    part = fields.Many2one('product.product', string="Part", tracking=True, required=True)
    part_check = fields.Integer(string="Stock Availability", compute='_compute_available_part')
    qty = fields.Integer(string="Quantity", default=1, readonly=True)
    consumption_status = fields.Selection(
        [('used', 'Used'),
         ('unused', 'Unused')],
        string="Consumption Status", readonly="True"
    )
    bad_ct_serial_no = fields.Char(string="Bad CT/Serial No")
    good_ct_serial_no = fields.Many2one('stock.production.lot', string="Good CT/Serial No",
                                        domain="[('id','in',good_ct)]")
    good_ct = fields.Many2many('stock.production.lot', compute="_get_good_ct")
    task_status1 = fields.Many2one('repair.status', string="Task Status")
    remark = fields.Char(string="Remark")
    rep_seq = fields.Char(string='Token')
    spr_claim_tag = fields.Boolean(default=False)

    @api.depends('part')
    def _get_good_ct(self):
        for rec in self:
            location_id = rec.env.user.context_default_warehouse_id.lot_stock_id.id
            product_id = rec.part.id
            stock_quant_data = self.env['stock.quant'].search([
                ('location_id', '=', location_id),
                ('product_id', '=', product_id),
                ('reserved_quantity', '=', 0),
            ])
            get_assign_lot = self.env['item.consumption.lines'].search(
                [('part', '=', product_id)]).good_ct_serial_no.ids

            get_eng_location_lot = self.env['stock.production.lot'].search([('id', 'in', stock_quant_data.lot_id.ids)])
            get_saved_lot = self.env['stock.production.lot'].search([('id', 'in', get_assign_lot)])
            existing_consumption_lot = self.env['stock.production.lot'].search(
                [('id', 'in', rec.item_consumption_id.item_consumption_line_ids.good_ct_serial_no.ids)])

            actual_lots = get_eng_location_lot - get_saved_lot - existing_consumption_lot
            rec.good_ct = actual_lots

    @api.onchange('part')
    def _onchange_part(self):
        for rec in self:
            location_id = rec.env.user.context_default_warehouse_id.lot_stock_id.id
            product_id = rec.part.id
            stock_quant_data = self.env['stock.quant'].search([
                ('location_id', '=', location_id),
                ('product_id', '=', product_id),
                ('reserved_quantity', '=', 0),
            ])
            get_assign_lot = self.env['item.consumption.lines'].search(
                [('part', '=', product_id)]).good_ct_serial_no.ids
            get_eng_location_lot = self.env['stock.production.lot'].search([('id', 'in', stock_quant_data.lot_id.ids)])
            get_saved_lot = self.env['stock.production.lot'].search([('id', 'in', get_assign_lot)])
            existing_consumption_lot = self.env['stock.production.lot'].search(
                [('id', 'in', rec.item_consumption_id.item_consumption_line_ids.good_ct_serial_no.ids)])
            actual_lots = get_eng_location_lot - get_saved_lot - existing_consumption_lot
            return {'domain': {'good_ct_serial_no': [('id', '=', actual_lots.ids)]}}

    @api.depends('part')
    def _compute_available_part(self):
        for rec in self:
            location_id = rec.part.warehouse_id.lot_stock_id.id
            rec.part_check = rec.part.with_context({'location': location_id}).free_qty

    def _show_available_product(self):
        for rec in self:
            location_id = rec.part.warehouse_id.lot_stock_id.id
            product_id = rec.part.id
            stock_quant_data = self.env['stock.quant'].search([
                ('location_id', '=', location_id),
                ('product_id', '=', product_id),
                ('reserved_quantity', '=', 0),
            ])
            return [('id', 'in', stock_quant_data.lot_id.ids)]

    def cancel_consumption(self):
        for rec in self:
            res = self.env['diagnosis.repair'].search([('order_id', '=', rec.item_consumption_id.order_id.id)])
            if rec.consumption_status == 'used':
                location_id = rec.env.user.context_default_warehouse_id.lot_stock_id.id
                product_id = rec.part.id
                lot_id = rec.good_ct_serial_no.id
                stock_quant_data = self.env['stock.quant'].search([
                    ('location_id', '=', location_id),
                    ('product_id', '=', product_id),
                    ('lot_id', '=', lot_id)
                ])
                stock_quant_data.reserved_quantity -= rec.qty
                rec.qty = 0
                rec.consumption_status = 'unused'
                rec.bad_ct_serial_no = None
                rec.good_ct_serial_no = None
                for x in res.diagnosis_repair_lines_ids:
                    if x.rep_seq == rec.rep_seq:
                        x.is_consumed = False


class stock_move_line(models.Model):
    _inherit = 'stock.move'
    bad_ct_serial_no = fields.Char(string="Bad CT/Serial No")

    @api.model
    def create(self, vals):
        res=super(stock_move_line, self).create(vals)
        stock_picking_data = self.env['stock.picking.type'].browse(vals.get('picking_type_id'))
        if stock_picking_data.code == 'outgoing':
            warehouse_data = self.env['stock.warehouse'].browse(vals.get('warehouse_id'))
            if warehouse_data:
                order_id = self.env['sale.order'].search([('name', '=', res.origin)])
                if order_id.part_claim:
                    for rec in order_id.order_line:
                        location_id_returnable_damage = self.env['stock.location'].search(
                            [('branch_id', '=', order_id.branch_id.id),
                             ('is_returnable_damage', '=', True)], limit=1)
                        res.location_id=location_id_returnable_damage.id,
                        res.bad_ct_serial_no=rec.bad_ct
        return res


# from odoo import api, fields, models, _
# from odoo.exceptions import ValidationError
#
#
# class ItemConsumption(models.Model):
#     _name = 'item.consumption'
#     _description = 'Item Consumption'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#     _rec_name = 'ref'
#
#     ref = fields.Char(readonly=True, default=lambda self: _('New'), string="Item Consumption")
#     order_id = fields.Many2one('field.service', string="Service Order", default=lambda self: self.id, readonly=True)
#     imei_no = fields.Char(string='IMEI/Serial No', readonly=False)
#     order_date = fields.Datetime(string="Order Date", readonly=False)
#     branch_id = fields.Many2one("res.branch", readonly=True)
#     customer_id = fields.Char(string="Customer", readonly=True)
#     current_branch = fields.Char(string="Current Branch", tracking=True, readonly=True)
#     departments = fields.Char(string="Department", readonly=False)
#     item_consumption_line_ids = fields.One2many('item.consumption.lines', 'item_consumption_id')
#     diagnosis_repair_ids = fields.Many2one('diagnosis.repair')
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('confirmed', 'Confirmed')],
#         default='draft', string="Status")
#     repair_status1 = fields.Char(string='Repair Status', tracking=True)
#
#     @api.model
#     def create(self, vals):
#         if vals.get('ref', ('New')) == ('New'):
#             vals['ref'] = self.env['ir.sequence'].next_by_code('item.consumption') \
#                           or _('New')
#         res = super(ItemConsumption, self).create(vals)
#         return res
#
#     def action_confirm(self):
#         for rec in self:
#             res = self.env['diagnosis.repair'].search([('order_id', '=', rec.order_id.id)])
#             for line in rec.item_consumption_line_ids:
#                 if line.consumption_status != 'used' and line.consumption_status != 'unused':
#                     location_id = rec.env.user.context_default_warehouse_id.lot_stock_id.id
#                     product_id = line.part.id
#                     lot_id = line.good_ct_serial_no.id
#                     stock_quant_data = self.env['stock.quant'].search([
#                         ('location_id', '=', location_id),
#                         ('product_id', '=', product_id),
#                         ('lot_id', '=', lot_id)
#                     ])
#                     stock_quant_data.reserved_quantity += line.qty
#                     line.consumption_status = 'used'
#                     # Parts storing on Returnable Damage Stock with lot
#                     location_id_returnable_damage = self.env['stock.location'].search(
#                         [('branch_id', '=', self.branch_id.id),
#                          ('is_returnable_damage', '=', True)], limit=1).id
#                     picking_type = self.env['stock.picking.type'].search(
#                         [('warehouse_id', '=', self.env.user.context_default_warehouse_id.id),
#                          ('code', '=', 'internal')]).id
#                     available_product_lot = self.env['stock.production.lot'].search([
#                         ('product_id', '=', product_id),
#                         ('product_uom_id', '=', line.part.product_tmpl_id.uom_id.id),
#                         ('name', '=', line.bad_ct_serial_no),
#                         ('company_id', '=', self.env.user.company_id.id)])
#                     if available_product_lot:
#                         available_bad_product = self.env['stock.quant'].search([
#                             ('location_id', 'not in', [4, 5]),
#                             ('product_id', '=', product_id),
#                             ('lot_id', '=', available_product_lot.id)
#                         ])
#                         if available_bad_product:
#                             raise ValidationError(_("Available Same Lot"))
#                         else:
#                             stock_quant_data_bad_ct_create = self.env['stock.quant'].create({
#                                 'location_id': location_id_returnable_damage,
#                                 'product_id': product_id,
#                                 'lot_id': available_product_lot.id,
#                                 'quantity': line.qty,
#                             })
#                             st_move = self.env['stock.move'].create({
#                                 'company_id': self.env.user.company_id.id,
#                                 'location_id': 5,
#                                 'location_dest_id': location_id_returnable_damage,
#                                 'product_id': product_id,
#                                 'product_uom_qty': line.qty,
#                                 'picking_type_id': picking_type,
#                                 'name': line.part.name,
#                                 'product_uom': line.part.product_tmpl_id.uom_id.id
#                             })
#                             st_move_line = self.env['stock.move.line'].create({
#                                 'company_id': self.env.user.company_id.id,
#                                 'location_id': 5,
#                                 'location_dest_id': location_id_returnable_damage,
#                                 'product_id': product_id,
#                                 'product_uom_qty': line.qty,
#                                 'lot_id': available_product_lot.id,
#                                 'picking_type_id': picking_type,
#                                 'product_uom_id': st_move.product_uom.id,
#                                 'bad_ct_serial_no': line.bad_ct_serial_no,
#                                 'move_id': st_move.id,
#                             })
#                     else:
#                         production_lot_create = self.env['stock.production.lot'].create({
#                             'product_id': product_id,
#                             'product_uom_id': line.part.product_tmpl_id.uom_id.id,
#                             'company_id': self.env.user.company_id.id
#                         })
#                         stock_quant_create_new_bad_ct_lot = self.env['stock.quant'].create({
#                             'location_id': location_id_returnable_damage,
#                             'product_id': product_id,
#                             'lot_id': production_lot_create.id,
#                             'quantity': line.qty,
#                         })
#                         st_move = self.env['stock.move'].create({
#                             'company_id': self.env.user.company_id.id,
#                             'location_id': 5,
#                             'location_dest_id': location_id_returnable_damage,
#                             'product_id': product_id,
#                             'product_uom_qty': line.qty,
#                             'picking_type_id': picking_type,
#                             'name': line.part.name,
#                             'product_uom': line.part.product_tmpl_id.uom_id.id
#                         })
#                         st_move_line = self.env['stock.move.line'].create({
#                             'company_id': self.env.user.company_id.id,
#                             'location_id': 5,
#                             'location_dest_id': location_id_returnable_damage,
#                             'product_id': product_id,
#                             'product_uom_qty': line.qty,
#                             'product_uom_id': st_move.product_uom.id,
#                             'picking_type_id': picking_type,
#                             'lot_id': production_lot_create.id,
#                             'bad_ct_serial_no': line.bad_ct_serial_no,
#                             'move_id': st_move.id
#                         })
#                     for x in res.diagnosis_repair_lines_ids:
#                         if x.rep_seq == line.rep_seq:
#                             x.is_consumed = True
#             self.state = 'confirmed'
#
#     def action_reset_to_draft(self):
#         self.state = 'draft'
#         for line in self.item_consumption_line_ids:
#             line.qty = 1
#
#
# class ItemConsumptionLines(models.Model):
#     _name = "item.consumption.lines"
#     _description = "Item Consumption Lines"
#
#     item_consumption_id = fields.Many2one('item.consumption')
#     part = fields.Many2one('product.product', string="Part", tracking=True, required=True)
#     part_check = fields.Integer(string="Stock Availability", compute='_compute_available_part')
#     qty = fields.Integer(string="Quantity", default=1, readonly=True)
#     consumption_status = fields.Selection(
#         [('used', 'Used'),
#          ('unused', 'Unused')],
#         string="Consumption Status", readonly="True"
#     )
#     bad_ct_serial_no = fields.Char(string="Bad CT/Serial No")
#     good_ct_serial_no = fields.Many2one('stock.production.lot', string="Good CT/Serial No",
#                                         domain="[('id','in',good_ct)]")
#     good_ct = fields.Many2many('stock.production.lot', compute="_get_good_ct")
#     task_status1 = fields.Many2one('repair.status', string="Task Status")
#     remark = fields.Char(string="Remark")
#     rep_seq = fields.Char(string='Token')
#     spr_claim_tag = fields.Boolean(default=False)
#
#     @api.depends('part')
#     def _get_good_ct(self):
#         for rec in self:
#             location_id = rec.env.user.context_default_warehouse_id.lot_stock_id.id
#             product_id = rec.part.id
#             stock_quant_data = self.env['stock.quant'].search([
#                 ('location_id', '=', location_id),
#                 ('product_id', '=', product_id),
#                 ('reserved_quantity', '=', 0),
#             ])
#             get_assign_lot = self.env['item.consumption.lines'].search(
#                 [('part', '=', product_id)]).good_ct_serial_no.ids
#
#             get_eng_location_lot = self.env['stock.production.lot'].search([('id', 'in', stock_quant_data.lot_id.ids)])
#             get_saved_lot = self.env['stock.production.lot'].search([('id', 'in', get_assign_lot)])
#             existing_consumption_lot = self.env['stock.production.lot'].search(
#                 [('id', 'in', rec.item_consumption_id.item_consumption_line_ids.good_ct_serial_no.ids)])
#
#             actual_lots = get_eng_location_lot - get_saved_lot - existing_consumption_lot
#             rec.good_ct = actual_lots
#
#     @api.onchange('part')
#     def _onchange_part(self):
#         for rec in self:
#             location_id = rec.env.user.context_default_warehouse_id.lot_stock_id.id
#             product_id = rec.part.id
#             stock_quant_data = self.env['stock.quant'].search([
#                 ('location_id', '=', location_id),
#                 ('product_id', '=', product_id),
#                 ('reserved_quantity', '=', 0),
#             ])
#             get_assign_lot = self.env['item.consumption.lines'].search(
#                 [('part', '=', product_id)]).good_ct_serial_no.ids
#             get_eng_location_lot = self.env['stock.production.lot'].search([('id', 'in', stock_quant_data.lot_id.ids)])
#             get_saved_lot = self.env['stock.production.lot'].search([('id', 'in', get_assign_lot)])
#             existing_consumption_lot = self.env['stock.production.lot'].search(
#                 [('id', 'in', rec.item_consumption_id.item_consumption_line_ids.good_ct_serial_no.ids)])
#             actual_lots = get_eng_location_lot - get_saved_lot - existing_consumption_lot
#             return {'domain': {'good_ct_serial_no': [('id', '=', actual_lots.ids)]}}
#
#     @api.depends('part')
#     def _compute_available_part(self):
#         for rec in self:
#             location_id = rec.part.warehouse_id.lot_stock_id.id
#             rec.part_check = rec.part.with_context({'location': location_id}).free_qty
#
#     def _show_available_product(self):
#         for rec in self:
#             location_id = rec.part.warehouse_id.lot_stock_id.id
#             product_id = rec.part.id
#             stock_quant_data = self.env['stock.quant'].search([
#                 ('location_id', '=', location_id),
#                 ('product_id', '=', product_id),
#                 ('reserved_quantity', '=', 0),
#             ])
#             return [('id', 'in', stock_quant_data.lot_id.ids)]
#
#     def cancel_consumption(self):
#         for rec in self:
#             res = self.env['diagnosis.repair'].search([('order_id', '=', rec.item_consumption_id.order_id.id)])
#             if rec.consumption_status == 'used':
#                 location_id = rec.env.user.context_default_warehouse_id.lot_stock_id.id
#                 product_id = rec.part.id
#                 lot_id = rec.good_ct_serial_no.id
#                 stock_quant_data = self.env['stock.quant'].search([
#                     ('location_id', '=', location_id),
#                     ('product_id', '=', product_id),
#                     ('lot_id', '=', lot_id)
#                 ])
#                 stock_quant_data.reserved_quantity -= rec.qty
#                 rec.qty = 0
#                 rec.consumption_status = 'unused'
#                 rec.bad_ct_serial_no = None
#                 rec.good_ct_serial_no = None
#                 for x in res.diagnosis_repair_lines_ids:
#                     if x.rep_seq == rec.rep_seq:
#                         x.is_consumed = False
#
#
# class stock_move_line(models.Model):
#     _inherit = 'stock.move.line'
#     bad_ct_serial_no = fields.Char(string="Bad CT/Serial No")

