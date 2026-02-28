# Copyright (c) 2025, HKM and contributors
# License: MIT. See LICENSE

"""Jinja filters for expense summary templates."""


def indian_currency(value):
	"""Format number in Indian style with comma separators and rupee sign.
	Indian system: 12,34,567.89 (last 3 digits, then groups of 2).
	Returns e.g. '₹ 12,34,567.89' for use in templates.
	"""
	if value is None:
		return "₹ 0.00"
	try:
		num = float(value)
	except (TypeError, ValueError):
		return "₹ 0.00"
	s = f"{num:.2f}"
	if "." in s:
		int_part, dec_part = s.rsplit(".", 1)
	else:
		int_part, dec_part = s, "00"
	sign = ""
	if int_part.startswith("-"):
		sign = "-"
		int_part = int_part[1:]
	if not int_part:
		int_part = "0"
	if len(int_part) <= 3:
		formatted = int_part
	else:
		formatted = int_part[-3:]
		rest = int_part[:-3]
		while rest:
			formatted = rest[-2:] + "," + formatted
			rest = rest[:-2]
	return f"₹ {sign}{formatted}.{dec_part}"
