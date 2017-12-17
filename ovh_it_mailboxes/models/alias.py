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


class OVHAlias(models.Model):
    _inherit = 'it.mailbox.alias'

    ovh_id = fields.Char(index=True)
    last_synchronisation = fields.Datetime()

    @api.model
    def sync_aliases_cron(self):
        _logger.info('Fetch OVH Fetch Mailbox Alias Cron Start')
        ovh_credenials = self.env['ovh.credentials'].get_credentials()

        it_mailbox_alias_env = self.env['it.mailbox.alias'].sudo()
        it_domain_env = self.env['it.domain'].sudo()

        for ovh_credential in ovh_credenials:
            client = ovh_credential.make_client()

            domains = ovh_credential.ovh_get(
                client, '/email/domain', [])
            for cdomain in domains:
                domain = it_domain_env.search(
                    [('name', '=', cdomain)])

                if domain:
                    ovh_alias_ids = ovh_credential.ovh_get(
                        client,
                        "/email/domain/%s/redirection" % cdomain)

                    for ovh_alias_id in ovh_alias_ids:
                        ovh_alias = ovh_credential.ovh_get(
                            client,
                            "/email/domain/%s/redirection/%s" %
                            (cdomain, ovh_alias_id))

                        values = {
                            'ovh_id': ovh_alias_id,
                            'last_synchronisation': fields.Datetime.now(),
                            'active': True,
                            'domain_id': domain.id,
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

        _logger.info('Fetch OVH Fetch Mailbox Alias Cron End')
