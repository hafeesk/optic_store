# -*- coding: utf-8 -*-
# Copyright (c) 2019, 9T9IT and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, cint
from functools import partial
from toolz import compose

from optic_store.api.customer import get_user_branch


def before_naming(doc, method):
    naming_series = (
        frappe.db.get_value("Branch", doc.os_branch, "os_sales_invoice_naming_series")
        if doc.os_branch
        else None
    )
    if naming_series:
        doc.naming_series = naming_series


_get_gift_card_amounts = compose(
    sum,
    partial(map, lambda x: x.amount),
    partial(filter, lambda x: x.mode_of_payment == "Gift Card"),
)


def validate(doc, method):
    gift_cards = map(
        lambda x: frappe.get_doc("Gift Card", x.gift_card), doc.os_gift_cards
    )
    map(partial(_validate_gift_card_expiry, doc.posting_date), gift_cards)
    if gift_cards:
        _validate_gift_card_balance(doc.payments, gift_cards)
    if cint(doc.redeem_loyalty_points):
        _validate_loyalty_card_no(doc.customer, doc.os_loyalty_card_no)


def _validate_gift_card_expiry(posting_date, giftcard):
    if giftcard.expiry_date and getdate(giftcard.expiry_date) < getdate(posting_date):
        frappe.throw(_("Gift Card {} has expired.".format(giftcard.gift_card_no)))


def _validate_gift_card_balance(payments, gift_cards):
    get_gift_card_balances = compose(sum, partial(map, lambda x: x.balance))
    if _get_gift_card_amounts(payments) > get_gift_card_balances(gift_cards):
        frappe.throw(_("Gift Card(s) has insufficient balance."))


def _validate_loyalty_card_no(customer, loyalty_card_no):
    if loyalty_card_no != frappe.db.get_value(
        "Customer", customer, "os_loyalty_card_no"
    ):
        frappe.throw(
            _(
                "Loyalty Card No: {} does not belong to this Customer".format(
                    loyalty_card_no
                )
            )
        )


def before_submit(doc, method):
    """
        Service dates are set to None to disable monthly scheduled task
        `erpnext.accounts.deferred_revenue.convert_deferred_revenue_to_income`
    """
    for item in doc.items:
        is_gift_card = frappe.db.get_value("Item", item.item_code, "is_gift_card")
        if is_gift_card:
            item.service_start_date = None
            item.service_end_date = None
            item.service_stop_date = None


def on_submit(doc, method):
    _set_gift_card_validities(doc)
    _set_gift_card_balances(doc)


def _set_gift_card_validities(doc):
    for row in doc.items:
        is_gift_card = frappe.db.get_value("Item", row.item_code, "is_gift_card")
        if is_gift_card and row.serial_no:
            for serial_no in row.serial_no.split("\n"):
                gift_card_no = frappe.db.exists(
                    "Gift Card", {"gift_card_no": serial_no}
                )
                if gift_card_no:
                    gift_card_validity = frappe.db.get_value("Item", row.item_code, "gift_card_validity")
                    frappe.db.set_value(
                        "Gift Card",
                        gift_card_no,
                        "expiry_date",
                        frappe.utils.add_days(
                            doc.posting_date, gift_card_validity
                        ),
                    )


def _set_gift_card_balances(doc, cancel=False):
    amount_remaining = _get_gift_card_amounts(doc.payments)
    gift_cards = map(
        lambda x: frappe.get_doc("Gift Card", x.gift_card), doc.os_gift_cards
    )
    for gift_card in gift_cards:
        if amount_remaining < 0:
            break
        amount = min(
            amount_remaining,
            gift_card.balance if not cancel else gift_card.amount - gift_card.balance,
        )
        frappe.db.set_value(
            "Gift Card",
            gift_card.gift_card_no,
            "balance",
            gift_card.balance - amount if not cancel else gift_card.balance + amount,
        )
        amount_remaining -= amount


def on_cancel(doc, method):
    _set_gift_card_balances(doc, cancel=True)


def before_insert(doc, method):
    if not doc.os_branch:
        doc.os_branch = get_user_branch()
