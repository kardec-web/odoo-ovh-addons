# -*- coding: utf-8 -*-
##############################################################################
#
#    Kardec
#    Copyright (C) 2016-Today Kardec (<http://www.kardec.net>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging

from openerp import models, fields, api

_logger = logging.getLogger(__name__)


class InInvoice(models.Model):
    _inherit = 'account.invoice'

    is_ovh_invoice = fields.Boolean(string="OVH Invoice", index=True)
    ovh_account_id = fields.Many2one('ovh.account', index=True)
    ovh_html_url = fields.Char()
    ovh_pdf_url = fields.Char()
    ovh_order_id = fields.Char()
    ovh_payment_date = fields.Date()
    ovh_payment_identifier = fields.Char()
    ovh_payment_type = fields.Char()

    @api.model
    def fetch_in_invoice_cron(self):
        _logger.info('Fetch OVH In Invoice Cron Start')
        ovh_credenials = self.env['ovh.credentials'].get_credentials(False)

        account_invoice_env = self.env['account.invoice'].sudo()
        account_invoice_line_env = self.env['account.invoice.line'].sudo()

        ovh_partner = self.env.ref('ovh_in_invoice.ovh_partner')
        account_payable_id = ovh_partner.property_account_payable_id.id
        ovh_product = self.env.ref('ovh_in_invoice.ovh_service')
        default_company = self.env.ref('base.main_company')

        client_param = {
            'date.from': self.env['ir.config_parameter'].get_param(
                'ovh.in_voice.from_date')
        }

        purchase_journal = self.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', default_company.id),
        ], limit=1)

        fpos = ovh_partner.property_account_position_id
        line_account = account_invoice_line_env.get_invoice_line_account(
            'in_invoice', ovh_product, fpos, default_company)

        for ovh_credential in ovh_credenials:
            client = ovh_credential.make_client()
            invoices = ovh_credential.ovh_get(
                client, '/me/bill', [], **client_param)

            for invoice in invoices:
                invoice_info = ovh_credential.ovh_get(
                    client, '/me/bill/%s' % invoice)

                bill = account_invoice_env.search([
                    ('reference', '=', invoice_info['billId'])
                ])

                if bill:
                    _logger.info('Vendor Bill %s exist!',
                                 invoice_info['billId'])
                    continue

                values = {
                    'type': 'in_invoice',
                    'is_ovh_invoice': True,
                    'ovh_account_id': ovh_credential.account_id.id,
                    'ovh_html_url': invoice_info['url'],
                    'ovh_pdf_url': invoice_info['pdfUrl'],
                    'reference': invoice_info['billId'],
                    'ovh_order_id': invoice_info['orderId'],
                    'state': 'draft',
                    'date_invoice': invoice_info['date'],
                    'partner_id': ovh_partner.id,
                    'account_id': account_payable_id,
                    'journal_id': purchase_journal.id,
                }

                bill = account_invoice_env.create(values)

                invoice_details = ovh_credential.ovh_get(
                    client,
                    '/me/bill/%s/details' % invoice, [])
                for invoice_detail in invoice_details:
                    detail = ovh_credential.ovh_get(
                        client,
                        '/me/bill/%s/details/%s' % (invoice, invoice_detail))

                    detail_obj = account_invoice_line_env.create({
                        'invoice_id': bill.id,
                        'name': detail['description'],
                        'quantity': detail['quantity'],
                        'price_unit': detail['unitPrice']['value'],
                        'account_id': line_account.id,
                        'product_id': ovh_product.id,
                    })
                    detail_obj._set_taxes()

                invoice_payment = ovh_credential.ovh_get(
                    client,
                    '/me/bill/%s/payment' % invoice)
                if invoice_payment:
                    bill.write({
                        'ovh_payment_date': invoice_payment['paymentDate'],
                        'ovh_payment_identifier': invoice_payment[
                            'paymentIdentifier'],
                        'ovh_payment_type': invoice_payment['paymentType'],
                    })
                else:
                    _logger.info('No payment found')

                bill.action_invoice_open()

                self.env.cr.commit()

        _logger.info('Fetch OVH In Invoice Cron End')
