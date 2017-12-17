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

# https://eu.api.ovh.com/console/#/dedicated/server/%7BserviceName%7D#GET
_logger = logging.getLogger(__name__)


class OVHServer(models.Model):
    _inherit = 'it.server'

    is_ovh_server = fields.Boolean(string="OVH Server", index=True)
    last_synchronisation = fields.Datetime()
    ovh_account_id = fields.Many2one(
        'ovh.account', string="Ovh Account", index=True)
    ovh_status = fields.Char(string="Status")
    ovh_server_id = fields.Char(string="Server Id")
    ovh_monitoring = fields.Char(string="Monitored By OVH")

    @api.model
    def fetch_dedicated_server_cron(self):
        _logger.info('Fetch OVH Dedicated server cron Start')
        ovh_credenials = self.env['ovh.credentials'].get_credentials()

        server_ip_env = self.env['it.server.ip'].sudo()
        server_env = self.env['it.server'].sudo()
        domain_env = self.env['it.domain'].sudo()

        for ovh_credential in ovh_credenials:
            client = ovh_credential.make_client()

            servers = ovh_credential.ovh_get(
                client, '/dedicated/server', [])
            for cserver in servers:
                values = {
                    'is_ovh_server': True,
                    'last_synchronisation': fields.Datetime.now(),
                }
                if ovh_credential.account_id:
                    values['ovh_account_id'] = ovh_credential.account_id.id

                domain = domain_env.search([
                    ('name', '=', cserver)
                ])
                server = False
                if domain:
                    server = server_env.search(
                        [('technical_domain_id', '=', domain.id)])

                server_infos = ovh_credential.ovh_get(
                    client,
                    "/dedicated/server/%s" % cserver)

                values['owner_id'] = ovh_credential.owner_id.id
                values['ovh_status'] = server_infos['state']
                values['os'] = server_infos['os']
                values['ovh_server_id'] = server_infos['serverId']
                values['ovh_monitoring'] = server_infos['monitoring']
                values['server_type'] = 'dedicated'

                hardware_infos = ovh_credential.ovh_get(
                    client,
                    "/dedicated/server/%s/specifications/hardware" % cserver,
                    False)

                if hardware_infos:
                    values['cpu'] = hardware_infos['numberOfProcessors']
                    values['memory'] = hardware_infos[
                        'memorySize']['value'] / 1024
                    disk_size = 0
                    for disk_group in hardware_infos['diskGroups']:
                        disk_size += disk_group['diskSize']['value']
                    values['disk'] = disk_size

                values['server_type'] = 'dedicated'

                if server:
                    server.write(values)
                else:
                    domain = domain_env.create({
                        'name': cserver,
                        'system': True
                    })

                    values['technical_domain_id'] = domain.id
                    values['domain_id'] = domain.id
                    server = server_env.create(values)

                domain.write({
                    'has_server': True
                })

                ips = ovh_credential.ovh_get(
                    client,
                    "/dedicated/server/%s/ips" % cserver, [])
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

        _logger.info('Fetch OVH Dedicated server cron End')

    @api.model
    def fetch_vps_server_cron(self):
        _logger.info('Fetch OVH VPS server cron Start')
        ovh_credenials = self.env['ovh.credentials'].get_credentials()

        server_ip_env = self.env['it.server.ip'].sudo()
        server_env = self.env['it.server'].sudo()
        domain_env = self.env['it.domain'].sudo()

        for ovh_credential in ovh_credenials:
            client = ovh_credential.make_client()

            servers = ovh_credential.ovh_get(
                client, '/vps', [])
            for cserver in servers:
                _logger.info('VPS: %s' % cserver)
                values = {
                    'is_ovh_server': True,
                    'last_synchronisation': fields.Datetime.now(),
                }
                if ovh_credential.account_id:
                    values['ovh_account_id'] = ovh_credential.account_id.id

                domain = domain_env.search([
                    ('name', '=', cserver)
                ])
                server = False
                if domain:
                    server = server_env.search(
                        [('technical_domain_id', '=', domain.id)])

                server_infos = ovh_credential.ovh_get(
                    client,
                    "/vps/%s" % cserver)

                distribution_infos = ovh_credential.ovh_get(
                    client,
                    "/vps/%s/distribution" % cserver)

                print str(distribution_infos)

                values['owner_id'] = ovh_credential.owner_id.id
                values['ovh_status'] = server_infos['state']
                values['os'] = distribution_infos['name']
                values['ovh_monitoring'] = server_infos['slaMonitoring']
                values['server_type'] = 'virtual'
                values['cpu'] = server_infos['vcore']
                values['memory'] = server_infos['memoryLimit'] / 1024
                values['disk'] = server_infos['model']['disk']

                if server:
                    server.write(values)
                else:
                    domain = domain_env.create({
                        'name': cserver,
                        'system': True
                    })

                    values['technical_domain_id'] = domain.id
                    values['domain_id'] = domain.id
                    server = server_env.create(values)

                domain.write({
                    'has_server': True
                })

                ips = ovh_credential.ovh_get(
                    client,
                    "/vps/%s/ips" % cserver, [])
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

        _logger.info('Fetch OVH VPS server cron End')
