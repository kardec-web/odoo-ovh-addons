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


class OVHAccount(models.Model):
    _name = 'ovh.account'
    _order = 'name'

    name = fields.Char(string="Nichandle", index=True)
    legal_form = fields.Char()
    state = fields.Char()
    email = fields.Char(string="E-mail")
    phone = fields.Char()
    firstname = fields.Char()
    lastname = fields.Char()
    vat = fields.Char()

    @api.model
    def fetch_ovh_account_cron(self):
        _logger.info('Fetch OVH account Cron Start')
        ovh_credenials = ovh_credenials = self.env[
            'ovh.credentials'].get_credentials()

        ovh_account_env = self.env['ovh.account'].sudo()

        for ovh_credential in ovh_credenials:
            client = ovh_credential.make_client()

            me = ovh_credential.ovh_get(
                client, '/me')
            values = {
                'name': me['nichandle'],
                'legal_form': me['legalform'],
                'state': me['state'],
                'email': me['email'],
                'phone': me['phone'],
                'firstname': me['firstname'],
                'lastname': me['name'],
            }

            ovh_account = ovh_account_env.search(
                [('name', '=', me['nichandle'])])
            if ovh_account:
                ovh_account.write(values)
            else:
                ovh_account_env.create(values)

            ovh_credential.write({
                'account_id': ovh_account.id
            })

        _logger.info('Fetch OVH account Cron End')
