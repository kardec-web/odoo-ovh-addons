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

{
    'name': 'OVH Fetch Hosting',
    'category': 'Tools',
    'summary': 'Fetch your Hosting.',
    'version': '10.0.1.0.0',
    'license': 'GPL-3',
    'author': 'Kardec',
    'website': 'https://www.kardec.net',
    'depends': [
        'ovh_base',
        'it_hosting',
    ],
    'data': [
        'data/scheduler.xml',
        'views/it_hosting.xml',
    ],
    'application': True,
    'external_dependencies': {
        # pip install ovh
        'python': ['ovh'],
    }
}
