# -*- coding: utf-8 -*-
# Copyright (c) 2017, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_fullname, get_datetime
from frappe.core.doctype.communication.email import make

class Meeting(Document):
	def send_mail(self):
		contact_person = self.contact_person if self.contact_person else 'Sir'
		minutes_message = """<p>Dear {0},</p>
				<p>Greeting from Siddharth Printing Machines Pvt. Ltd.!</p>
				<p>Thank you for sparing your valuable time on {1}</p><br>""".format(contact_person, get_datetime(self.meeting_from).strftime("%A, %d %b %Y"))
				
		minutes_message += self.discussion
				
		if self.actionables:
			actionable_heading = """<br><p>
								<strong>Actionables</strong>
							</p>
							<table border="1" cellspacing="0" cellpadding="0">
								<tbody>
									<tr>
										<td width="45%" valign="top">
											<p>
												<strong>Actionable</strong>
											</p>
										</td>
										<td width="30%" valign="top">
											<p>
												<strong>Responsibility</strong>
											</p>
										</td>
										<td width="25%" valign="top">
											<p>
												<strong>Exp. Completion Date</strong>
											</p>
										</td>
									</tr>"""
									
			actionable_row = """<tr>
									<td width="45%" valign="top"> {0}
									</td>
									<td width="30%" valign="top"> {1}
									</td>
									<td width="25%" valign="top"> {2}
									</td>
								</tr>"""
			
			actionable_rows = ""

			for row in self.actionables:
				actionable_rows += actionable_row.format(row.actionable, row.responsible, row.get_formatted('expected_completion_date'))
				
			actionable_heading += actionable_rows
			actionable_heading += "</tbody></table>"
			minutes_message += actionable_heading
			
		minutes_message += """<p>
			SIDDHARTH PRINTING MACHINES PVT. LTD<br>
			B-105, Titanium City Center, Anand Nagar Road<br>
			Near sachin Tower, Satelite,<br> 
			Ahmedabad-380015 (INDIA)<br>
			MBL. +91 9725801515<br>
			<a href="http://www.teamspm.com">
			www.teamspm.com
			</a><br>
			<a href="http://www.spmpl.in">
			www.spmpl.in
			</a> <br>
			<a href="http://www.siddharthprintingmachines.com">
			www.siddharthprintingmachines.com
			</a>
			</p> """

		subject = "Minutes of the Meeting on Date - {0}".format(get_datetime(self.meeting_from).strftime("%A %d-%b-%Y"))
		
		recipients = self.email_id and self.user + ',' + self.email_id or self.user
		
		cc = None
		if self.mark_cc:
			cc = ",".join([cc.mark_cc for cc in self.mark_cc if cc.mark_cc])

		if recipients:
			make(recipients=recipients,
				cc=cc,
				subject=subject, 
				content=minutes_message,
				sender=frappe.session.user,
				doctype=self.doctype,
				name=self.name,
				send_email=True)

			frappe.msgprint(_("Minutes of the Meeting Sent!"), title="Success", indicator='green')
