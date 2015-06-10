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
from openerp.osv import osv, fields
from openerp import tools
from openerp.tools.translate import _
from openerp.addons.decimal_precision import decimal_precision as dp
from datetime import datetime, timedelta
from openerp.exceptions import Warning

class account_analytic_account(osv.osv):
    _inherit = "account.analytic.account"
    def _is_holiday_pricelist(self,cr,uid,date,account,context={}):
        holidays=account.holidays_calendar_id.holiday_ids
        if holidays:
            for holiday in holidays:
                if holiday.date==date:
                    return True
        return False
    
    def _is_extra_hour_pricelist(self,cr,uid,date,account,start_time,end_time,context={}):
        is_extra=False
        date_number=datetime.strptime(date, '%Y-%m-%d').weekday()
        schedules=account.regular_schedule_id.attendance_ids
        if schedules:
            for schedule in schedules:
                if str(date_number)==schedule.dayofweek:
                    if start_time>=schedule.hour_from and end_time<=schedule.hour_to:
                        is_extra=False
                        break
                    elif start_time>=schedule.hour_to and end_time>schedule.hour_to:
                        is_extra=True
                        break
                    elif start_time<schedule.hour_from and end_time<=schedule.hour_from:
                        is_extra=True
                        break
            else:
                is_extra=False
        else:
            is_extra=False
        return is_extra
            
    def _get_invoice_price(self, cr, uid, account, date,start_time,end_time, product_id,categ_id,qty,service_type,employee_id,factor_id,context = {}):
        timesheet_obj=self.pool.get('hr.analytic.timesheet')
        pricelist_obj=self.pool.get('contract.pricelist')
        issue_obj=self.pool.get('project.issue')
        product_ids=[]
        categ_ids=[]
        amount=0.0
        count_limit=0.0
        count_extra=0.0
        origin_start_time=start_time
        origin_end_time=end_time
        original_quantity=qty

        pricelist_product_ids=pricelist_obj.search(cr,uid,[('contract_id','=', account.id),('product_id','=', product_id)])
        pricelist_category_ids=pricelist_obj.search(cr,uid,[('contract_id','=', account.id),('categ_id','=', categ_id)])
        if pricelist_product_ids or pricelist_category_ids:
            if pricelist_product_ids and pricelist_category_ids:
                pricelist=pricelist_obj.browse(cr, uid, pricelist_product_ids, context=context)
            elif not pricelist_product_ids and pricelist_category_ids:
                pricelist=pricelist_obj.browse(cr, uid, pricelist_category_ids, context=context)
            elif  pricelist_product_ids and not pricelist_category_ids:
                pricelist=pricelist_obj.browse(cr, uid, pricelist_product_ids, context=context)
            for list in pricelist:
                minimun_time_ids=pricelist_obj.search(cr,uid,[('contract_id','=', account.id),('minimum_time','=', list.minimum_time),('technical_rate','=', list.technical_rate),('assistant_rate','=', list.assistant_rate)])
                pricelist_times=pricelist_obj.browse(cr,uid,minimun_time_ids,context=context)
                for pricelist in pricelist_times:
                    if pricelist.pricelist_line_type=='category':
                        categ_ids.append(pricelist.categ_id.id)
                    elif pricelist.pricelist_line_type=='product':
                        product_ids.append(pricelist.product_id.id)
                issues_ids=issue_obj.search(cr,uid,['|',('product_id','in',product_ids),('categ_id','in',categ_ids),('analytic_account_id','=',account.id)])
                timesheets_before_ids=timesheet_obj.search(cr,uid,[('issue_id','in',issues_ids),('date','=',date),('end_time','<=',start_time),('service_type','=',service_type),('employee_id','=',employee_id)],order='end_time desc')
                timesheets_before=timesheet_obj.browse(cr,uid,timesheets_before_ids,context=context)
                timesheets_after_ids=timesheet_obj.search(cr,uid,[('issue_id','in',issues_ids),('date','=',date),('start_time','>=',end_time),('service_type','=',service_type),('employee_id','=',employee_id)],order='start_time asc')
                timesheets_after=timesheet_obj.browse(cr,uid,timesheets_after_ids,context=context)
        
                count_limit+=qty
                if timesheets_before or timesheets_after:
                    for timesheet in timesheets_before:
                        if timesheet.end_time==start_time:
                            count_limit+=timesheet.end_time-timesheet.start_time
                            start_time=timesheet.start_time
                    for timesheet in timesheets_after:
                        if timesheet.start_time==end_time:
                            count_limit+=timesheet.end_time-timesheet.start_time
                            end_time=timesheet.end_time
                    if count_limit<list.minimum_time:
                        qty=qty/count_limit
                else:
                    if qty<list.minimum_time:
                        qty=list.minimum_time
                holiday_state=self._is_holiday_pricelist(cr,uid,date,account,context={})
                if holiday_state==True:
                    if service_type=='expert':
                        amount=(list.technical_rate*list.holiday_multiplier)
                    elif service_type=='assistant':
                        amount=list.assistant_rate*list.holiday_multiplier
                else:
                    if service_type=='expert':
                        rate=list.technical_rate
                    elif service_type=='assistant':
                        rate=list.assistant_rate
                    is_extra=self._is_extra_hour_pricelist(cr,uid,date,account,origin_start_time,origin_end_time,context={})
                    if is_extra==True:
                        count_extra+=original_quantity
                        if timesheets_before or timesheets_after:
                            for timesheet in timesheets_before:
                                if timesheet.end_time==origin_start_time:
                                    if self._is_extra_hour_pricelist(cr,uid,timesheet.date,account,timesheet.start_time,timesheet.end_time,context={})==True:
                                        count_extra+=timesheet.end_time-timesheet.start_time
                                        origin_start_time=timesheet.start_time
                                    else:
                                        is_extra=False
                            for timesheet in timesheets_after:
                                if timesheet.start_time==origin_end_time:
                                    if self._is_extra_hour_pricelist(cr,uid,timesheet.date,account,timesheet.start_time,timesheet.end_time,context={})==True:
                                        count_extra+=timesheet.end_time-timesheet.start_time
                                        origin_end_time=timesheet.end_time
                            if count_extra<1 and is_extra==False:
                                amount=rate
                            elif count_extra>=1:
                                amount=rate*list.overtime_multiplier
                            else:
                                amount=rate*list.overtime_multiplier
                        else:
                            amount=rate*list.overtime_multiplier
                    else:
                        amount=rate
        return qty,amount
    def _analysis_all(self, cr, uid, ids, fields, arg, context=None):
        total=0.0
        res=super(account_analytic_account,self)._analysis_all(cr, uid, ids, fields, arg, context)
        accounts = self.browse(cr, uid, ids, context=context)
        for f in fields:
            if f == 'ca_to_invoice':
                for account in accounts:
                    if account.pricelist_ids:
                        cr.execute("""
                            SELECT line.to_invoice, sum(line.unit_amount), line.name,sheet.issue_id,issue.categ_id,issue.product_id,line.date,sheet.service_type,sheet.start_time,sheet.end_time,sheet.employee_id
                            FROM project_issue issue
                            LEFT JOIN hr_analytic_timesheet sheet on (issue.id=sheet.issue_id)
                            LEFT JOIN account_analytic_line line on (line.id=sheet.line_id)
                            LEFT JOIN account_analytic_journal journal ON (journal.id = line.journal_id)
                            WHERE account_id = %s AND journal.type != 'purchase'
                                  AND line.invoice_id IS NULL
                                  AND to_invoice IS NOT NULL
                            GROUP BY line.to_invoice, line.product_uom_id, line.name,sheet.service_type,line.date,sheet.start_time,sheet.employee_id,sheet.end_time,sheet.issue_id,issue.categ_id,issue.product_id""", (account.id,))
                        for factor_id, qty, line_name, issue_id,categ_id,product_id, date, service_type, start_time,end_time,employee_id in cr.fetchall():
                                factor = self.pool.get('hr_timesheet_invoice.factor').browse(cr,uid,factor_id,context=context)
                                qty,amount=self._get_invoice_price(cr, uid, account, date,start_time,end_time, product_id,categ_id,qty,service_type,employee_id,factor_id,context)
                                total+=qty*amount*(100-factor.factor or 0.0) / 100.0
                        res[account.id][f] = total
        return res

    _columns = {
        'ca_to_invoice': fields.function(_analysis_all, multi='analytic_analysis', type='float', string='Uninvoiced Amount',
            help="If invoice from analytic account, the remaining amount you can invoice to the customer based on the total costs.",
            digits_compute=dp.get_precision('Account')),
        'ca_theorical': fields.function(_analysis_all, multi='analytic_analysis', type='float', string='Theoretical Revenue',
            help="Based on the costs you had on the project, what would have been the revenue if all these costs have been invoiced at the normal sale price provided by the pricelist.",
            digits_compute=dp.get_precision('Account')),
        'hours_quantity': fields.function(_analysis_all, multi='analytic_analysis', type='float', string='Total Worked Time',
            help="Number of time you spent on the analytic account (from timesheet). It computes quantities on all journal of type 'general'."),
        'last_invoice_date': fields.function(_analysis_all, multi='analytic_analysis', type='date', string='Last Invoice Date',
            help="If invoice from the costs, this is the date of the latest invoiced."),
        'last_worked_invoiced_date': fields.function(_analysis_all, multi='analytic_analysis', type='date', string='Date of Last Invoiced Cost',
            help="If invoice from the costs, this is the date of the latest work or cost that have been invoiced."),
        'last_worked_date': fields.function(_analysis_all, multi='analytic_analysis', type='date', string='Date of Last Cost/Work',
            help="Date of the latest work done on this account."),
        'hours_qtt_non_invoiced': fields.function(_analysis_all, multi='analytic_analysis', type='float', string='Uninvoiced Time',
            help="Number of time (hours/days) (from journal of type 'general') that can be invoiced if you invoice based on analytic account."),
        'month_ids': fields.function(_analysis_all, multi='analytic_analysis', type='many2many', relation='account_analytic_analysis.summary.month', string='Month'),
        'user_ids': fields.function(_analysis_all, multi='analytic_analysis', type="many2many", relation='account_analytic_analysis.summary.user', string='User'),
                }
class account_invoice_report(osv.osv):
    _inherit = "account.invoice.report"
    _columns = {
             'porcent_variation_margin': fields.float(string="Variation Margin(%)", readonly=True),
             'variation_margin': fields.float(string="Variation Margin", readonly=True)
             }
    _depends = {
         'account.invoice.line': ['porcent_variation_margin','variation_margin'],
    }
     
    def _select(
         self):
        return  super(account_invoice_report, self)._select() + ", sub.porcent_variation_margin as porcent_variation_margin, sub.variation_margin as variation_margin"
    
    def _sub_select(self):
        return  super(account_invoice_report, self)._sub_select() + ", ail.porcent_variation_margin as porcent_variation_margin, ail.variation_margin as variation_margin"
    
    def _group_by(self):
        return super(account_invoice_report, self)._group_by() + ", ail.porcent_variation_margin, ail.variation_margin"

class ProjectIssue(osv.osv):
    _inherit = 'project.issue'
    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        result={}
        domain=[]
        result = super(ProjectIssue, self).onchange_partner_id(cr, uid, ids, partner_id)
        if partner_id:
            domain.append(('type', '!=', 'view'))
            contract_ids = self.pool.get('account.analytic.account').search(cr,uid,[('partner_id','=',partner_id)])
            if contract_ids:
                domain.append(('partner_id', '=',partner_id))
            if not contract_ids:
                contract_ids = self.pool.get('account.analytic.account').search(cr,uid,[('partner_id','=',False)])
                domain.append(('partner_id', '=',False))
            result['domain']['analytic_account_id']=domain
            if contract_ids:
                result['value']['analytic_account_id']=contract_ids[0]
            else:
                result['value']['analytic_account_id']=False
        return result
    
    def onchange_branch_id(self, cr, uid, ids, branch_id, context=None):
        result={}
        domain=[]
        result = super(ProjectIssue, self).onchange_branch_id(cr, uid, ids, branch_id)
        if branch_id:
            domain.append(('type', '!=', 'view'))
            contract_ids = self.pool.get('account.analytic.account').search(cr,uid,[('branch_ids.id','=',branch_id)])
            if contract_ids:
                domain.append(('branch_ids.id', '=',branch_id))
            if not contract_ids:
                contract_ids = self.pool.get('account.analytic.account').search(cr,uid,[('partner_id','=',False)])
                domain.append(('partner_id', '=',False))
            result['domain']['analytic_account_id']=domain
            if contract_ids:
                result['value']['analytic_account_id']=contract_ids[0]
            else:
                result['value']['analytic_account_id']=False
        return result
class HrAnaliticTimeSheet(osv.osv):
    _inherit = 'hr.analytic.timesheet'
    def is_permited_schedule(self, cr, uid, ids, context=None):
        res=False
        for timesheet in self.browse(cr, uid, ids, context=context):
            date_number=datetime.strptime(timesheet.date, '%Y-%m-%d').weekday()
            schedules=timesheet.account_id.regular_schedule_id.attendance_ids
            if schedules:
                for schedule in schedules:
                    if str(date_number)==schedule.dayofweek:
                        if timesheet.start_time>=schedule.hour_from and timesheet.end_time<=schedule.hour_to:
                            res=True
                            break
                        elif timesheet.start_time>=schedule.hour_to and timesheet.end_time>schedule.hour_to:
                            res=True
                            break
                        elif timesheet.start_time<schedule.hour_from and timesheet.end_time<=schedule.hour_from:
                            res=True
                            break
                        else:
                            res=False
                            break
                    else:
                        res=True
            else:
                res=True
        return res
    _constraints = [
                    (is_permited_schedule, 'Can not mix regular and extra hours. Please check records or enter them separately',['start_time','end_time','date'])
                    ]