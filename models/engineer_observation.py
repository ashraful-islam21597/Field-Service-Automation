from odoo import api, fields, models, _
from datetime import date


class EngineerObservation(models.Model):
    _name = 'engineer.observation'
    _description = 'Engineer Observation'
    _rec_name = "engineer_observation"

    engineer_observation = fields.Char(string="Engineer Observation")
    active = fields.Boolean(string='Active', default=True)
