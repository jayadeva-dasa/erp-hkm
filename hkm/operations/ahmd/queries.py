fetch_donor_query = """
select
	d.id as old_donor_id,
	users.code as llp_preacher,
	salutations.name as salutation,
	d.first_name ,
	d.last_name,
	d.birth_of_date as date_of_birth,
	d.occupation,
	CONCAT(countries.phonecode, right(d.primary_phone, 10)) as mobile1,
	CONCAT(wa_countries.phonecode, right(d.whatsapp_no, 10)) as whatsapp1,
	d.other_phone,
	d.other_email,
	d.primary_email as email1,
	d.pan_number as pan_no,
	-- Primary Address
	d.primary_address_type,
	d.flatno as primary_address_1,
	d.primary_address as primary_address_2,
	pri_citites.city_name as primary_city,
	pri_states.state_name as primary_state,
	pri_countries.country_name as primary_country,
	d.primary_pincode,
	d.primary_lat,
	d.primary_long,
	-- Secondary Address
	d.secondary_address_type,
	d.flatno_two as secondary_address_1,
	d.secondary_address as secondary_address_2,
	sec_citites.city_name as secondary_city,
	sec_states.state_name as secondary_state,
	sec_countries.country_name as secondary_country,
	d.secondary_pincode,
	d.secondary_lat,
	d.secondary_long,
	-- Address Pref
	d.mailto as pref_address,
	-- Extra
	d.profile,
	-- Patron Info
	d.is_patron,
    d.patron_code,
	d.patron_form,
	d.corpus_form,
	sevas.name as seva_name
from
	donors d
join receipts_masters rm 
on
	rm.donor_patron_id = d.id
left join users
on
	users.id = d.preacher_id
left join salutations
on
	salutations.id = d.salutation
left join countries
on
	countries.id = d.primary_phone_code
left join countries wa_countries
on
	wa_countries.id = d.whatsapp_no_code
	-- Cities Join
left join cities pri_citites
on
	pri_citites.id = d.primary_city
left join cities sec_citites
on
	sec_citites.id = d.secondary_city
	-- States Join
left join states pri_states
on
	pri_states.id = d.primary_state
left join states as sec_states
on
	sec_states.id = d.secondary_state
	-- Country Join
left join countries pri_countries
on
	pri_countries.id = d.primary_country
left join countries sec_countries
on
	sec_countries.id = d.secondary_country
	-- Seva join
left join sevas 
	on
	sevas.id = d.seva_code
where
	1
	# d.patron_code is null or d.patron_code not in ()
group by
	d.id
    """


seva_subtype_fetch = """
select
	sevas.name as seva,
	sevas.amount,
	sevas1.name as parent
from
	sevas
left join sevas sevas1
on
	sevas1.id = sevas.parent_seva_id
where
	(sevas.name != 'Patronship')
	and (sevas.parent_seva_id not in (156,187))
order by
	sevas.parent_seva_id
"""
avoid_to_make_patrons = [
    "PR11007559",
    "PR11007311",
    "PR11007295",
    "PR11006540",
    "PR11005900",
    "PR11005433",
    "PR11004897",
    "PR11004172",
    "PR11004029",
    "PR11003864",
    "PR11003234",
    "PR11002950",
    "PR11002743",
    "PR11002700",
    "PR11002656",
    "PR11002322",
    "PR11002232",
    "PR11002229",
    "PR11002058",
    "PR11002014",
    "PR11001979",
    "PR11001889",
    "PR11001888",
    "PR11001882",
    "PR11001848",
    "PR11001802",
    "PR11001764",
    "PR11001732",
    "PR11001692",
    "PR11001666",
    "PR11001658",
    "PR11001614",
    "PR11001476",
    "PR11001470",
    "PR11001346",
    "PR11001345",
    "PR11001339",
    "PR11001331",
    "PR11001303",
    "PR11001263",
    "PR11001259",
    "PR11001220",
    "PR11001203",
    "PR11001127",
    "PR11001112",
    "PR11000952",
    "PR11000940",
    "PR11000724",
    "PR11000646",
    "PR11000619",
    "PR11000584",
    "PR11000364",
    "PR11000077",
    "PR11000071",
]

upload_receipts_query = """
select
	rm.id as old_dr_no,
	rm.donor_patron_id as donor_id,
	users.code as preacher,
	sevas.name as seva_subtype,
	sevas.id as seva_id,
	sevas.parent_seva_id as parent_seva_id,
	rm.donation_date as receipt_date,
	rm.donation_amount as amount,
	payments.name as payment_method,
	-- Cheque Details
	rm.cheque_no as cheque_number,
	rm.cheque_date as cheque_date,
	rm.bank_ifsc as ifsc_code,
	rm.bank_name as bank_name,
	rm.transaction_id as remarks,
	rm.remark as user_remarks,
	rm.ddf_image as payment_screenshot,
	rm.sevak_name as sevak_name,
	rm.tax_exemption_receipt as atg_required,
	rm.tag_id as tag_id,
	rm.deleted_at as cancelled
from
	receipts_masters rm
left join sevas
on
	rm.seva_id = sevas.id
join users
on
	users.id = rm.preacher_id
join payments
on
	payments.id = rm.payment_id
where
	1
order by receipt_date
"""

patron_seva_ids = [187, 188, 189, 190, 156, 157, 158, 159, 160, 161, 162]

festival_parent_ids = [
    1,
    2,
    10,
    19,
    34,
    43,
    50,
    81,
    88,
    98,
    107,
    117,
    141,
    145,
    152,
    193,
    202,
    208,
]


relation_company_patron = {
    "7393": "7408",
    "7208": "4800",
    "6464": "7223",
    "5830": "6585",
    "4835": "2711",
    "3989": "3378",
    "3825": "11615",
    "2714": "11590",
    "2628": "2375",
    "2299": "11585",
    "2210": "11586",
    "2207": "2307",
    "2037": "3378",
    "1870": "47",
    "1864": "11579",
    "1787": "3221",
    "1751": "1853",
    "1720": "11593",
    "1658": "11472",
    "1463": "1908",
    "1339": "6232",
    "1332": "11453",
    "1324": "11605",
    "1257": "11578",
    "1253": "11451",
    "1215": "1875",
    "1198": "6160",
    "1107": "11452",
    "947": "11454",
    "935": "11607",
    "722": "5588",
    "69": "11439",
}

upload_general_receipts_query = """
select
	rm.id as original_id,
	CONCAT("GR",rm.id) as dr_no,
	-- Extra
	rm.name as donor_name,
	rm.email,
	rm.phone_number as mobile,
	rm.address,
	rm.pincode,
	rm.pan_no,
	-- Extra
	users.code  as preacher,
	sevas.name as seva_subtype,
	sevas.id as seva_id,
	sevas.parent_seva_id as parent_seva_id,
	rm.donation_date as date,
	rm.donation_amount as amount,
	payments.name as payment_method,
	CONCAT(rm.transaction_number," on ",rm.transaction_date)  as remarks,
	rm.remark as user_remarks
from
	general_receipts rm
left join users
on
	users.id  = rm.created_by
left join sevas
on
	rm.seva_id = sevas.id
join payments
on
	payments.id = rm.payment_id
where
1
-- 	rm.email LIKE '%mailforkaofficial@gmail.com%'
order by date
"""
