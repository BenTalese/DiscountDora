"""Password policy — FU-442 close-out.

Policy shape follows NIST SP 800-63B (referenced by ISO/IEC 27002:2022
§5.17): minimum 8 characters, no composition rules, reject bundled
breach-list offenders. No admin override.
"""

import pytest

from dora_api.infrastructure.auth_helpers import (
    MIN_PASSWORD_LENGTH,
    PASSWORD_RULES_DOC,
    validate_password,
)


class TestMinimumLength:
    def test_minimum_is_eight_per_nist(self):
        assert MIN_PASSWORD_LENGTH == 8

    def test_rejects_empty(self):
        assert validate_password("") is not None

    def test_rejects_below_minimum(self):
        err = validate_password("abc12")
        assert err is not None
        assert "8 characters" in err

    def test_accepts_exactly_minimum(self):
        # 8 chars, no letters + digits mix required (composition rules gone)
        assert validate_password("aaaaaaaa") is None

    def test_accepts_long_passphrase(self):
        # NIST 800-63B §5.1.1.2: verifiers SHOULD accept ≥ 64.
        # 128-char phrase.
        assert validate_password("correcthorsebatterystaple " * 5) is None


class TestNoCompositionRules:
    """Rules dropped 2026-07-04 (FU-442) — NIST removed them in 2017 for
    real-world entropy reasons."""

    def test_letters_only_ok(self):
        assert validate_password("passphrase") is None

    def test_digits_only_ok(self):
        # Not blocked at policy level. It's a bad password by *entropy*,
        # but composition-rule enforcement pushes users toward predictable
        # substitutions (`Password1!`) which is worse.
        assert validate_password("13579246") is None

    def test_symbols_not_required(self):
        assert validate_password("a whole sentence works") is None


class TestBreachList:
    """Breach-list offenders are rejected outright (case-insensitive) per
    NIST 800-63B §5.1.1.2 ("SHALL check against a list of values known
    to be commonly used, expected, or compromised")."""

    @pytest.mark.parametrize("candidate", [
        # All 8+ chars — the breach-list check kicks in after the length
        # check passes, so shorter entries like "qwerty" are caught by
        # length rather than the deny-list.
        "password", "PASSWORD", "Password123",
        "qwerty123", "12345678", "letmein1", "iloveyou",
        "admin123", "welcome1", "dashydora", "P@ssword",
    ])
    def test_rejects_common_breach_list_entries(self, candidate):
        err = validate_password(candidate)
        assert err is not None, f"expected {candidate!r} to be rejected"
        assert "breach" in err.lower() or "common" in err.lower()

    def test_short_common_password_caught_by_length_first(self):
        # "qwerty" is 6 chars — even without the breach list it fails on
        # length. Ordering is fine; user gets a clear message either way.
        err = validate_password("qwerty")
        assert err is not None

    def test_lookalike_not_in_list_still_ok(self):
        # A near-miss that's not literally in the deny-list passes the
        # policy (entropy is the user's job — we only reject the
        # most-guessed shortlist).
        assert validate_password("passphrase-please") is None


class TestPolicyDoc:
    def test_doc_mentions_current_minimum(self):
        assert "8" in PASSWORD_RULES_DOC

    def test_doc_does_not_promise_composition_rules(self):
        # The doc reads as "at least 8 chars, longer is safer, avoid common"
        # rather than the old "must include a letter and a digit".
        assert "letter and" not in PASSWORD_RULES_DOC
        assert "digit" not in PASSWORD_RULES_DOC.lower()
