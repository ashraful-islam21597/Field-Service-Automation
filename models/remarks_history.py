from odoo import api, fields, models, _
from datetime import date
from datetime import datetime



class RemarksHistory(models.Model):
    _name = "remarks.history"
    _description = "Remarks History"
    _rec_name = "order_id"

    order_id = fields.Many2one('field.service',  string='Service Order ID')
    remarks_lines_ids = fields.One2many('remarks.lines', 'remark_id',
                                                  string="Remarks line", readonly=True)
class RemarksLines(models.Model):
    _name = "remarks.lines"
    _description = "Remarks Lines"

    # possible_solution = fields.Many2one('possible.solution',string='Possible Soultion')
    remarks = fields.Char(string='Remark')
    # remarked_date = fields.Date(string='Date')
    remarked_date = fields.Datetime(string='Date')
    remarked_by = fields.Many2one('res.users', string='Remarked by')
    remarked_place = fields.Char(string='Remarked Place')
    remark_id = fields.Many2one('remarks.history', string="Remarks")
