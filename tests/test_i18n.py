# Iris — Email Sender
# Copyright (C) 2026 Marco Lombardo
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# Distributed WITHOUT ANY WARRANTY; see LICENSE for the full terms.
# A commercial licence, without the AGPL's obligations, is available for use
# in proprietary or closed-source products — see COMMERCIAL-LICENSE.md.

"""Tests for the translation layer."""

import re

import pytest

from iris import i18n


def test_english_is_the_default():
    assert i18n.DEFAULT_LANGUAGE == "en"
    assert i18n.get_language() == "en"


def test_set_and_get_language():
    assert i18n.set_language("it") == "it"
    assert i18n.get_language() == "it"


@pytest.mark.parametrize("value", ["IT", "it-IT", "it_IT", " it "])
def test_language_codes_are_normalised(value):
    assert i18n.normalize_language(value) == "it"


@pytest.mark.parametrize("value", ["", None, "klingon", "de"])
def test_unknown_languages_fall_back_to_the_default(value):
    assert i18n.normalize_language(value) == i18n.DEFAULT_LANGUAGE


def test_translation_changes_with_the_language():
    i18n.set_language("en")
    assert i18n.t("status.ready") == "Ready"
    i18n.set_language("it")
    assert i18n.t("status.ready") == "Pronto"


def test_placeholders_are_substituted():
    assert i18n.t("status.send_progress", done=3, total=10) == "Sending... 3/10"


def test_unknown_key_returns_the_key():
    assert i18n.t("does.not.exist") == "does.not.exist"


def test_missing_placeholder_does_not_raise():
    # A caller forgetting an argument must not break the interface.
    assert "{" in i18n.t("status.send_progress")


def test_language_choices():
    codes = [code for code, _ in i18n.language_choices()]
    assert codes == ["en", "it"]
    assert i18n.language_name("it") == "Italiano"
    assert i18n.language_name("klingon") == "English"


def test_catalogues_have_the_same_keys():
    """Every language must translate exactly the same set of keys."""
    english = set(i18n.CATALOGUES["en"])
    for code, catalogue in i18n.CATALOGUES.items():
        missing = english - set(catalogue)
        extra = set(catalogue) - english
        assert not missing, f"{code}: missing keys {sorted(missing)}"
        assert not extra, f"{code}: unknown keys {sorted(extra)}"


def test_placeholders_match_across_languages():
    """A translation must not introduce or drop a placeholder."""
    pattern = re.compile(r"\{(\w+)\}")
    for key, english in i18n.CATALOGUES["en"].items():
        expected = set(pattern.findall(english))
        for code, catalogue in i18n.CATALOGUES.items():
            found = set(pattern.findall(catalogue[key]))
            assert found == expected, f"{code}/{key}: placeholders {found} != {expected}"


def test_every_translation_is_non_empty():
    for code, catalogue in i18n.CATALOGUES.items():
        for key, value in catalogue.items():
            assert value.strip(), f"{code}/{key} is empty"


def test_translations_actually_differ():
    """Guard against an untranslated copy-paste of the English catalogue."""
    english = i18n.CATALOGUES["en"]
    italian = i18n.CATALOGUES["it"]
    identical = [key for key in english if english[key] == italian[key]]
    # A few entries legitimately match (LOG, PDF, CSV, ...); most must differ.
    assert len(identical) < len(english) * 0.2
