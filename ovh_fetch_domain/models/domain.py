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
import ovh
from openerp import models, fields, api

# https://eu.api.ovh.com/console/#/domain/zone/%7BzoneName%7D#GET


class OVHDomain(models.Model):
    _inherit = 'it.domain'

    is_ovh_domain = fields.Boolean(string="OVH Domain")

    last_synchronisation = fields.Datetime()
    # last_ovh_update = fields.Datetime(string="OVH Last Update")
    show_domain_zone = fields.Boolean(default=False)
    domain_zone = fields.Text(string="Bind Zone")
    ovh_status = fields.Char(string="Status")
    ovh_creation_date = fields.Date(string="Creation date")
    ovh_account = fields.Many2one('ovh.account', string="Account")

    @api.model
    def fetch_domain_cron(self):

        ovh_credenials = self.env['ovh.credentials'].search(
            [('consumer_key', '!=', False)])

        for ovh_credential in ovh_credenials:
            client = ovh.Client(
                endpoint=ovh_credential.endpoint,
                application_key=ovh_credential.application_key,
                application_secret=ovh_credential.application_secret,
                consumer_key=ovh_credential.consumer_key,
            )
            # /domain/zone/{zoneName}/record

            domains = client.get('/domain/zone')
            for cdomain in domains:
                values = {
                    'is_ovh_domain': True,
                    'last_synchronisation': fields.Datetime.now(),
                }
                if ovh_credential.account:
                    values['ovh_account'] = ovh_credential.account.id

                domain_name = self.env['it.domain'].sudo().search(
                    [('name', '=', cdomain)])

                values['domain_zone'] = client.get(
                    "/domain/zone/%s/export" % cdomain)

                serviceInfos = client.get(
                    "/domain/zone/%s/serviceInfos" % cdomain)

                values['name'] = cdomain
                values['ovh_status'] = serviceInfos['status']
                values['date_expiration'] = serviceInfos['expiration']
                values['ovh_creation_date'] = serviceInfos['creation']

                if domain_name:
                    domain_name.write(values)
                else:
                    self.env['it.domain'].sudo().create(values)
