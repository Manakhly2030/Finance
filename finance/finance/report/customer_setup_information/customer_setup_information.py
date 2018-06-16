# Copyright (c) 2013, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import re
from frappe import _, db
from frappe.contacts.doctype.address.address import get_default_address

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data
	
def get_columns():
	columns = [
		_("ID") + ":Link/Serial No:120",
		_("Item Code") + ":Link/Item:190",
		_("Customer") + ":Link/Customer:190",
		_("Maintenance Status") + ":Data:170",
		_("Warranty Expiry Date") + ":Date:130",
		_("City") + ":Data:80"
	]
	return columns
	
def get_data(filters):

	conditions = get_conditions(filters)

	data = db.sql("""
			select
				name as 'ID' , item_code as 'Item Code', customer as 'Customer', maintenance_status as 'Maintenance Status', warranty_expiry_date as 'Warranty Expiry Date'
			from
				`tabSerial No`
			{}""".format(conditions), as_dict=1)
			
	for row in data:	
		address = get_default_address('Customer',row['Customer'])
		city = db.get_value("Address",address,'city')
		row["City"] = city or ''
		
	return data	

def get_conditions(filters):
	
	#conditions = ''
	conditions = list()
	if filters.name:
		conditions.append("name = '%s' " % filters.name)
	if filters.item_code:
		conditions.append("item_code = '%s' " % filters.item_code.replace("'","\'"))
	if filters.maintenance_status:
		conditions.append("maintenance_status = '%s' " % filters.maintenance_status)
	if filters.customer:
		conditions.append("customer = '%s' " % filters.customer.replace("'", "\'"))
	
	conditions = conditions and " where %s" % " and ".join(conditions) or ''
	
	# conditions += filters.name and " and name = '%s' " % filters.name or ''
	# conditions += filters.item_code and " and item_code = '%s' " % filters.item_code.replace("'","\'") or ''
	# conditions += filters.maintenance_status and " and maintenance_status = '%s' " % filters.maintenance_status or ''
	# conditions += filters.customer and " and customer = '%s' " % filters.customer.replace("'", "\'") or ''
	
	return conditions