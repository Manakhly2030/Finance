cur_frm.email_field = "contact_email";
cur_frm.fields_dict.engineer.get_query = function(doc) {
    return {
        filters: {
            "status": "Active",
            "designation": "Service Engineer"
        }
    }
};

cur_frm.add_fetch("engineer", "prefered_email", "engineer_email");

frappe.ui.form.on("Warranty Claim", "issue_type", function(frm) {
    if(frm.doc.issue_type) {
    frappe.model.with_doc("Issue Database", frm.doc.issue_type, function() {
        var qmtable= frappe.model.get_doc("Issue Database", frm.doc.issue_type)
        $.each(qmtable.possible_causes, function(index, row){
            d = frm.add_child("possible_causes");
            d.cause = row.cause;
            d.solution = row.solution;
        cur_frm.refresh_field("possible_causes");
        })
        $.each(qmtable.parts_required, function(index, row){
            d = frm.add_child("parts_required");
            d.part = row.part;
        cur_frm.refresh_field("parts_required");
        })
    msgprint("Possible Reasons and Parts Required for visit Updated as per Issue Type Selection");      
    });
    }
});

frappe.ui.form.on("Warranty Claim",{
    refrsh: function(frm) {
        frappe.dynamic_link = {doc: frm.doc, fieldname: 'customer', doctype: 'Customer'}

        if(!frm.doc.__islocal && frm.doc.status == 'Visit Required') {
            cur_frm.add_custom_button(__('Maintenance Visit'), function(){
                frappe.model.open_mapped_doc({
                    method: "erpnext.support.doctype.warranty_claim.warranty_claim.make_maintenance_visit",
                    frm: cur_frm
                });
            }, __("Make"));
            frm.page.set_inner_btn_group_as_primary(__("Make"));
        }
        else {
            console.log('called')
            cur_frm.remove_custom_button('Maintenance Visit', "Make");
        }
    }
});
