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


class OVHAlias(models.Model):
    _inherit = 'it.mailbox.alias'

    ovh_id = fields.Char(index=True)
    last_synchronisation = fields.Datetime()

    @api.model
    def sync_aliases_cron(self):
        ovh_credenials = self.env['ovh.credentials'].search(
            [('consumer_key', '!=', False)])

        it_mailbox_alias_env = self.env['it.mailbox.alias'].sudo()
        it_domain_env = self.env['it.domain'].sudo()

        for ovh_credential in ovh_credenials:
            client = ovh.Client(
                endpoint=ovh_credential.endpoint,
                application_key=ovh_credential.application_key,
                application_secret=ovh_credential.application_secret,
                consumer_key=ovh_credential.consumer_key,
            )

            domains = client.get('/email/domain')
            for cdomain in domains:
                domain = it_domain_env.search(
                    [('name', '=', cdomain)])

                if domain:
                    ovh_alias_ids = client.get(
                        "/email/domain/%s/redirection" % cdomain)

                    for ovh_alias_id in ovh_alias_ids:
                        ovh_alias = client.get(
                            "/email/domain/%s/redirection/%s" %
                            (cdomain, ovh_alias_id))

                        values = {
                            'ovh_id': ovh_alias_id,
                            'last_synchronisation': fields.Datetime.now(),
                            'active': True,
                            'domain': domain.id,
                            'name': ovh_alias['from'].replace(
                                '@' + domain.name, ''),
                            'goto': ovh_alias['to'],
                        }

                        alias = it_mailbox_alias_env.search([
                            ("|"),
                            ('ovh_id', '=', values['ovh_id']),
                            ('name', '=', values['name'])
                        ])

                        if alias:
                            alias.write(values)
                        else:
                            it_mailbox_alias_env.create(values)
