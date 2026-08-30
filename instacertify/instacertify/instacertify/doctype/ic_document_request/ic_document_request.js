# Copyright (c) Instacertify
frappe.ui.form.on("IC Document Request", {
	refresh(frm) {
		frm.add_custom_button(__("Open Library"), () => {
			frappe.set_route("document-collection-library");
		});
		ic_apply_doc_format_visibility(frm);
	},
	include_company_address: ic_apply_doc_format_visibility,
	include_product_name: ic_apply_doc_format_visibility,
	include_product_model: ic_apply_doc_format_visibility,
	include_product_brand: ic_apply_doc_format_visibility,
	include_data_collection_remarks: ic_apply_doc_format_visibility,
	include_data_fields: ic_apply_doc_format_visibility,
	include_sample_dispatch: ic_apply_doc_format_visibility,
	include_remarks: ic_apply_doc_format_visibility,
});

const IC_DOC_FORMAT_MAP = [
	{ flag: "include_company_address", fields: ["company_address"] },
	{ flag: "include_product_name", fields: ["product_name"] },
	{ flag: "include_product_model", fields: ["product_model"] },
	{ flag: "include_product_brand", fields: ["product_brand"] },
	{ flag: "include_data_collection_remarks", fields: ["data_collection_remarks"] },
	{ flag: "include_data_fields", fields: ["section_data_fields", "data_fields"] },
	{
		flag: "include_sample_dispatch",
		fields: [
			"section_sample",
			"courier_name",
			"tracking_number",
			"column_break_sample",
			"dispatch_date",
			"pod_attachment",
			"sample_dispatch_remarks",
		],
	},
	{ flag: "include_remarks", fields: ["section_notes", "remarks"] },
];

const IC_DOC_PRODUCT_FLAGS = [
	"include_company_address",
	"include_product_name",
	"include_product_model",
	"include_product_brand",
	"include_data_collection_remarks",
];

function ic_format_flag_on(frm, flag) {
	if (!frm.fields_dict[flag]) return true;
	const v = frm.doc[flag];
	if (v === undefined || v === null || v === "") return true;
	return cint(v) === 1;
}

function ic_apply_doc_format_visibility(frm) {
	IC_DOC_FORMAT_MAP.forEach(({ flag, fields }) => {
		const show = ic_format_flag_on(frm, flag);
		fields.forEach((f) => {
			if (frm.fields_dict[f]) frm.toggle_display(f, show);
		});
	});
	const show_product = IC_DOC_PRODUCT_FLAGS.some((f) => ic_format_flag_on(frm, f));
	if (frm.fields_dict.section_data_product) {
		frm.toggle_display("section_data_product", show_product);
	}
	if (frm.fields_dict.column_break_data_2) {
		frm.toggle_display(
			"column_break_data_2",
			ic_format_flag_on(frm, "include_product_model") ||
				ic_format_flag_on(frm, "include_product_brand")
		);
	}
}
