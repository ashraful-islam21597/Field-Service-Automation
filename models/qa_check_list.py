# from odoo import api, fields, models, _
# from datetime import date
#
# class QualityCheckingList(models.Model):
#     _name = "quality.list"
#
#     category=fields.Char(string="QC Category")
#     category_ids=fields.One2many('quality.list.lines','category_id',string='Qc list ids')
#
# class QualityCheckingList_lines(models.Model):
#     _name="quality.list.lines"
#     name= fields.Char(string="Description")
#     category_id=fields.Many2one('quality.list', string="qc category")


from odoo import api, fields, models, _
from datetime import date

class QualityCheckingList(models.Model):
    _name = "quality.list"
    _rec_name="category"

    category=fields.Char(string="QC Category")
    category_ids=fields.One2many('quality.list.lines','category_id',string='Qc list ids')

class QualityCheckingList_lines(models.Model):
    _name="quality.list.lines"
    _rec_name='name'
    name= fields.Char(string="Description")
    category_id=fields.Many2one('quality.list', string="QC Category")