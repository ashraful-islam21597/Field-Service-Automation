from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError


class FieldServiceMonitoringData(models.Model):
    _name = 'field.service.monitoring.data'
    _description = "Field Service Monitoring Data"
    _rec_name = 'so_number'

    # so_number = fields.Many2one('field.service', string='So Number')
    # date_start = fields.Date(string='Start Date', )
    # date_end = fields.Date(string='End Date', default=fields.Date.today)
    # monitor_type = fields.Selection([
    #     ('so_date_wise', "SO Create Date Wise"),
    #     ('delivery_date_wise', "SO Delivery Date Wise")], default=False, string="Monitoring Type")
    # monitoring_data_lines_ids = fields.One2many('field.service.monitoring.data.lines', "monitoring_data_id",
    #                                             string="Monitoring Data Lines")

    so_number = fields.Many2one('field.service', string='So Number')
    # monitoring_data_id = fields.Many2one('field.service.monitoring.data', string="Monitoring Data")
    imei_no = fields.Char(string="IMEI Number")
    customer = fields.Many2one('res.partner', string="Customer")
    retailer = fields.Many2one('res.partner', string="Retailer")
    receive_from = fields.Many2one('res.partner', string="Receive From")
    mobile = fields.Char(string="Mobile")
    so_date = fields.Datetime(string='Create Date')
    brand = fields.Many2one('field.service.department', string="Brand")
    product = fields.Many2one('product.product', string="Product")
    cost_center = fields.Many2one('res.branch', string="Cost Center")
    warranty_status = fields.Many2one('warranty.status', string="Warranty Status")
    service_order_date = fields.Date(string="Service Order Date")
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
    assign_f = fields.Selection(
        [('diagnosis and repair', 'Diagnosis and Repair'),
         ('quality assurance', 'Quality Assurance'),
         ('over phone communication', 'Over Phone Communication')
         ], string="Assigned For")
    assign_date = fields.Date(string="Assign Date")
    assign_status = fields.Many2one("repair.status", string="Assign Status")
    qa_status = fields.Many2one("repair.status", string="Qa Status")
    remarks = fields.Char(string="Remark")
    qa_comment = fields.Char(string="Qa Comment")
    delivery_date = fields.Date(string="Delivery Date")
    dpt_diff_days = fields.Integer(string='DptDiffDate')
    # dpt_diff_date = fields.Date(string='DptDiffDate', compute="difference_date",store=True)
    # dpt_diff_days = fields.Date(string='DptDiffDate')

    assign_date_qa = fields.Date(string='AssignDateQA')
    assign_by_qa = fields.Many2one('res.users', string='AssignByQA')
    assign_eng_qa = fields.Many2one('res.partner', string='AssignEngineerQA')
    assign_by_op = fields.Many2one('res.users', string='AssignByOP')
    assign_eng_op = fields.Many2one('res.partner', string='AssignEngineerOP')

    rbt_no = fields.Many2one('stock.picking', string="RBTNo")
    to_branch = fields.Many2one('res.branch', string="TransferBranch")
    tbr_by = fields.Many2one('res.partner', string="RBTBy")
    rbt_date = fields.Date(string='RBTDate')
    rtt_date = fields.Date(string='RTTday')
    tbt_date = fields.Date(string='TBTDate')
    rbr_date = fields.Date(string='RBRDate')
    tbt_by = fields.Many2one('res.users', string='TBTBy')
    dest_type = fields.Selection([
        ('branch', 'Branch'),
        ('department', 'Department')
    ], string="Destination Type")
    dept = fields.Many2one('field.service.department', string='Department')
    current_user = fields.Many2one('res.users', string="RBRBy")
    rbr_by = fields.Many2one('res.users', string='RBRBy')
    rbr_no = fields.Many2one('stock.picking', string='RBRNO')
    tin_transit_day = fields.Date(string='TInTransitDay')
    delivery_diff_date = fields.Date(string='DeliveryDiffDate')
    delivery_by = fields.Many2one('res.users', string='DeliveryBy')
    delivery_date = fields.Date(string='DeliveryDate')
    warranty_expiry_date_p = fields.Date(string='WarrantyExpiryDate P')
    warranty_expiry_date_l = fields.Date(string='WarrantyExpiryDate L')
    expected_deliver_date = fields.Date(string='ExpectedDeliveryDate')
    claim_no = fields.Char(string='ClaimNO')
    principal_claim_no = fields.Char(string='PrincipalSONO')
    part_claim_no = fields.Char(string='PartsClaimNO')
    claim_create_no = fields.Char(string='ClaimCreateOn')
    claim_date = fields.Date(string='ClaimDate')
    claim_by = fields.Many2one('res.users', string='ClaimBy')
    receive_by = fields.Many2one('res.users', string='ReceiveBy')
    claim_receive_date = fields.Date(string='ClaimReceiveDate')
    claim_tat = fields.Char(string='ClaimTAT')
    claim_receive_create_date = fields.Date(string='ClaimReceiveCreateDate')
    brand_name = fields.Many2one('res.branch', string='BrandName')

    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, 'field_service_monitoring_data')
    #     self.env.cr.execute("""
    #                  CREATE OR REPLACE VIEW field_service_monitoring_data AS (
    #                      SELECT
    #                          row_number() OVER () AS id,
    #                          line.so_number,
    #                          line.imei_no,
    #                          line.customer,
    #                          line.product,
    #                          FROM (
    #                              SELECT sol.imei_no,sol,customer,sol.product so.so_number from
    #                              field_service_monitoring_data_lines sol
    #                              left join field_service_monitoring_data so ON (so.id=sol.monitoring_data_id)
    #
    #                           )line
    #                      )""")


class FieldServiceMonitoringDataLine(models.Model):
    _name = 'field.service.monitoring.data.lines'
    _description = "Field Service Monitoring Data Lines"

    so_number = fields.Many2one('field.service', string='So Number')
    monitoring_data_id = fields.Many2one('field.service.monitoring.data', string="Monitoring Data")
    imei_no = fields.Char(string="IMEI Number")
    customer = fields.Many2one('res.partner', string="Customer")
    retailer = fields.Many2one('res.partner', string="Retailer")
    receive_from = fields.Many2one('res.partner', string="Receive From")
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

    assign_for = fields.Many2one("res.users", string="Assigned TO")
    assign_by = fields.Many2one('res.users', string="Assign By")
    assign_f = fields.Selection(
        [('diagnosis_and_repair', 'Diagnosis and Repair'),
         ('quality_assurance', 'Quality Assurance'),
         ('over_phone_communication', 'Over Phone Communication')
         ], string="Assigned For")
    assign_date = fields.Date(string="Assign Date")
    assign_status = fields.Many2one("repair.status", string="Assign Status")
    qa_status = fields.Many2one("repair.status", string="Qa Status")
    remarks = fields.Char(string="Remark")
    qa_comment = fields.Char(string="Qa Comment")
    delivery_date = fields.Date(string="Delivery Date")

    @api.model
    def create(self, vals):
        res = super(FieldServiceMonitoringDataLine, self).create(vals)

        # monitoring_line = self.env['field.service.monitoring.data.line'].search(
        #             [('so_number', '=', vals['s'])])

        # c_res = self.env['another.submodel'].create({'field_name': value, ...})
        #
        # # creating B record
        #
        # b_res = self.env['sub.model'].create({'field_name': value, ...})
        #
        # # Adding C to B
        #
        # b_res.xx_ids += c_res
        #
        # res.x_ids += b_res
        #
        # return res
