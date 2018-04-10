# -*- coding: utf-8 -*-
# Copyright (c) 2017, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.core.doctype.communication.email import make
from frappe.utils import get_datetime

class MeetingSchedule(Document):
	def send_invitation(self):
		if not self.email_id:
			msgprint(_("Please enter email id"), title="No Email ID found", indicator='red')
			return
		
		subject = "Meeting Scheduled on %s " % get_datetime(self.scheduled_from).strftime("%A %d-%b-%Y")
		
		make(recipients=self.email_id,
			subject=subject, 
			content=self.invitation_message,
			sender=frappe.session.user,
			doctype=self.doctype, 
			name=self.name,
			send_email=True)
		
		msgprint(_("Mail sent successfully!"), title="Success")

@frappe.whitelist()
def make_meeting(source_name, target_doc=None):	
	doclist = get_mapped_doc("Meeting Schedule", source_name, {
			"Meeting Schedule":{
				"doctype": "Meeting",
				"field_map": {
					"name": "schedule_ref",
					"scheduled_from": "meeting_from",
					"scheduled_to": "meeting_to"
				},
				"field_no_map": {
					"naming_series"
				}
			}
		}, target_doc)

	return doclist