from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.contacts.doctype.contact.contact import get_contact_details, get_default_contact


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
