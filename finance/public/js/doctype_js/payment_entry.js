frappe.ui.form.on('Payment Entry', {
	party: function(frm) {
        console.log(frm.doc.party)
		frappe.call({
			method:"finance.party_details.get_party_details",
			args:{
				party: frm.doc.party,
				party_type: frm.doc.party_type
			},
			callback: function(r){
				if(r.message){
					frm.set_value('contact_person', r.message.contact_person)
					frm.set_value('email_id', r.message.contact_email)
					frm.set_value ('party_name', frm.doc.party)
				}
			}
		})
	}})