# -*- coding: utf-8 -*-
"""Tests for the extraction of recipients from documents."""

import os

import pytest

from iris import parsers
from iris.parsers import Recipient


# --------------------------------------------------------------------------
# Address validation
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "value",
    [
        "info@example.com",
        "john.doe@example.co.uk",
        "user+tag@sub.example.org",
        "a@b.io",
    ],
)
def test_valid_addresses(value):
    assert parsers.is_valid_email(value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "not-an-address",
        "info@example",
        "info@example.c",
        "info@@example.com",
        "space inside@example.com",
        # The pre-2.0 pattern ``[A-Z|a-z]{2,}`` wrongly accepted a pipe.
        "info@example.|m",
        "info@example.||",
    ],
)
def test_invalid_addresses(value):
    assert not parsers.is_valid_email(value)


def test_normalize_email():
    assert parsers.normalize_email(" <mailto:info@example.com> ") == "info@example.com"


# --------------------------------------------------------------------------
# Plain text
# --------------------------------------------------------------------------
def test_extraction_from_text_with_separators():
    text = "\n".join(
        [
            "Acme Corp, info@acme.com",
            "Globex Ltd; contact@globex.com",
            "Initech\tsales@initech.com",
            "Umbrella S.r.l. | info@umbrella.it",
        ]
    )
    assert parsers.extract_from_text(text) == [
        Recipient("Acme Corp", "info@acme.com"),
        Recipient("Globex Ltd", "contact@globex.com"),
        Recipient("Initech", "sales@initech.com"),
        Recipient("Umbrella S.r.l.", "info@umbrella.it"),
    ]


def test_address_before_the_company_name():
    text = "info@acme.com; Acme Corp"
    assert parsers.extract_from_text(text) == [Recipient("Acme Corp", "info@acme.com")]


def test_without_separator_the_preceding_text_is_the_company():
    text = "Acme Corp   info@acme.com"
    assert parsers.extract_from_text(text) == [Recipient("Acme Corp", "info@acme.com")]


def test_fallback_to_the_domain_when_no_name_is_found():
    assert parsers.extract_from_text("info@acme.com") == [Recipient("Company Acme", "info@acme.com")]


def test_fallback_company_follows_the_language():
    from iris import i18n

    i18n.set_language("it")
    assert parsers.extract_from_text("info@acme.com") == [
        Recipient("Azienda Acme", "info@acme.com")
    ]


def test_duplicates_are_dropped_keeping_the_first():
    text = "First, info@acme.com\nSecond, INFO@acme.com\nThird, other@acme.com"
    assert parsers.extract_from_text(text) == [
        Recipient("First", "info@acme.com"),
        Recipient("Third", "other@acme.com"),
    ]


def test_lines_without_an_address_are_ignored():
    text = "Document header\nAcme Corp, info@acme.com\n---"
    assert parsers.extract_from_text(text) == [Recipient("Acme Corp", "info@acme.com")]


def test_extraction_from_txt(tmp_path):
    path = tmp_path / "recipients.txt"
    path.write_text("Città Alfa; alfa@example.it\n", encoding="utf-8")
    assert parsers.extract_from_file(str(path)) == [Recipient("Città Alfa", "alfa@example.it")]


def test_txt_with_windows_encoding(tmp_path):
    path = tmp_path / "recipients.txt"
    path.write_bytes("Société Beta; beta@example.fr\n".encode("cp1252"))
    assert parsers.extract_from_file(str(path)) == [Recipient("Société Beta", "beta@example.fr")]


# --------------------------------------------------------------------------
# Tables / spreadsheets
# --------------------------------------------------------------------------
def test_extraction_from_rows_with_a_header():
    rows = [
        ["Company Name", "Email"],
        ["Acme Corp", "info@acme.com"],
        ["Globex Ltd", "contact@globex.com"],
    ]
    assert parsers.extract_from_rows(rows) == [
        Recipient("Acme Corp", "info@acme.com"),
        Recipient("Globex Ltd", "contact@globex.com"),
    ]


def test_extraction_from_rows_with_swapped_columns():
    rows = [
        ["Email", "Company"],
        ["info@acme.com", "Acme Corp"],
    ]
    assert parsers.extract_from_rows(rows) == [Recipient("Acme Corp", "info@acme.com")]


def test_empty_rows_and_rows_without_an_address_are_ignored():
    rows = [[None, None], ["Name only", ""], ["Acme", "info@acme.com"]]
    assert parsers.extract_from_rows(rows) == [Recipient("Acme", "info@acme.com")]


def test_extraction_from_xlsx(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    path = tmp_path / "recipients.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["Company Name", "Email"])
    sheet.append(["Acme Corp", "info@acme.com"])
    sheet.append(["Globex Ltd", "contact@globex.com"])
    workbook.save(path)

    assert parsers.extract_from_file(str(path)) == [
        Recipient("Acme Corp", "info@acme.com"),
        Recipient("Globex Ltd", "contact@globex.com"),
    ]


def test_extraction_from_legacy_xls():
    """The legacy .xls sample must be readable.

    Before the fix it was handed to openpyxl, which does not support the
    binary format, so the analysis always failed.
    """
    pytest.importorskip("xlrd")
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "data", "sample.xls"
    )
    if not os.path.exists(path):
        pytest.skip("sample.xls not available")
    recipients = parsers.extract_from_file(path)
    assert recipients
    assert all(parsers.is_valid_email(recipient.email) for recipient in recipients)


def test_extraction_from_csv(tmp_path):
    path = tmp_path / "recipients.csv"
    path.write_text("Company Name;Email\nAcme Corp;info@acme.com\n", encoding="utf-8")
    assert parsers.extract_from_file(str(path)) == [Recipient("Acme Corp", "info@acme.com")]


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------
def test_extraction_from_pdf_text_on_separate_lines():
    text = "Acme Corp\ninfo@acme.com\nGlobex Ltd\ncontact@globex.com\n"
    assert parsers.extract_from_pdf_text(text) == [
        Recipient("Acme Corp", "info@acme.com"),
        Recipient("Globex Ltd", "contact@globex.com"),
    ]


def test_extraction_from_pdf_same_line():
    text = "Acme Corp   info@acme.com\nGlobex Ltd   contact@globex.com"
    assert parsers.extract_from_pdf_text(text) == [
        Recipient("Acme Corp", "info@acme.com"),
        Recipient("Globex Ltd", "contact@globex.com"),
    ]


def test_pdf_addresses_on_different_lines():
    """Regression: the old implementation always used the first occurrence."""
    text = "Alpha alpha@example.com\nBeta beta@example.com\nGamma gamma@example.com"
    result = parsers.extract_from_pdf_text(text)
    assert [recipient.company for recipient in result] == ["Alpha", "Beta", "Gamma"]


# --------------------------------------------------------------------------
# Dispatcher
# --------------------------------------------------------------------------
def test_unsupported_format(tmp_path):
    path = tmp_path / "document.rtf"
    path.write_text("content", encoding="utf-8")
    with pytest.raises(parsers.UnsupportedFormatError):
        parsers.extract_from_file(str(path))


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        parsers.extract_from_file("/path/that/does/not/exist.txt")
