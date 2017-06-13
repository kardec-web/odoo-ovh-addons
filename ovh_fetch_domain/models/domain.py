# -*- coding: utf-8 -*-
import ovh
from openerp import models, fields, api

# https://eu.api.ovh.com/console/#/domain/zone/%7BzoneName%7D#GET


class OVHDomain(models.Model):
    _inherit = 'it.domain'

    is_ovh_domain = fields.Boolean(string="OVH Domain")

    last_synchronisation = fields.Datetime(string="Last Synchronisation")
    # last_ovh_update = fields.Datetime(string="OVH Last Update")
    show_domain_zone = fields.Boolean(string="Show Domain Zone", default=False)
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
