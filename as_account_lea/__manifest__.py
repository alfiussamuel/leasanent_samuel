# -*- coding: utf-8 -*-
##############################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name' : 'Account Only',
    'version' : '1.0',
    'summary': 'Master Account Only',
    'description': """
        Provide an information about account only
    """,
    'author' : 'Ajeng Shilvie',
    'category': 'Account',
    'depends' : ['account'],
    'data': [
            'security/ir.model.access.csv',
            'views/account_view.xml',
            'wizard/get_accounts_report_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

