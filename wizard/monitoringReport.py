# -*- coding: utf-8 -*-
from xlsxwriter import workbook

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta, BytesIO, xlsxwriter, \
    base64


# from custom_addons.usl_service_erp.models.xls_report_tool import UslXlxsReportUtil as utill

class MonitoringReportWizard(models.TransientModel):
    _name = "monitoring.report.wizard"
    _description = "Monitoring Report Wizard"

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    so_numbers = fields.Many2many('field.service', 'mrw_report_monitor_rel', 'mrw_report_monitor_id',
                                  string='So Number')
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    customer_ids = fields.Many2many('res.partner', 'mr_report_customer_rel', 'mr_report_customer_id', 'part_id',
                                    'Customer')
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)
    monitor_type = fields.Selection([
        ('so_date_wise', "SO Create Date Wise"),
        ('delivery_date_wise', "SO Delivery Date Wise")], default=False, string="Monitoring Type")

    def _get_companies(self):
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        allowed_company = []
        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    def action_print_excel_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'so_numbers': self.so_numbers,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'company_id': self.company_id.id,
                'customer_ids': self.customer_ids,
                'monitor_type': self.monitor_type,
                # 'branch_name': self.branch_ids.name,
            },
        }
        so_numbers = data['form']['so_numbers']
        start_date = data['form']['date_start']
        end_date = data['form']['date_end']
        customer_ids = data['form']['customer_ids']
        company_id = data['form']['company_id']
        monitor_type = data['form']['monitor_type']
        #
        new_customer_ids = []
        # x = customer_ids.split("(")
        # y = x[1].split(")")
        # z = y[0].split(",")
        where_so_number = "1=1"
        where_monitor_type = "1=1"
        where_customer_ids = "1=1"
        where_branch_ids = "1=1"
        where_branch_ids = "1=1"
        where_date = ""
        if monitor_type == 'so_date_wise':
            where_date = "sf.create_date::DATE between '{}' and '{}'".format(start_date.strftime(DATETIME_FORMAT),
                                                                             end_date.strftime(DATETIME_FORMAT))
        if monitor_type == 'delivery_date_wise':
            where_date = "sp.write_date::DATE between '{}' and '{}'".format(start_date.strftime(DATETIME_FORMAT),
                                                                            end_date.strftime(DATETIME_FORMAT))
        if so_numbers:
            where_so_number = "sf.id in %s" % str(tuple(so_numbers.ids)).replace(',)',')')
        if customer_ids:
            where_customer_ids = "sf.partner_id in %s" % str(tuple(customer_ids.ids)).replace(',)',
                                                                                              ')')
        if company_id:
            where_company_id = " sf.company_id = %s" % company_id
        else:
            where_company_id = "1=1"

        query = """SELECT sf.order_no,sf.order_date,sf.imei_no,sf.repair_status,sf.remark as so_remark,sf.item_receive_status, 
                    sf.state as so_state, arp.name as engineer_name,ael.assign_date,ael.remarks as assign_engineer_remark, 
                    ael.assign_status1,ael.assign_for,drp.name as diagnosis_repair_engineer,drs.state as diagnosis_repair_state,
                    pt.name as product,sf.invoice,sf.phone,sf.state,ru.login,fsd.name as department_name,ws.name as warranty_status,
                    rp.name as customer,st.name as service_type,rp.name as customer,rb.name as item_receive_branch,
                    sf.product_receive_date,sf.delivery_date,sf.p_delivery_date AS possible_delivery_date, 
                    rp.name as transfer_to,sp.state, rb.name as from_branch,sp.to_branch,sp.scheduled_date
                    FROM field_service sf
                    LEFT JOIN diagnosis_repair drs ON (sf.id = drs.order_id)
                    LEFT JOIN res_users dru ON (dru.id =drs.engineer )
                    LEFT JOIN res_Partner drp ON (drp.id = dru.partner_id)
                    LEFT JOIN service_type st ON (st.id = sf.service_type)
                    LEFT JOIN res_branch rb ON (rb.id =sf.item_receive_branch)
                    LEFT JOIN res_partner rp ON (rp.id= sf.customer_id)
                    LEFT JOIN res_users ru ON (ru.id= sf.user_id)
                    LEFT JOIN warranty_status ws ON (ws.id= sf.warranty_status)
                    LEFT JOIN field_service_department fsd ON (fsd.id= sf.departments)
                    LEFT JOIN product_product pp ON (pp.id =sf.product_id )
                    LEFT JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
                    LEFT JOIN assign_engineer_details aed ON (sf.id = aed.order_id)
                    LEFT JOIN assign_engineer_lines ael ON (ael.id = aed.order_id)
                    LEFT JOIN res_users aru ON (aru.id =ael.engineer_name )
                    LEFT JOIN stock_picking_rel spr ON (spr.field_service_id = sf.id)
                    LEFT JOIN stock_picking sp ON (sp.id = spr.stock_picking_id)
                    LEFT JOIN res_Partner arp ON (arp.id = aru.partner_id) where {} and {} """.format(where_so_number,
                                                                                                      where_date)
        self._cr.execute(query=query)
        result = self._cr.fetchall()
        report_name = 'Service Monitoring Report'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)
        # worksheet.merge_range('A2:D3', report_name, wbf['title_doc'])
        # columns_group = [
        #     ('SL', 30, 'no', 'no'),
        #     ('Invoice No', 30, 'char', 'char'),
        #     ('BP Amount', 50, 'char', 'char'),
        # ]
        col = 0
        row = 0
        worksheet.write(row, col, "SoNumber", wbf['title_doc'])
        worksheet.write(row, col + 1, "OrderDate", wbf['title_doc'])
        worksheet.write(row, col + 2, "ImeiNo", wbf['title_doc'])
        worksheet.write(row, col + 3, "RepairStatus", wbf['title_doc'])
        worksheet.write(row, col + 4, "SoRemark", wbf['title_doc'])
        worksheet.write(row, col + 5, "ItemReceiveStatus", wbf['title_doc'])
        worksheet.write(row, col + 6, "SoState", wbf['title_doc'])
        worksheet.write(row, col + 7, "EngineerName", wbf['title_doc'])
        worksheet.write(row, col + 8, "EngAssignDate", wbf['title_doc'])
        worksheet.write(row, col + 9, "AssignEngRemark", wbf['title_doc'])
        worksheet.write(row, col + 10, "EngAssignStatus", wbf['title_doc'])
        worksheet.write(row, col + 11, "EngAssignFor", wbf['title_doc'])
        worksheet.write(row, col + 12, "EngDiagnosisRepair", wbf['title_doc'])
        worksheet.write(row, col + 13, "DiagnosisRepairState", wbf['title_doc'])
        worksheet.write(row, col + 14, "Product", wbf['title_doc'])
        worksheet.write(row, col + 15, "Invoice", wbf['title_doc'])
        worksheet.write(row, col + 16, "Phone", wbf['title_doc'])
        worksheet.write(row, col + 17, "State", wbf['title_doc'])
        worksheet.write(row, col + 18, "Login", wbf['title_doc'])
        worksheet.write(row, col + 19, "DepartmentName", wbf['title_doc'])
        worksheet.write(row, col + 20, "WarrantyStatus", wbf['title_doc'])
        worksheet.write(row, col + 21, "Customer", wbf['title_doc'])
        worksheet.write(row, col + 22, "ServiceType", wbf['title_doc'])
        worksheet.write(row, col + 23, "Customer", wbf['title_doc'])
        worksheet.write(row, col + 24, "ItemReceiveBranch", wbf['title_doc'])
        worksheet.write(row, col + 25, "ProductReceiveDate", wbf['title_doc'])
        worksheet.write(row, col + 26, "DeliveryDate", wbf['title_doc'])
        worksheet.write(row, col + 27, "PossibleDeliveryDate", wbf['title_doc'])
        worksheet.write(row, col + 28, "TransferTo", wbf['title_doc'])
        worksheet.write(row, col + 29, "State", wbf['title_doc'])
        worksheet.write(row, col + 30, "FromBranch", wbf['title_doc'])
        worksheet.write(row, col + 31, "TransferToBranch", wbf['title_doc'])
        worksheet.write(row, col + 32, "ScheduledDate", wbf['title_doc'])
        for so_number in result:
            row += 1
            worksheet.write(row, col, so_number[0])
            worksheet.write(row, col + 1, str(so_number[1]))
            worksheet.write(row, col + 2, so_number[2])
            worksheet.write(row, col + 3, so_number[3])
            worksheet.write(row, col + 4, so_number[4])
            worksheet.write(row, col + 5, so_number[5])
            worksheet.write(row, col + 6, so_number[6])
            worksheet.write(row, col + 7, so_number[7])
            worksheet.write(row, col + 8, str(so_number[8]))
            worksheet.write(row, col + 9, so_number[9])
            worksheet.write(row, col + 10, so_number[10])
            worksheet.write(row, col + 11, so_number[11])
            worksheet.write(row, col + 12, so_number[12])
            worksheet.write(row, col + 13, so_number[13])
            worksheet.write(row, col + 14, so_number[14])
            worksheet.write(row, col + 15, so_number[15])
            worksheet.write(row, col + 16, so_number[16])
            worksheet.write(row, col + 17, so_number[17])
            worksheet.write(row, col + 18, so_number[18])
            worksheet.write(row, col + 19, so_number[19])
            worksheet.write(row, col + 20, so_number[20])
            worksheet.write(row, col + 21, so_number[21])
            worksheet.write(row, col + 22, so_number[22])
            worksheet.write(row, col + 23, so_number[23])
            worksheet.write(row, col + 24, so_number[24])
            worksheet.write(row, col + 25, str(so_number[25]))
            worksheet.write(row, col + 26, str(so_number[26]))
            worksheet.write(row, col + 27, str(so_number[27]))
            worksheet.write(row, col + 28, so_number[28])
            worksheet.write(row, col + 29, so_number[29])
            worksheet.write(row, col + 30, so_number[30])
            worksheet.write(row, col + 31, so_number[31])
            worksheet.write(row, col + 32, str(so_number[32]))

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'datas': out, 'datas_fname': filename})
        fp.close()
        filename += '%2Exlsx'
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=datas&download=true&filename=' + filename,
        }

        # return self.env.ref('usl_service_erp.report_service_order_monitoring_xls').report_action(self, data=result)

    def add_workbook_format(self, workbook):
        colors = {
            'white_orange': '#FFFFDB',
            'orange': '#FFC300',
            'red': '#FF0000',
            'yellow': '#F6FA03',
        }

        wbf = {}
        wbf['header'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Georgia'})
        wbf['header'].set_border()

        wbf['header_orange'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['orange'], 'font_color': '#000000',
             'font_name': 'Georgia'})
        wbf['header_orange'].set_border()

        wbf['header_yellow'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['yellow'], 'font_color': '#000000',
             'font_name': 'Georgia'})
        wbf['header_yellow'].set_border()

        wbf['header_no'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Georgia'})
        wbf['header_no'].set_border()
        wbf['header_no'].set_align('vcenter')

        wbf['footer'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})

        wbf['content_datetime'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss', 'font_name': 'Georgia'})
        wbf['content_datetime'].set_left()
        wbf['content_datetime'].set_right()

        wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd', 'font_name': 'Georgia'})
        wbf['content_date'].set_left()
        wbf['content_date'].set_right()

        wbf['title_doc'] = workbook.add_format({
            'bold': True,
            'align': 'center',
            # 'valign': 'vcenter',
            'font_size': 11,
            'font_name': 'Georgia',
        })

        wbf['company'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})
        wbf['company'].set_font_size(11)

        wbf['content'] = workbook.add_format()
        wbf['content'].set_left()
        wbf['content'].set_right()

        wbf['content_float'] = workbook.add_format(
            {'align': 'right', 'num_format': '#,##0.00', 'font_name': 'Georgia'})
        wbf['content_float'].set_right()
        wbf['content_float'].set_left()

        wbf['content_number'] = workbook.add_format(
            {'align': 'right', 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()

        wbf['content_percent'] = workbook.add_format(
            {'align': 'right', 'num_format': '0.00%', 'font_name': 'Georgia'})
        wbf['content_percent'].set_right()
        wbf['content_percent'].set_left()

        wbf['total_float'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float'].set_top()
        wbf['total_float'].set_bottom()
        wbf['total_float'].set_left()
        wbf['total_float'].set_right()

        wbf['total_number'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['white_orange'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
        wbf['total_number'].set_top()
        wbf['total_number'].set_bottom()
        wbf['total_number'].set_left()
        wbf['total_number'].set_right()

        wbf['total'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total'].set_left()
        wbf['total'].set_right()
        wbf['total'].set_top()
        wbf['total'].set_bottom()

        wbf['total_float_yellow'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['yellow'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float_yellow'].set_top()
        wbf['total_float_yellow'].set_bottom()
        wbf['total_float_yellow'].set_left()
        wbf['total_float_yellow'].set_right()

        wbf['total_number_yellow'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['yellow'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
        wbf['total_number_yellow'].set_top()
        wbf['total_number_yellow'].set_bottom()
        wbf['total_number_yellow'].set_left()
        wbf['total_number_yellow'].set_right()

        wbf['total_yellow'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['yellow'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total_yellow'].set_left()
        wbf['total_yellow'].set_right()
        wbf['total_yellow'].set_top()
        wbf['total_yellow'].set_bottom()

        wbf['total_float_orange'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['orange'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float_orange'].set_top()
        wbf['total_float_orange'].set_bottom()
        wbf['total_float_orange'].set_left()
        wbf['total_float_orange'].set_right()

        wbf['total_number_orange'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['orange'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
        wbf['total_number_orange'].set_top()
        wbf['total_number_orange'].set_bottom()
        wbf['total_number_orange'].set_left()
        wbf['total_number_orange'].set_right()

        wbf['total_orange'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['orange'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total_orange'].set_left()
        wbf['total_orange'].set_right()
        wbf['total_orange'].set_top()
        wbf['total_orange'].set_bottom()

        wbf['header_detail_space'] = workbook.add_format({'font_name': 'Georgia'})
        wbf['header_detail_space'].set_left()
        wbf['header_detail_space'].set_right()
        wbf['header_detail_space'].set_top()
        wbf['header_detail_space'].set_bottom()

        wbf['header_detail'] = workbook.add_format({'bg_color': '#E0FFC2', 'font_name': 'Georgia'})
        wbf['header_detail'].set_left()
        wbf['header_detail'].set_right()
        wbf['header_detail'].set_top()
        wbf['header_detail'].set_bottom()

        return wbf, workbook
