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
import os

from fabric.api import task, local


@task
def lint():
    lint_xml()
    lint_flake8()
    lint_odoo_lint()


@task
def lint_flake8():
    print('\033[1;32m• Flake8\033[1;m')
    local("flake8 . --config=.flakerc")


@task
def lint_odoo_lint():
    print('\033[1;32m• pyLinter\033[1;m')
    addons = _get_odoo_addons()

    # invalid-commit: because ovh_in_invoice take a long time on cron
    disable = 'manifest-version-format,rst-syntax-error,missing-readme,'
    'invalid-commit'
    command = "pylint --load-plugins=pylint_odoo -d all -e odoolint" + \
        " %s --disable=%s"

    for addon in addons:
        local(command % (addon, disable))


@task
def lint_xml():
    print('\033[1;32m• XMl Linter\033[1;m')
    local('find . -maxdepth 3 -type f -iname "*.xml" '
          '| xargs -I \'{}\' xmllint -noout \'{}\'')


def _get_odoo_addons():
    addons = []
    for item in os.listdir('.'):
        if not os.path.isfile(item) and not item[0] == '.':
            addons.append('./' + item)
    return addons
