from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.contacts.doctype.contact.contact import get_contact_details, get_default_contact
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt

@frappe.whitelist()
def install_on_submit(self, method):
	add_parts(self, method)

def add_parts(self, method):
	target_doc = frappe.get_doc("Serial No", self.items[0].serial_no.strip())
	target_doc.dongle_id = self.dongle_id
	target_doc.license_type = self.license_type
	target_doc.valid_up_to = self.valid_up_to
	for li in self.machine_parts: 
		target_doc.append("machine_parts", {
			"part_name": li.part_name,
			"no_of_parts" : li.no_of_parts,
			"serial_no" : li.serial_no,
			"original_serial" : li.serial_no
		})
	target_doc.save()
	frappe.db.commit()
	
@frappe.whitelist()
def get_party_details(party=None, party_type="Lead", ignore_permissions=False):

	if not party:
		return {}

	if not frappe.db.exists(party_type, party):
		frappe.throw(_("{0}: {1} does not exists").format(party_type, party))

	return _get_party_details(party, party_type, ignore_permissions)
	
	
def _get_party_details(party=None, party_type="Lead", ignore_permissions=False):

	out = frappe._dict({
		party_type.lower(): party
	})

	party = out[party_type.lower()]

	if not ignore_permissions and not frappe.has_permission(party_type, "read", party):
		frappe.throw(_("Not permitted for {0}").format(party), frappe.PermissionError)

	party = frappe.get_doc(party_type, party)
	set_contact_details(out, party, party_type)
	return out

def set_contact_details(out, party, party_type):
	out.contact_person = get_default_contact(party_type, party.name)

	if not out.contact_person:
		out.update({
			"contact_person": None,
			"contact_display": None,
			"contact_email": None,
			"contact_mobile": None,
			"contact_phone": None,
			"contact_designation": None,
			"contact_department": None
		})
	else:
		out.update(get_contact_details(out.contact_person))
		
@frappe.whitelist()
def make_purchase_order_for_drop_shipment(source_name, for_supplier, target_doc=None):
	def set_missing_values(source, target):
		target.supplier = for_supplier
		target.apply_discount_on = ""
		target.additional_discount_percentage = 0.0
		target.discount_amount = 0.0

		default_price_list = frappe.get_value("Supplier", for_supplier, "default_price_list")
		if default_price_list:
			target.buying_price_list = default_price_list

		if any( item.delivered_by_supplier==1 for item in source.items):
			if source.shipping_address_name:
				target.shipping_address = source.shipping_address_name
				target.shipping_address_display = source.shipping_address
			else:
				target.shipping_address = source.customer_address
				target.shipping_address_display = source.address_display

			target.customer_contact_person = source.contact_person
			target.customer_contact_display = source.contact_display
			target.customer_contact_mobile = source.contact_mobile
			target.customer_contact_email = source.contact_email

		else:
			target.customer = ""
			target.customer_name = ""

		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	def update_item(source, target, source_parent):
		target.schedule_date = source.delivery_date
		target.qty = flt(source.qty)
		target.stock_qty = (flt(source.qty) - flt(source.ordered_qty)) * flt(source.conversion_factor)

	doclist = get_mapped_doc("Sales Order", source_name, {
		"Sales Order": {
			"doctype": "Purchase Order",
			"field_no_map": [
				"address_display",
				"contact_display",
				"contact_mobile",
				"contact_email",
				"contact_person",
				"taxes_and_charges"
			],
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Sales Order Item": {
			"doctype": "Purchase Order Item",
			"field_map":  [
				["name", "sales_order_item"],
				["parent", "sales_order"],
				["stock_uom", "stock_uom"],
				["uom", "uom"],
				["conversion_factor", "conversion_factor"],
				["delivery_date", "schedule_date"]
			],
			"field_no_map": [
				"rate",
				"price_list_rate"
			],
			"postprocess": update_item,
		}
	}, target_doc, set_missing_values)

	return doclist

@frappe.whitelist()
def get_items(customer):
	
	where_clause = ''
	where_clause += customer and " parent = '%s' " % customer.replace("'", "\'") or ''
	
	return frappe.db.sql("""
		SELECT 
			item_code
		FROM
			`tabCustomer Item`
		WHERE
			%s
		ORDER BY
			idx"""% where_clause, as_dict=1)