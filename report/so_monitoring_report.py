from odoo import models, fields, api
from odoo import tools


# class SoMonitoringReportXLsx(models.AbstractModel):
#     # _name = 'report.usl_service_erp.report_service_order_monitoring_id_xls'
    # _inherit = 'report.report_xlsx.abstract'
    #
    # # exclude_from_invoice_tab = fields.Boolean('Exclude from invoice')
    #
    # def generate_xlsx_report(self, workbook, data, partners):
    #     sheet = workbook.add_worksheet('Monitoring Report')
    #     bold = workbook.add_format({'bold': True})
    #     row = 0
    #     col = 0
    #
    #     sheet.write(row, col, 'Service Number', bold)
    #     sheet.write(row, col + 1, 'Product', bold)
    #     for so_number in data:
    #         print('<><><>>',so_number)
    #         row += 1
    #         sheet.write(row, col, so_number)
    #         # sheet.write(row, col+1, so_number.order_date)
    #
    #     # def init(self):
    # #     tools.drop_view_if_exists(self.env.cr, 'so_monitoring_report')
    # #     self.env.cr.execute("""
    # #         CREATE OR REPLACE VIEW so_monitoring_report AS (
    # #             SELECT
    # #                 row_number() OVER () AS id,
    # #                 # line.product_id,
    # #                 # line.date,
    # #                 # line.quantity,
    # #                 # line.untaxed_total,
    # #                 # line.total,
    # #                 # line.invoice_id,
    # #                 # line.partner_id,
    # #                 # line.user_id,
    # #                 # line.type,
    # #                 # line.state,
    # #                 # line.exclude_from_invoice_tab FROM (
    # #                 #     SELECT
    # #                 #         p.id as product_id,
    # #                 #         am.invoice_date as date,
    # #                 #         (aml.quantity * invoice_type.sign_qty) as quantity,
    # #                 #         (aml.price_subtotal * invoice_type.sign_qty) as untaxed_total,
    # #                 #         (aml.price_total * invoice_type.sign_qty) as total,
    # #                 #         aml.move_id as invoice_id,
    # #                 #         am.partner_id as partner_id,
    # #                 #         am.invoice_user_id as user_id,
    # #                 #         am.type as type,
    # #                 #         am.state as state,
    # #                 #         aml.exclude_from_invoice_tab as exclude_from_invoice_tab
    # #                 #     FROM product_product p
    # #                 #     LEFT JOIN account_move_line aml ON (p.id = aml.product_id)
    # #                 #     LEFT JOIN account_move am ON (aml.move_id = am.id)
    # #                 #     JOIN (
    # #                 #         SELECT id,(CASE
    # #                 #              WHEN am.type::text = ANY (ARRAY['in_refund'::character varying::text, 'in_invoice'::character varying::text])
    # #                 #                 THEN -1
    # #                 #                 ELSE 1
    # #                 #             END) AS sign,(CASE
    # #                 #              WHEN am.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
    # #                 #                 THEN -1
    # #                 #                 ELSE 1
    # #                 #             END) AS sign_qty
    # #                 #         FROM account_move am
    # #                 #     ) AS invoice_type ON invoice_type.id = am.id
    # #                 # ) as line
    # #                 # WHERE
    # #                 #     line.state = 'posted' AND
    # #                 #     not line.exclude_from_invoice_tab AND
    # #                 #     line.type in ('out_invoice', 'out_refund')
    # #             )""")
