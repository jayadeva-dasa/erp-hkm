import frappe


def execute():
    query = frappe.db.sql(
    """
    SELECT 
        parent,
        role,
        if_owner,
        permlevel,
        COUNT(*) AS duplicate_count
    FROM `tabCustom DocPerm`
    GROUP BY 
        parent, role, if_owner, permlevel
    HAVING COUNT(*) > 1
    """,
    as_dict=1,
    )

    for row in query:
        
        duplicate = frappe.get_all(
            "Custom DocPerm",
            filters={
                "parent": row.parent,
                "role": row.role,
                "if_owner": row.if_owner,
                "permlevel": row.permlevel,
            },
            pluck="name",
        )
        
        select = 0
        read = 0
        write = 0
        create = 0
        delete = 0
        submit = 0
        cancel = 0
        amend = 0
        report = 0
        export_ = 0
        import_ = 0
        share = 0
        print_ = 0
        email = 0
        document_parent = row.parent
        role = row.role
        if_owner = row.if_owner
        permlevel = row.permlevel
        
        for i in duplicate:
            perm = frappe.get_doc("Custom DocPerm", i)
            if perm.get("select") == 1 and select == 0:
                select += 1
            if perm.get("read") == 1 and read == 0:
                read += 1
            if perm.get("write") == 1 and write == 0:
                write += 1
            if perm.get("create") == 1 and create == 0:
                create += 1
            if perm.get("delete") == 1 and delete == 0:
                delete += 1
            if perm.get("submit") == 1 and submit == 0:
                submit += 1
            if perm.get("cancel") == 1 and cancel == 0:
                cancel += 1
            if perm.get("amend") == 1 and amend == 0:
                amend += 1
            if perm.get("report") == 1 and report == 0:
                report += 1
            if perm.get("export") == 1 and export_ == 0:
                export_ += 1
            if perm.get("import") == 1 and import_ == 0:
                import_ += 1
            if perm.get("share") == 1 and share == 0:
                share += 1
            if perm.get("print") == 1 and print_ == 0:
                print_ += 1
            if perm.get("email") == 1 and email == 0:
                email += 1
           
            frappe.delete_doc("Custom DocPerm", i)
            
        custom_docperm = frappe.get_doc(
            {
                "doctype": "Custom DocPerm",
                "parent": document_parent,
                "role": role,
                "if_owner": if_owner,
                "permlevel": permlevel,
                "select": select,
                "read": read,
                "write": write,
                "create": create,
                "delete": delete,
                "submit": submit,
                "cancel": cancel,
                "amend": amend,
                "report": report,
                "export": export_,
                "import": import_,
                "share": share,
                "print": print_,
                "email": email,
            }
        )
        custom_docperm.insert() 
            
                
    frappe.db.commit()  # v16: OK - patch script
