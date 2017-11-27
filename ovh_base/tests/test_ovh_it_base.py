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
from mock import patch
from odoo.tests.common import TransactionCase
import logging
_logger = logging.getLogger(__name__)

try:
    from ovh import Client
except (ImportError, IOError) as err:
    _logger.debug(err)


class OvhItBaseTest(TransactionCase):

    def setUp(self):
        super(OvhItBaseTest, self).setUp()

        self.usersEnv = self.env['res.users']
        self.ovhAccountEnv = self.env['ovh.account']
        self.ovhCredentialsEnv = self.env['ovh.credentials']
        self.group_user_id = self.ref('base.group_user')
        self.group_it_admin_id = self.ref('it_base.it_admin')
        self.main_company_id = self.ref('base.main_company')

        self.credential = self.ovhCredentialsEnv.create({
            'name': 'ovh-eu',
            'endpoint': 'ovh-eu',
            'consumer_key': 'consumer_key'
        })

    @patch.object(Client, 'call')
    def test_fetch_ovh_account_cron(self, m_call):
        '''Test it.link model'''
        self.ovhAccountEnv.fetch_ovh_account_cron()
        self.ovhAccountEnv.fetch_ovh_account_cron()
        get_me_result = self._get__me_call()
        m_call.return_value = get_me_result

        account = self.ovhAccountEnv.search([])

    # ('name', '=', get_me_result['nichandle'])

        print '-----' + str(get_me_result['nichandle']) + '++++'
        self.assertEqual(self.credential.account_id.id, account.id)

    def _get__me_call(self):
        return {
            'firstname': "Customer",
            'vat': "BE0674534534",
            'ovhSubsidiary': "FR",
            'area': "",
            'birthDay': "Invalid date",
            'nationalIdentificationNumber': False,
            'spareEmail': "info@test.com",
            'ovhCompany': "ovh",
            'state': "complete",
            'phoneCountry': "BE",
            'email': "info@test.com",
            'currency': {
                'symbol': "€",
                'code': "EUR",
            },
            'city': "Bruxelles",
            'fax': "",
            'nichandle': "tt5645-ovh",
            'address': "Rue de la montagne, 56",
            'companyNationalIdentificationNumber': False,
            'birthCity': "",
            'country': "BE",
            'language': "fr_FR",
            'organisation': "Company",
            'name': "Customer Name",
            'phone': "+32.1234567",
            'sex': "male",
            'zip': "1000",
            'corporationType': "",
            'customerCode': "0111-11111-11",
            'legalform': "corporation",

        }
