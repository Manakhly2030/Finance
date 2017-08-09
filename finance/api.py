import frappe
from frappe import _

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