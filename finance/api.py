from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_fullname, get_datetime, now_datetime, get_url_to_form, date_diff, add_days,add_months, getdate
from frappe.contacts.doctype.address.address import get_address_display, get_default_address
from frappe.contacts.doctype.contact.contact import get_contact_details, get_default_contact
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, now_datetime
from erpnext.accounts.utils import get_fiscal_year

@frappe.whitelist()
def install_on_submit(self, method):
	add_parts(self, method)

@frappe.whitelist()
def opp_before_save(self,method):
	add_sales_person(self)	
	
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
	
	set_organisation_details(out, party, party_type)
	set_address_details(out, party, party_type)
	set_contact_details(out, party, party_type)
	set_other_values(out, party, party_type)

	return out

def set_organisation_details(out, party, party_type):
	
	organisation = None
	
	if party_type == 'Lead':
		organisation = frappe.db.get_value("Lead", {"name": party.name}, "company_name")
	elif party_type == 'Customer':
		organisation = frappe.db.get_value("Customer", {"name": party.name}, "customer_name")
	elif party_type == 'Supplier':
		organisation = frappe.db.get_value("Supplier", {"name": party.name}, "supplier_name")

	out.update({'organisation': organisation})

def set_address_details(out, party, party_type):
	billing_address_field = "customer_address" if party_type == "Lead" \
		else party_type.lower() + "_address"
	out[billing_address_field] = get_default_address(party_type, party.name)
	
	# address display
	out.address_display = get_address_display(out[billing_address_field])

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

def set_other_values(out, party, party_type):
	# copy
	if party_type=="Customer":
		to_copy = ["customer_name", "customer_group", "territory", "language"]
	else:
		to_copy = ["supplier_name", "supplier_type", "language"]
	for f in to_copy:
		out[f] = party.get(f)
		
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
				"taxes_and_charges",
				"naming_series"
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
def make_meetings(source_name, doctype, ref_doctype, target_doc=None):

	def set_missing_values(source, target):
		target.party_type = doctype
		now = now_datetime()
		if ref_doctype == "Meeting Schedule":
			target.scheduled_from = target.scheduled_to = now
		else:
			target.meeting_from = target.meeting_to = now

	def update_contact(source, target, source_parent):
		if doctype == 'Lead':
			if not source.organization_lead:
				target.contact_person = source.lead_name

	doclist = get_mapped_doc(doctype, source_name, {
			doctype: {
				"doctype": ref_doctype,
				"field_map":  {
					'company_name': 'organisation',
					'name': 'party'
				},
				"field_no_map": [
					"naming_series"
				],
				"postprocess": update_contact
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
			

def add_sales_person(self):
	if self.lead:
		lead = frappe.get_doc('Lead',self.lead)
		lead.sales_person = self.sales_person
		lead.save()
		frappe.db.commit()
	
	
@frappe.whitelist()		
def recalculate_depreciation(doc_name):
	doc = frappe.get_doc("Asset", doc_name)
	# fiscal_year = get_fiscal_year(doc.purchase_date)[0]
	# frappe.errprint(fiscal_year)
	year_end = get_fiscal_year(doc.purchase_date)[2]
	# frappe.errprint(year_end)
	# year_end_date = frappe.db.get_value("Fiscal Year","2017-2018","year_end_date")
	# frappe.errprint(year_end_date)
	useful_life_year_1 = date_diff(year_end,doc.purchase_date)
	
	if doc.schedules[0].depreciation_amount:
		sl_dep_year_1 = round((doc.schedules[1].depreciation_amount * useful_life_year_1)/ 365,2)
		#frappe.errprint(sl_dep_year_1)
		sl_dep_year_last = round(doc.schedules[1].depreciation_amount - sl_dep_year_1,2)
		frappe.db.set_value("Asset", doc_name, "depreciation_method", "Manual")
		frappe.db.set_value("Depreciation Schedule", doc.schedules[0].name, "depreciation_amount", sl_dep_year_1)
		frappe.db.set_value("Depreciation Schedule", doc.schedules[0].name, "accumulated_depreciation_amount", sl_dep_year_1)
		total_depre = len(doc.get('schedules'))
		if (doc.total_number_of_depreciations >= len(doc.get('schedules'))):
			fields =dict(
				schedule_date = add_months(doc.next_depreciation_date, doc.total_number_of_depreciations*12),
				depreciation_amount = sl_dep_year_last,
				accumulated_depreciation_amount = doc.gross_purchase_amount - doc.expected_value_after_useful_life,
				parent = doc.name,
				parenttype = doc.doctype,
				parentfield = 'schedules',
				idx = len(doc.get('schedules'))+1	
			)
			schedule = frappe.new_doc("Depreciation Schedule")
			schedule.db_set(fields, commit=True)
			schedule.insert(ignore_permissions=True)
			schedule.save(ignore_permissions=True)
			frappe.db.commit
			doc.reload()
		else:
			frappe.db.set_value("Depreciation Schedule", doc.schedules[(len(doc.get('schedules')))-1].name, "depreciation_amount", sl_dep_year_last)
			frappe.db.commit	
		return sl_dep_year_1