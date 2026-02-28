# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class AshramLibraryBook(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		book_image: DF.AttachImage | None
		hwjqbduybwq: DF.MarkdownEditor | None
		language: DF.Literal["English", "Hindi", "Kannada", "Other"]
		title: DF.Data
		user: DF.Link | None
	# end: auto-generated types
	pass
