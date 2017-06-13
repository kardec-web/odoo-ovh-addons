# -*- coding: utf-8 -*-
import ovh

from openerp import models, fields, api


class OVHAccount(models.Model):
    _name = 'ovh.account'
    _order = 'name'

    name = fields.Char(string="Nichandle")
    legalform = fields.Char(string="Legal Form")
    state = fields.Char(string="State")
    email = fields.Char(string="E-mail")
    phone = fields.Char(string="Phone")
    firstname = fields.Char(string="Firstname")
    lastname = fields.Char(string="Lastname")
    vat = fields.Char(string="Vat")

    @api.model
    def fetch_ovh_account_cron(self):
        ovh_credenials = self.env['ovh.credentials'].search(
            [('consumer_key', '!=', False)])

        for ovh_credential in ovh_credenials:
            client = ovh.Client(
                endpoint=ovh_credential.endpoint,
                application_key=ovh_credential.application_key,
                application_secret=ovh_credential.application_secret,
                consumer_key=ovh_credential.consumer_key,
            )

            me = client.get('/me')
            values = {
                'name': me['nichandle'],
                'legalform': me['legalform'],
                'state': me['state'],
                'email': me['email'],
                'phone': me['phone'],
                'firstname': me['firstname'],
                'lastname': me['name'],
            }

            ovh_account = self.env['ovh.account'].sudo().search(
                [('name', '=', me['nichandle'])])
            if ovh_account:
                ovh_account.write(values)
            else:
                self.env['ovh.account'].sudo().create(values)

            ovh_credential.write({
                'account': ovh_account.id
            })
