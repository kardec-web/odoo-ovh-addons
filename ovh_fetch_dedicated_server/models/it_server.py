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

# https://eu.api.ovh.com/console/#/dedicated/server/%7BserviceName%7D#GET


class OVHServer(models.Model):
    _inherit = 'it.server'

    is_ovh_server = fields.Boolean(string="OVH Server")
    last_synchronisation = fields.Datetime()
    ovh_account = fields.Many2one('ovh.account', string="Account")
    ovh_status = fields.Char(string="Status")
    ovh_server_id = fields.Char(string="Server Id")
    ovh_monitoring = fields.Char(string="Monitored By OVH")

    @api.model
    def fetch_dedicated_server_cron(self):

        ovh_credenials = self.env['ovh.credentials'].search(
            [('consumer_key', '!=', False)])

        server_ip_env = self.env['it.server.ip'].sudo()
        server_env = self.env['it.server'].sudo()
        domain_env = self.env['it.domain'].sudo()
        for ovh_credential in ovh_credenials:
            client = ovh.Client(
                endpoint=ovh_credential.endpoint,
                application_key=ovh_credential.application_key,
                application_secret=ovh_credential.application_secret,
                consumer_key=ovh_credential.consumer_key,
            )

            servers = client.get('/dedicated/server')
            for cserver in servers:
                values = {
                    'is_ovh_server': True,
                    'last_synchronisation': fields.Datetime.now(),
                }
                if ovh_credential.account:
                    values['ovh_account'] = ovh_credential.account.id

                domain = domain_env.search([
                    ('name', '=', cserver)
                ])
                server = False
                if domain:
                    server = server_env.search(
                        [('technical_domain_id', '=', domain.id)])

                server_infos = client.get(
                    "/dedicated/server/%s" % cserver)

                values['ovh_status'] = server_infos['state']
                values['os'] = server_infos['os']
                values['ovh_server_id'] = server_infos['serverId']
                values['ovh_monitoring'] = server_infos['monitoring']
                values['server_type'] = 'dedicated'

                if server:
                    server.write(values)
                else:
                    domain_id = domain_env.create({
                        'name': cserver,
                        'system': True
                    }).id

                    values['technical_domain_id'] = domain_id
                    values['domain_id'] = domain_id
                    server = server_env.create(values)

                ips = client.get(
                    "/dedicated/server/%s/ips" % cserver)
                server_ip_env.search([
                    ('server_id', '=', server.id),
                    ('name', 'not in', ips),
                ]).unlink()

                server_ips = server_ip_env.search([
                    ('server_id', '=', server.id),
                ])
                server_ips = [server_ip.name for server_ip in server_ips]
                for ip in ips:
                    if ip not in server_ips:
                        server_ip_env.create({
                            'name': ip,
                            'server_id': server.id,
                        })
