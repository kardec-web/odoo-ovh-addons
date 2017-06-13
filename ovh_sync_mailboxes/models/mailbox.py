# -*- coding: utf-8 -*-
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

    last_synchronisation = fields.Datetime(string="Last Synchronisation")

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
