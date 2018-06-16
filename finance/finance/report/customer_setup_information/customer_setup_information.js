// Copyright (c) 2016, FinByz Tech Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer Setup information"] = {
	"filters": [
		{
			fieldname: "ID",
			label: __("ID"),
			fieldtype: "Link",
			options: "Serial No"
		},	
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item"
		},	
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer"
		},
		{
			fieldname: "maintenance_status",
			label: __("Status"),
			fieldtype: "Select",
			options:"\nUnder Warranty\nOut of Warranty\nUnder AMC\nOut of AMC"
		},
	]
}
