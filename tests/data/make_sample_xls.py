#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Regenerate ``tests/data/sample.xls``.

The legacy binary .xls format cannot be written by openpyxl, so the fixture is
produced once with ``xlwt`` (a development-only dependency) and committed.

Usage::

    pip install xlwt
    python tests/data/make_sample_xls.py
"""

import os

import xlwt

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "sample.xls")

ROWS = [
    ("Company Name", "Email"),
    ("Acme Corp", "info@acme.example"),
    ("Globex Ltd", "contact@globex.example"),
    ("Initech S.r.l.", "sales@initech.example"),
]


def build() -> None:
    workbook = xlwt.Workbook(encoding="utf-8")
    sheet = workbook.add_sheet("Recipients")
    for row_index, row in enumerate(ROWS):
        for column_index, value in enumerate(row):
            sheet.write(row_index, column_index, value)
    workbook.save(TARGET)
    print(f"Written: {TARGET}")


if __name__ == "__main__":
    build()
