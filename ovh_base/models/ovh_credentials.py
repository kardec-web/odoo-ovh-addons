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
from openerp.tools.translate import _
from openerp.exceptions import UserError
import openerp.tools as tools

_logger = logging.getLogger(__name__)

try:
    import ovh
    from ovh.exceptions import APIError
except (ImportError, IOError) as err:
    _logger.debug(err)


class OVHCredentials(models.Model):
    _name = 'ovh.credentials'

    name = fields.Char(string="Description", required=True, index=True)
    account_id = fields.Many2one(
        'ovh.account', index=True)
    endpoint = fields.Selection([
        ('ovh-eu', 'OVH Europe API'),
        ('ovh-ca', 'OVH North-America API'),
        ('soyoustart-eu', 'So you Start Europe API'),
        ('soyoustart-ca', 'So you Start North America API'),
        ('kimsufi-eu', 'Kimsufi Europe API'),
        ('kimsufi-ca', 'Kimsufi North America API'),
        ('runabove-ca', 'RunAbove API'),
    ])
    application_key = fields.Char()
    application_secret = fields.Char()
    consumer_key = fields.Char()
    active = fields.Boolean(default=True)
    owner_id = fields.Many2one(
        'res.partner', string="Owner", required=True,
        default=lambda self: self._default_owner())

    @api.model
    def _default_owner(self):
        return self.env.ref('base.main_company').id

    @api.multi
    def generate_consumer_key(self):
        for record in self:
            if not record.endpoint:
                raise UserError(_("You should specify an endpoint!"))
            client = ovh.Client(
                endpoint=record.endpoint,
                application_key=record.application_key,
                application_secret=record.application_secret
            )

            access_rules = [
                {'method': 'GET', 'path': '/*'},
                {'method': 'POST', 'path': '/*'},
                {'method': 'PUT', 'path': '/*'},
                {'method': 'DELETE', 'path': '/*'}
            ]
            try:
                validation = client.request_consumerkey(access_rules)
            except APIError as e:
                raise UserError(tools.ustr(e))

            record.write({
                'consumer_key_status':  validation['state'],
                'consumer_key':  validation['consumerKey'],
            })
            raise UserError(
                _("Please visit\n%s\nto authenticate"
                  "\nConsumer Key: %s\nState:%s" %
                  (
                      validation['validationUrl'],
                      validation['consumerKey'],
                      validation['state']))
            )

    @api.multi
    def test_ovh_connection(self):
        for record in self:

            client = ovh.Client(
                endpoint=self.endpoint,
                application_key=self.application_key,
                application_secret=self.application_secret,
                consumer_key=self.consumer_key,
            )
            try:
                result = client.get('/me')
            except APIError as e:
                "",
                raise UserError(
                    _("Connection Test Failed! Here is"
                        " what we got instead:\n %s") % tools.ustr(e))

            raise UserError(
                _("Connection Test Succeeded!\nWelcome %s\n"
                    "Everything seems properly set up!" % result['firstname']))

    @api.model
    def get_credentials(self):
        return self.env['ovh.credentials'].search(
            [('consumer_key', '!=', False)])

    @api.multi
    def ovh_get(self, client, url, error_return=False, **params):
        self.ensure_one()

        _logger.info('OVH API - GET: %s on %s', url, self.account_id.name)

        try:
            return client.get(url, **params)
        except APIError as e:
            _logger.error(tools.ustr(e))

        return error_return

    @api.multi
    def make_client(self):
        self.ensure_one()

        _logger.info('OVH API - Create CLient: %s', self.account_id.name)

        return ovh.Client(
            endpoint=self.endpoint,
            application_key=self.application_key,
            application_secret=self.application_secret,
            consumer_key=self.consumer_key,
        )
