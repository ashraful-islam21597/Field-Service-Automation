from odoo import api, fields, models, _


class WarehouseMapping(models.Model):
    _name = "warehouse.mapping"
    _description = "Warehouse Mapping"
    _rec_name = 'ref'

    ref = fields.Char(readonly=True, default=lambda self: _('New'), string="Reference")
    branch_id = fields.Many2one('res.branch', string="Branch")
    stock_type = fields.Selection(
        [
            ('warranty', 'Warranty'),
            ('non_warranty', 'Non Warranty')
        ], string="Stock Type"
    )

    allowed_location = fields.Many2many('stock.location', string="Allowed Location")
    default_location = fields.Many2one('stock.location', string="Default Location")
    is_engineer_warehouse = fields.Many2many('stock.location', 'allowed_location', string="Is Engineer Warehouse")

    context_default_warehouse_id = fields.Many2one(
        'stock.warehouse', string='Default Warehouse', company_dependent=True
    )
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=False, readonly=True,
        states={'draft': [('readonly', False)]})

    @api.onchange('branch_id')
    def onchange_branch(self):
        for rec in self:
            return {'domain': {'allowed_location': [('branch_id', '=', rec.branch_id.id)]}}

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        for rec in self:
            return {'domain': {'is_engineer_warehouse': [('branch_id', '=', rec.branch_id.id)]}}

    @api.onchange('branch_id')
    def onchange_branch_default_location(self):
        for rec in self:
            return {'domain': {'default_location': [('branch_id', '=', rec.branch_id.id)]}}

    @api.model
    def create(self, vals):
        if vals.get('ref', _('New')) == _('New'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('warehouse.mapping') \
                          or _('New')
        res = super(WarehouseMapping, self).create(vals)
        return res
