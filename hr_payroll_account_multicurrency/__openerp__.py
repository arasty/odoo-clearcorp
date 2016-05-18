# -*- coding: utf-8 -*-
# © 2016 ClearCorp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'HR Payroll Account MultiCurrency',
    'summary': 'Create journal items in multi-currency',
    'version': '8.0.1.0',
    'category': 'HR',
    'website': 'http://clearcorp.cr',
    'author': 'ClearCorp',
    'license': 'AGPL-3',
    'sequence': 10,
    'application': False,
    'installable': True,
    'auto_install': False,
    'depends': [
        'hr_payroll_multicurrency',
        'hr_payroll_account',
    ],
}
