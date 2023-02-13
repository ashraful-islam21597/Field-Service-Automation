from odoo import api, fields, models, _


class SymptomsType(models.Model):
    _name = "symptoms.type"
    _description = "Symptoms Type"
    _rec_name = "symptom"
    symptom = fields.Char(string='Symptom')
    active = fields.Boolean(string='Active', default=True, copy=False)

    possible_solution_lines_ids = fields.One2many('possible.solution.lines', 'symptoms_type',
                                                  string="Possible solution")

    class PossibleSoultionLines(models.Model):
        _name = "possible.solution.lines"
        _description = "Possible Soultion Lines"
        _rec_name = "possible_solution"

        # possible_solution = fields.Many2one('possible.solution',string='Possible Soultion')
        possible_solution = fields.Char(string='Possible Soultion')
        symptoms_type = fields.Many2one('symptoms.type', string="Symptoms Type")


class ReasonType(models.Model):
    _name = "reasons.type"
    _rec_name = "reason"
    reason = fields.Char(string='Reason')
    active = fields.Boolean(string='Active', default=True, copy=False)
