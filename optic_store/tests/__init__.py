# -*- coding: utf-8 -*-
# Copyright (c) 2019, 9T9IT and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from toolz import merge

from optic_store.api.install import _setup_accounts


def make_sales_invoices():
    make_users()
    make_companies()
    customer = make_customers()[0]
    items = make_items()
    serial_nos = make_serials()
    records = [
        (
            {"customer": customer.name, "posting_date": "2019-02-28"},
            {
                "company": "Optix",
                "set_posting_time": 1,
                "posting_date": "2019-02-28",
                "due_date": "2019-03-02",
                "items": [
                    {
                        "item_code": items[2].name,
                        "qty": 1,
                        "rate": 100,
                        "conversion_factor": 1,
                        "warehouse": "Stores - O",
                        "cost_center": "Main - O",
                        "enable_deferred_revenue": 1,
                        "serial_no": serial_nos[2].name,
                    },
                    {
                        "item_code": items[3].name,
                        "qty": 1,
                        "rate": 200,
                        "conversion_factor": 1,
                        "warehouse": "Stores - O",
                        "cost_center": "Main - O",
                        "enable_deferred_revenue": 1,
                        "serial_no": serial_nos[1].name,
                    },
                ],
            },
        )
    ]
    return map(lambda x: make_test_doc("Sales Invoice", submit=True, *x), records)


def make_sales_orders():
    make_users()
    make_companies()
    customer = make_customers()[0]
    item = make_items()[0]
    records = [
        (
            {"customer": customer.name, "transaction_date": "2019-02-26"},
            {
                "company": "Optix",
                "delivery_date": "2019-02-28",
                "orx_type": "Contacts",
                "items": [
                    {
                        "item_code": item.name,
                        "qty": 1,
                        "rate": 100,
                        "conversion_factor": 1,
                        "warehouse": "Stores - O",
                    }
                ],
            },
        )
    ]
    return map(lambda x: make_test_doc("Sales Order", submit=True, *x), records)


def make_customers():
    make_branches()
    records = [
        (
            {"customer_name": "Ned Flanders"},
            {
                "type": "Individual",
                "customer_group": "All Customer Groups",
                "territory": "All Territories",
                "branch": "Moe's Tavern",
            },
        )
    ]
    return map(lambda x: make_test_doc("Customer", *x), records)


def make_items():
    records = [
        ({"item_name": "Yellow Frame"}, {"item_group": "Frame"}),
        ({"item_name": "Green Lens"}, {"item_group": "Prescription Lens"}),
        (
            {"item_name": "Gift Card"},
            {
                "item_group": "Products",
                "is_gift_card": 1,
                "gift_card_value": 100,
                "gift_card_validity": 30,
            },
        ),
        (
            {"item_name": "Gift Card Unlimited"},
            {"item_group": "Products", "is_gift_card": 1, "gift_card_value": 200},
        ),
    ]
    return map(lambda x: make_test_doc("Item", *x), records)


def make_serials():
    items = make_items()
    records = [
        ({"serial_no": "GC0001"}, {"item_code": items[2].name}),
        ({"serial_no": "GCU0001"}, {"item_code": items[3].name}),
        ({"serial_no": "GC0002"}, {"item_code": items[2].name}),
    ]
    return map(lambda x: make_test_doc("Serial No", *x), records)


def make_employees():
    make_companies()
    make_users()
    make_branches()
    records = [
        (
            {"user_id": "simpson@optix.com"},
            {
                "first_name": "Homer",
                "last_name": "Simpson",
                "company": "Optix",
                "gender": "Male",
                "date_of_birth": "1956-05-12",
                "date_of_joining": "2010-10-10",
                "branch": "Moe's Tavern",
            },
        )
    ]
    return map(lambda x: make_test_doc("Employee", *x), records)


def make_users():
    records = [
        (
            {"email": "simpson@optix.com"},
            {
                "first_name": "Homer",
                "last_name": "Simpson",
                "roles": [{"role": "Employee"}, {"role": "Sales User"}],
            },
        )
    ]
    return map(lambda x: make_test_doc("User", *x), records)


def make_branches():
    records = [({"branch": "Moe's Tavern"}, {})]
    return map(lambda x: make_test_doc("Branch", *x), records)


def make_companies():
    records = [
        (
            {"company_name": "Optix"},
            {
                "abbr": "O",
                "parent_compnay": None,
                "default_currency": "BHD",
                "country": "Bahrain",
            },
        )
    ]
    companies = map(lambda x: make_test_doc("Company", *x), records)
    map(_setup_accounts, map(lambda x: x.name, companies))
    return companies


def make_test_doc(doctype, exists_dict, args, submit=False):
    name = frappe.db.exists(doctype, exists_dict)
    if name:
        return frappe.get_doc(doctype, name)
    doc = frappe.get_doc(merge({"doctype": doctype}, exists_dict, args)).insert(
        ignore_permissions=True
    )
    if submit:
        doc.submit()
    return doc


def remove_test_doc(doctype, exists_dict):
    name = frappe.db.exists(doctype, exists_dict)
    if name:
        doc = frappe.get_doc(doctype, name)
        if doc.docstatus == 1:
            doc.cancel()
        frappe.delete_doc(doctype, name, ignore_permissions=True)