# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Addons modules by CLEARCORP S.A.
#    Copyright (C) 2009-TODAY CLEARCORP S.A. (<http://clearcorp.co.cr>).
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
    'name': 'Public Budget',
    'version': '0.1',
    'url': 'http://launchpad.net/openerp-ccorp-addons',
    'author': 'ClearCorp S.A.',
    'website': 'http://clearcorp.co.cr',
    'category': 'Generic Modules/Base',
    'description': """ This module adds the logic for Public Budget management and it's different processes
    """,
    'depends': [
        'base',
        'account',
        'purchase',
        'sale',
        'purchase_order_discount',
        'hr_payroll',
        'hr_expense',    
        ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'budget_workflow.xml',
        'budget_view.xml',
        'res_partner_view.xml',
        'wizard/budget_import_catalog_view.xml',
        'security/security.xml',
        'budget_sequence.xml',
        'account_invoice_view.xml',
        'purchase_view.xml',
        'purchase_workflow.xml',
        'sale_view.xml'
        ],
    'license': 'AGPL-3',
    'installable': True,
    'active': False,
    'application': True,

}
