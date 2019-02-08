# Copyright (c) 2013, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _


def execute(filters=None):
	if not filters: filters = {}
	salary_slips = get_salary_slips(filters)
	columns = get_columns()
	expense_amounts = get_expense_amounts(salary_slips, filters)
	employee_invoices = get_employee_invoices(salary_slips, filters)

	data = []
	for ss in salary_slips:
		row = [ss.employee, ss.employee_name, ss.gross_pay]
		expense_amount = expense_amounts.get(ss.employee, 0.0)
		row.append(expense_amount)
		row.append(expense_amount + ss.gross_pay)
		row.append(employee_invoices.get(ss.employee, 0.0))

		data.append(row)

	return columns, data

def get_columns():
	columns = [
		_("Employee") + ":Link/Employee:120",
		_("Employee Name") + "::140",
		_("Gross Pay") + ":Currency:120",
		_("Expense Amount") + ":Currency:120",
		_("Total Amount") + ":Currency:120",
		_("No. of Invoices") + ":Int:100",
	]

	return columns

def get_salary_slips(filters):
	filters.update({"from_date": filters.get("date_range")[0], "to_date":filters.get("date_range")[1]})
	conditions = get_conditions(filters)
	salary_slips = frappe.db.sql("""select employee, employee_name, gross_pay from `tabSalary Slip` where docstatus = 1 %s
		order by employee""" % conditions, filters, as_dict=1)

	if not salary_slips:
		frappe.throw(_("No salary slip found between {0} and {1}").format(
			filters.get("from_date"), filters.get("to_date")))
	return salary_slips

def get_conditions(filters):
	conditions = ""
	if filters.get("date_range"): conditions += " and start_date >= %(from_date)s"
	if filters.get("date_range"): conditions += " and end_date <= %(to_date)s"
	if filters.get("company"): conditions += " and company = %(company)s"
	if filters.get("employee"): conditions += " and employee = %(employee)s"

	return conditions

def get_expense_amounts(salary_slips, filters):

	conditions = " and employee in (%s)" % ', '.join(['%s'] * len(salary_slips))
	conditions += " and posting_date between '%(from_date)s' and '%(to_date)s' " % filters

	expense_amounts = frappe.db.sql("""select employee, sum(total_sanctioned_amount) as expense_amount from `tabExpense Claim` 
		where approval_status = 'Approved' and docstatus = 1 %s group by employee""" % conditions, 
		tuple([d.employee for d in salary_slips]), as_dict=1)

	expense_map = {}

	for exp in expense_amounts:
		expense_map.setdefault(exp.employee, exp.expense_amount)

	return expense_map

def get_employee_invoices(salary_slips, filters):
	
	conditions = " and employee_name in (%s)" % ', '.join(['%s'] * len(salary_slips))
	conditions += " and posting_date between '%(from_date)s' and '%(to_date)s' " % filters

	invoices = frappe.db.sql("""select employee_name, count(*) as count from `tabSales Invoice` 
		where docstatus = 1 %s """ % conditions, tuple([d.employee for d in salary_slips]), as_dict=1)

	invoice_map = {}

	for d in invoices:
		invoice_map.setdefault(d.employee_name, d.count)

	return invoice_map
