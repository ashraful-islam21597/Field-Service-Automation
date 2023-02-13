from odoo import api, fields, models, _


class ItemConsumptionInherit(models.Model):
    _inherit = "field.service"

    def action_item_consumption_details(self):
        self.ensure_one()
        for rec in self:
            line = []
            consumption_exists = self.env['item.consumption'].search([('order_id', '=', rec.id)])
            if not consumption_exists:
                dr = self.env['diagnosis.repair'].search([('order_id', '=', rec.id)])

                for i in dr.diagnosis_repair_lines_ids:
                    if i.task_status1.repair_status == "Ready For Replacement":
                        line.append((0, 0, {
                            'part': i.part.id,
                            'part_check': i.part_check,
                            'task_status1': i.task_status1.id,
                            'bad_ct_serial_no': i.defective_sno,
                            'rep_seq': i.rep_seq
                        }))
                vals = {
                    'order_id': self.id,
                    'item_consumption_line_ids': line
                }
                consumption_exists = self.env['item.consumption'].sudo().create(vals)
            else:
                dr = self.env['diagnosis.repair'].search([('order_id', '=', rec.id)])
                for i in dr.diagnosis_repair_lines_ids:
                    existing_consumption_line_ids = consumption_exists.item_consumption_line_ids.filtered(
                        lambda x: x.rep_seq == i.rep_seq)
                    if not existing_consumption_line_ids:
                        if i.task_status1.repair_status == "Ready For Replacement":
                            line.append({
                                'part': i.part.id,
                                'part_check': i.part_check,
                                'task_status1': i.task_status1.id,
                                'bad_ct_serial_no': i.defective_sno,
                                'rep_seq': i.rep_seq,
                                'item_consumption_id': consumption_exists.id,
                            })
                if line:
                    self.env['item.consumption.lines'].create(line)
            for i in consumption_exists:
                i.order_date = self.order_date
                i.branch_id = self.branch_name.id
                i.departments = self.departments.name
        return {
            'name': _('Item Consumption'),
            'view_mode': 'form',
            'res_model': 'item.consumption',
            'views': [(self.env.ref('usl_service_erp.view_item_consumption_form').id, 'form'), (False, 'list')],
            'type': 'ir.actions.act_window',
            # 'context': {
            #     'default_order_id': self.id,
            # },
            # 'res_id': self.env['item.consumption'].sudo().search([('order_id', '=', self.id)],
            #                                                      limit=1, order='id desc').id
            'res_id': consumption_exists.id
        }
