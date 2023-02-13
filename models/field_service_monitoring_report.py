from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FieldServiceMonitoringReport(models.Model):
    _name = 'field.service.monitoring.report'
    _description = "Field Service Monitoring Report"
    _rec_name = 'so_number'

    so_number = fields.Many2one('field.service', string='So Number')
    date_start = fields.Date(string='Start Date', )
    date_end = fields.Date(string='End Date', default=fields.Date.today)
    monitor_type = fields.Selection([
        ('so_date_wise', "SO Create Date Wise"),
        ('delivery_date_wise', "SO Delivery Date Wise")], default=False, string="Monitoring Type")

    monitoring_report_lines_ids = fields.One2many('field.service.monitoring.report.lines', "monitoring_report_id",
                                                  string="Monitoring Report Lines")


class FieldServiceMonitoringReportLine(models.Model):
    _name = 'field.service.monitoring.report.lines'
    _description = "Field Service Monitoring Report Lines"

    so_number = fields.Many2one('field.service', string='So Number')
    monitoring_report_id = fields.Many2one('field.service.monitoring.report', string="Monitoring Report")
    imei_no = fields.Char(string="IMEI Number")
    customer = fields.Many2one('res.partner', string="Customer")
    retailer = fields.Many2one('res.partner', string="Retailer")
    receive_from = fields.Many2one('res.partner', string="Receive From")
    so_date = fields.Datetime(string='Create Date')
    mobile = fields.Char(string="Mobile")
    brand = fields.Many2one('field.service.department', string="Brand")
    product = fields.Many2one('product.product', string="Product")
    cost_center = fields.Many2one('res.branch', string="Cost Center")
    warranty_status = fields.Many2one('warranty.status', string="Warranty Status")
    service_order_date = fields.Datetime(string="Service Order Date")
    so_created_by = fields.Many2one("res.users", string="Created By")
    service_type = fields.Many2one("service.type", string="Service Type")
    repair_status = fields.Many2one("repair.status", string="Repair Status")
    item_receive_branch = fields.Many2one("res.branch", string='Item Receive Branch')
    item_receive_status = fields.Char(string='Item Receive Status')
    product_receive_date = fields.Date(string='Product Receive Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('service_for_approval', 'Submitted For Approval'),
        ('approval', 'Approved'),
        ('cancel', 'Canceled'),
    ], string="Status")

    model_state = fields.Selection([
        ('fs_create', 'Field Service Created'),
        ('fs_submit_for_approval', 'Field Service Submit For Approved'),
        ('fs_approval', 'Field Service Approved'),
        ('receive', 'Received'),
        ('assign_eng', 'Assigned Engineer'),
        ('order_transfer', 'Ordered Transfer'),
    ], string="Model Status")

    assign_for = fields.Many2one("res.users", string="Assign For")
    assign_by = fields.Many2one('res.users', string="Assign By")
    assign_date = fields.Date(string="Assign Date")
    assign_status = fields.Many2one("repair.status", string="Assign Status")
    qa_status = fields.Many2one("repair.status", string="Qa Status")
    remarks = fields.Char(string="Remark")
    qa_comment = fields.Char(string="Qa Comment")
    delivery_date = fields.Date(string="Delivery Date")
