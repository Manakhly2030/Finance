# Copyright (c) 2013, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_outstanding_invoices(filters)
	return columns, data

def get_columns():
	return [_("Invoice") + ":Link/Sales Invoice:100",_("Invoice Date")+ ":Date:90",_("Customer") + ":Link/Customer:200",_("Invoice Amt")  + ":Currency:100",
		_("Outstanding Amount") + ":Currency:100"]

def get_outstanding_invoices(filters):
	cond = "1=1"
	if filters.get("customer"):
		cond = "si.customer = %(customer)s"

	return frappe.db.sql(""" 
		select
			si.name, si.posting_date, si.customer, si.rounded_total, si.outstanding_amount
		from 
			`tabSales Invoice` si
		where
			si.outstanding_amount > 0 and si.docstatus = 1 and naming_series != 'SINV-MAC-' and naming_series != 'OMSINV-' and naming_series != 'SINV/MAC/18-19/' and {cond}
	""".format(cond=cond), filters, as_list=1)