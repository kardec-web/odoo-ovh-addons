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

# Domain
# offer ->
# allowedAccountSize ->
# /email/domain/{domain}/summary
# /email/domain/{domain}/quota


class OVHMailbox(models.Model):
    _inherit = 'it.mailbox'

    last_synchronisation = fields.Datetime()

    @api.model
    def sync_mailboxes_cron(self):

        ovh_credenials = self.env['ovh.credentials'].search(
            [('consumer_key', '!=', False)])

        for ovh_credential in ovh_credenials:
            client = ovh.Client(
                endpoint=ovh_credential.endpoint,
                application_key=ovh_credential.application_key,
                application_secret=ovh_credential.application_secret,
                consumer_key=ovh_credential.consumer_key,
            )

            domains = client.get('/email/domain')
            for cdomain in domains:
                domain = self.env['it.domain'].sudo().search(
                    [('name', '=', cdomain)])

                if domain:
                    domain.write({
                        'has_mailbox': True
                    })
                    ovh_mailboxes = client.get(
                        "/email/domain/%s/account" % cdomain)
                    for ovh_mailbox_name in ovh_mailboxes:

                        ovh_mailbox_data = client.get(
                            "/email/domain/%s/account/%s" % (cdomain, ovh_mailbox_name))
                        ovh_mailbox_usage = client.get(
                            "/email/domain/%s/account/%s/usage" % (cdomain, ovh_mailbox_name))

                        values = {
                            'active': ovh_mailbox_data['isBlocked'] == False,
                            'name': ovh_mailbox_name,
                            'domain': domain.id,
                            'description': ovh_mailbox_data['description'],
                            'last_synchronisation': fields.Datetime.now(),
                            'quota': ovh_mailbox_data['size'] / 1000,
                            'quota_used': (ovh_mailbox_usage['quota'] / 1000) if ovh_mailbox_usage['quota'] else 0,
                            'number_of_emails': ovh_mailbox_usage['emailCount'],
                        }

                        mailbox = self.env['it.mailbox'].sudo().search(
                            [('name', '=', ovh_mailbox_name), ('active', 'in', [True, False])])

                        if mailbox:
                            mailbox.write(values)
                        else:
                            self.env['it.mailbox'].sudo().create(values)
