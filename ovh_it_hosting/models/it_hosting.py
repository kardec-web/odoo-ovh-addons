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


class OVHServer(models.Model):
    _inherit = 'it.hosting'

    is_ovh_hosting = fields.Boolean(string="OVH Hosting", index=True)
    last_synchronisation = fields.Datetime()
    ovh_account_id = fields.Many2one('ovh.account', index=True)
    ovh_status = fields.Char(string="Status")
    ovh_offer = fields.Char()

    @api.model
    def fetch_dedicated_hosting_cron(self):
        _logger.info('Fetch OVH Hosting cron Start')
        ovh_credenials = self.env['ovh.credentials'].get_credentials()

        server_ip_env = self.env['it.server.ip'].sudo()
        hosting_env = self.env['it.hosting'].sudo()
        domain_env = self.env['it.domain'].sudo()

        active_domain = [
            '|',
            ('active', '=', True),
            ('active', '=', False),
        ]

        for ovh_credential in ovh_credenials:
            client = ovh_credential.make_client()

            hostings = ovh_credential.ovh_get(
                client, '/hosting/web', [])

            for chosting in hostings:
                values = {
                    'is_ovh_hosting': True,
                    'last_synchronisation': fields.Datetime.now(),
                }
                if ovh_credential.account_id:
                    values['ovh_account_id'] = ovh_credential.account_id.id

                server_infos = ovh_credential.ovh_get(
                    client,
                    "/hosting/web/%s" % chosting)

                domain = domain_env.search([
                    ('name', '=', chosting)
                ] + active_domain)

                if not domain:
                    domain = domain_env.create({
                        'name': chosting
                    })

                values['name'] = chosting
                values['active'] = server_infos['state'] == 'active'
                values['ovh_status'] = server_infos['state']
                values['os'] = server_infos['operatingSystem']
                values['hosting_type'] = 'web'
                values['resource_type'] = server_infos['resourceType']
                values['ovh_offer'] = server_infos['offer']
                values['disk_size'] = int(server_infos['quotaSize']['value'])
                values['domain_id'] = domain.id

                server_extra_infos = ovh_credential.ovh_get(
                    client,
                    "/hosting/web/%s/serviceInfos" % chosting)

                values['date_creation'] = server_extra_infos['creation']
                values['date_expiration'] = server_extra_infos['expiration']

                hosting = hosting_env.search([
                    ('name', '=', chosting)
                ] + active_domain)

                if hosting:
                    hosting.write(values)
                else:
                    hosting = hosting.create(values)

                # Add Links
                clink = server_infos['serviceManagementAccess']
                self._add_links(hosting, clink, server_infos)

                domain.write({
                    'has_hosting': True
                })

                ips = [
                    server_infos['hostingIp'],
                    server_infos['hostingIpv6'],
                ]

                server_ip_env.search([
                    ('hosting_id', '=', hosting.id),
                    ('name', 'not in', ips),
                ] + active_domain).unlink()

                hosting_ips = server_ip_env.search([
                    ('hosting_id', '=', hosting.id),
                ])
                hosting_ips = [hosting_ip.name for hosting_ip in hosting_ips]
                for ip in ips:
                    if ip not in hosting_ips:
                        server_ip_env.create({
                            'name': ip,
                            'hosting_id': hosting.id,
                        })

                domains = ovh_credential.ovh_get(
                    client,
                    "/hosting/web/%s/attachedDomain" % chosting, [])

                for cdomain in domains:
                    domain = domain_env.search([
                        ('name', '=', cdomain)
                    ] + active_domain)
                    if not domain:
                        domain = domain_env.create({
                            'name': cdomain
                        })

                    domain.write({
                        'hosting_id': hosting.id
                    })

        _logger.info('Fetch OVH Hosting cron End')

    @api.model
    def _add_links(self, hosting, clink, server_infos):
        self._add_or_update_link(
            hosting.id,
            'ftp://%s' % clink['ftp']['url'],
            'ftp',
            port=clink['ftp']['port']
        )
        self._add_or_update_link(
            hosting.id,
            clink['http']['url'],
            'http',
            port=clink['http']['port'])

        url = 'ssh %s@%s -p %d' % (
            server_infos['primaryLogin'],
            clink['ssh']['url'],
            clink['ssh']['port']
        )

        self._add_or_update_link(
            hosting.id,
            url,
            'ssh',
            hostname=clink['ssh']['url'],
            port=clink['ssh']['port'],
            user=server_infos['primaryLogin']
        )

    @api.model
    def _add_or_update_link(self, hosting_id, url, protocol, hostname='',
                            port=80, user=''):
        active_domain = [
            '|',
            ('active', '=', True),
            ('active', '=', False),
        ]

        link_env = self.env['it.link'].sudo()
        link = link_env.search([
            ('url', '=', url)
        ] + active_domain)

        if link:
            link.write({
                'url': url,
                'protocol': protocol,
                'hostname': hostname,
                'port': port,
                'user': user,
                'hosting_id': hosting_id,
            })
        else:
            link_env.create({
                'name': url,
                'url': url,
                'protocol': protocol,
                'hostname': hostname,
                'port': port,
                'user': user,
                'hosting_id': hosting_id,
            })
