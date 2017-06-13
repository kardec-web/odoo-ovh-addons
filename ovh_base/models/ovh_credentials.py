# -*- coding: utf-8 -*-
import ovh
from ovh.exceptions import (
    APIError
)

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import UserError
import openerp.tools as tools


class OVHCredentials(models.Model):
    _name = 'ovh.credentials'

    name = fields.Char(string="Description", required=True, index=True)
    account = fields.Many2one(
        'ovh.account', string="Account", index=True)
    endpoint = fields.Selection([
        ('ovh-eu', 'OVH Europe API'),
        ('ovh-ca', 'OVH North-America API'),
        ('soyoustart-eu', 'So you Start Europe API'),
        ('soyoustart-ca', 'So you Start North America API'),
        ('kimsufi-eu', 'Kimsufi Europe API'),
        ('kimsufi-ca', 'Kimsufi North America API'),
        ('runabove-ca', 'RunAbove API'),
    ], string="Endpoint")
    application_key = fields.Char(string="Application Key")
    application_secret = fields.Char(string="Application Secret")
    consumer_key = fields.Char(string="Consumer Key")
    consumer_key_status = fields.Char(string="Consumer Key Status")
    active = fields.Boolean('Active', default=True)

    @api.multi
    def generate_consumer_key(self):
        for record in self:
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
                raise UserError(
                    _("%s") % tools.ustr(e))

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
