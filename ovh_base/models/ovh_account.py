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


class OVHAccount(models.Model):
    _name = 'ovh.account'
    _order = 'name'

    name = fields.Char(string="Nichandle")
    legal_form = fields.Char()
    state = fields.Char()
    email = fields.Char(string="E-mail")
    phone = fields.Char()
    firstname = fields.Char()
    lastname = fields.Char()
    vat = fields.Char()

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
                'legal_form': me['legalform'],
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
