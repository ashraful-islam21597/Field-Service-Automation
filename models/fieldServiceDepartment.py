# # -*- coding: utf-8 -*-
from odoo import api, fields, models, _
#
#
# class FieldServiceDepartment(models.Model):
#     _name = "field.service.department"
#     _description = "Field Service Department"
#     _rec_name = 'name'
#
#     name = fields.Char(string="Name", required=True)
#     active = fields.Boolean(string="Active", default=True)
#
#
# class ResUsers(models.Model):
#     _inherit = 'res.users'
#
#     department_id = fields.Many2one('field.service.department', string='Department')
class FieldServiceDepartment(models.Model):
    _name = "field.service.department"
    _description = "Field Service Department"
    _rec_name = 'name'
    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string="Active", default=True)



class ResUsers(models.Model):
    _inherit = 'res.users'
    department_id = fields.Many2one('field.service.department', string='Department')


