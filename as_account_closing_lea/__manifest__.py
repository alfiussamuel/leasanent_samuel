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
    'name' : 'Account Closing',
    'version' : '1.0',
    'summary': 'Closing per Periods',
    'description': """
        Provide a function to stored balance account per periods and fiscal year
    """,
    'author' : 'Ajeng Shilvie',
    'category': 'Account',
    'depends' : ['as_account_lea','mail'],
    'data': [
            'security/ir.model.access.csv',
            'security/account_closing_security.xml',
            'wizard/account_period_close_view.xml',
            'wizard/account_fiscalyear_close_state.xml',
            'wizard/close_period_view.xml',
            'views/account_fiscalyear.xml',
            'views/account_closing_view.xml',
            'views/account_period.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}


