import json
import frappe
import requests


class ERPConnection(object):
    def __init__(self):
        self.destination = "https://pb.vcmerp.in"
        self.key = "86eec78dd2ef82e"
        self.secret = "143f9867f3e824b"

    def test(self):
        # test_r = self.get_doctype_list("Seva Type")
        # print(test_r)
        response = requests.get(
            self.destination + f"/api/method/frappe.auth.get_logged_user",
            headers=frappe._dict(Authorization=f"token {self.key}:{self.secret}"),
            params={},
        )
        print(response.text)

    def create_doc(self, doctype, data):

        response = requests.post(
            self.destination + f"/api/method/vcm.migration.operations.create_doc",
            headers=frappe._dict(Authorization=f"token {self.key}:{self.secret}"),
            data=json.dumps(data, indent=4, sort_keys=True, default=str),
        )
        print(response.text)
        r = json.loads(response.text)
        if "exception" in r:
            print(r["exception"])

    def create_doc_with_file(self, data, files={}):
        # print(data)
        response = requests.post(
            self.destination
            + f"/api/method/vcm.migration.operations.create_doc_with_file",
            headers=frappe._dict(Authorization=f"token {self.key}:{self.secret}"),
            data=json.dumps(data),
            files=files,
        )
        print(response.text)
        r = json.loads(response.text)
        if "exception" in r:
            print(r["exception"])

    def api_create(self, doctype, data):
        response = requests.get(
            self.destination + f"/api/resource/{doctype}",
            headers=frappe._dict(Authorization=f"token {self.key}:{self.secret}"),
            data=json.dumps(data, indent=4, sort_keys=True, default=str),
        )
        print(response.text)
        return response

    # def api_create(self, method, params={}):
    #     response = requests.get(
    #         self.destination + f"/api/method/{method}",
    #         headers=frappe._dict(Authorization=f"token {self.key}:{self.secret}"),
    #         params=params,
    #     )
    #     return response

    # def get_doctype_list(self, doctype):
    #     response = requests.get(
    #         self.source
    #         + f"/api/resource/{doctype}?fields=['*']&limit_page_length=10000000000",
    #         headers=frappe._dict(Authorization=f"token {self.key}:{self.secret}"),
    #     )
    #     print(response.text)
    #     return json.loads(response.text)

    # def upload_media(self, data):

    #     response = requests.post(
    #         self.destination + f"/api/method/vcm.migration.operations.create_doc",
    #         headers=frappe._dict(Authorization=f"token {self.key}:{self.secret}"),
    #         data=json.dumps(data, indent=4, sort_keys=True, default=str),
    #     )

    #     r = json.loads(response.text)
    #     if "exception" in r:
    #         print(r["exception"])
