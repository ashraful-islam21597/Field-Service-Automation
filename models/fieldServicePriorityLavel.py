from odoo import api, fields, models, _


class FieldServiceDepartment(models.Model):
    _name = "field.service.priority.level"
    _description = "Field Service Priority Level"
    _rec_name = 'priority_level'

    priority_level = fields.Char(string="Priority Level", required=True)
    active = fields.Boolean(string="Active",  default=True)


