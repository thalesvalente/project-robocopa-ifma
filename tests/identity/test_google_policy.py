"""Testes sintéticos da política ID-010, não do Google OAuth/OIDC real."""
import dataclasses
import socket
import subprocess
import unittest
from unittest.mock import patch

from services.identity.google_policy import (
    EnrollmentStatus,
    GoogleAccountKind,
    IdentityPolicyError,
    VerifiedGoogleIdentity,
    classify_google_identity,
)


def verified(**overrides):
    value = dict(
        provider="google",
        provider_sub="108874312345678902221",
        email="learner@gmail.com",
        email_verified=True,
        hosted_domain=None,
    )
    value.update(overrides)
    return VerifiedGoogleIdentity(**value)


def error_code(**values):
    try:
        classify_google_identity(verified(**values))
    except IdentityPolicyError as error:
        return str(error)
    raise AssertionError("identity should be refused")


class GooglePolicyUnitTests(unittest.TestCase):
    def test_personal_gmail_without_hd_can_sign_in_pending(self):
        result = classify_google_identity(verified())
        self.assertEqual(result.account_kind, GoogleAccountKind.PERSONAL_GMAIL)
        self.assertEqual(result.enrollment_status, EnrollmentStatus.PENDING)

    def test_gmail_address_case_and_plus_tag_are_accepted(self):
        result = classify_google_identity(verified(email="Learner+project@GMAIL.com"))
        self.assertEqual(result.account_kind, GoogleAccountKind.PERSONAL_GMAIL)
        self.assertEqual(result.enrollment_status, EnrollmentStatus.PENDING)

    def test_workspace_with_verified_hd_is_pending(self):
        result = classify_google_identity(verified(email="student@school.edu.br", hosted_domain="school.edu.br"))
        self.assertEqual(result.account_kind, GoogleAccountKind.WORKSPACE)
        self.assertEqual(result.enrollment_status, EnrollmentStatus.PENDING)

    def test_other_workspace_domain_can_enter_pending_for_future_school(self):
        result = classify_google_identity(verified(email="student@school-two.edu.br", hosted_domain="another-domain.edu.br"))
        self.assertEqual(result.account_kind, GoogleAccountKind.WORKSPACE)
        self.assertEqual(result.enrollment_status, EnrollmentStatus.PENDING)

    def test_neither_account_type_receives_school_role_or_owner(self):
        for identity in [verified(), verified(email="s@school.edu.br", hosted_domain="school.edu.br")]:
            with self.subTest(email=identity.email):
                outcome = classify_google_identity(identity)
                self.assertEqual([field.name for field in dataclasses.fields(outcome)], ["account_kind", "enrollment_status"])
                self.assertFalse(hasattr(outcome, "school_id"))
                self.assertFalse(hasattr(outcome, "role"))
                self.assertFalse(hasattr(outcome, "owner_ref"))
                self.assertEqual(outcome.enrollment_status, EnrollmentStatus.PENDING)

    def test_google_academic_email_without_verified_hd_not_treated_as_workspace(self):
        self.assertEqual(error_code(email="student@acad.ifma.edu.br"), "GOOGLE_ACCOUNT_UNSUPPORTED")

    def test_gmail_similar_domains_cannot_impersonate_gmail(self):
        for domain in ["gmail.com.evil.example", "mailgmail.com", "gmail.co", "gmail.com-evil.example"]:
            with self.subTest(domain=domain):
                self.assertEqual(error_code(email=f"student@{domain}"), "GOOGLE_ACCOUNT_UNSUPPORTED")

    def test_other_personal_email_google_account_is_out_of_initial_scope(self):
        self.assertEqual(error_code(email="student@yahoo.com"), "GOOGLE_ACCOUNT_UNSUPPORTED")

    def test_unverified_email_refused_for_both_kinds(self):
        for identity in [
            dict(email_verified=False),
            dict(email="s@school.edu.br", hosted_domain="school.edu.br", email_verified=False),
            dict(email_verified=1),
            dict(email_verified="true"),
        ]:
            with self.subTest(identity=identity):
                self.assertEqual(error_code(**identity), "GOOGLE_EMAIL_UNVERIFIED")

    def test_only_google_provider(self):
        for provider in ["email", "facebook", "Google", "", None]:
            with self.subTest(provider=provider):
                self.assertEqual(error_code(provider=provider), "GOOGLE_PROVIDER_REQUIRED")

    def test_subject_is_required_and_not_email(self):
        for subject in ["", "  ", "a b", "\n", None, True, 1234, "a" * 256]:
            with self.subTest(subject=subject):
                self.assertEqual(error_code(provider_sub=subject), "GOOGLE_SUB_INVALID")

    def test_invalid_email_refused_without_reflection(self):
        for email in ["", "notanemail", "a@@gmail.com", " a@gmail.com", "a@gmail.com\n", ".a@gmail.com", "a..b@gmail.com", "a@", "a@gmail.com.", 123, None]:
            with self.subTest(email=email):
                self.assertEqual(error_code(email=email), "GOOGLE_EMAIL_INVALID")

    def test_hd_is_not_permitted_for_gmail_personal(self):
        self.assertEqual(error_code(hosted_domain="school.edu.br"), "GOOGLE_IDENTITY_INCONSISTENT")
        self.assertEqual(error_code(hosted_domain="gmail.com"), "GOOGLE_IDENTITY_INCONSISTENT")

    def test_invalid_hosted_domain_is_denied(self):
        for hd in ["", "school", "bad_school.edu.br", "a..edu.br", "a.edu.br/", "school.edu.br\n", 123, False]:
            with self.subTest(hd=hd):
                self.assertEqual(error_code(email="s@school.edu.br", hosted_domain=hd), "GOOGLE_HD_INVALID")

    def test_hd_gmail_com_is_not_organizational_domain(self):
        self.assertEqual(error_code(email="s@school.edu.br", hosted_domain="gmail.com"), "GOOGLE_IDENTITY_INCONSISTENT")

    def test_untrusted_dict_and_wrong_type_are_rejected(self):
        for identity in [{"provider": "google"}, None, object()]:
            with self.subTest(identity=str(type(identity))):
                with self.assertRaisesRegex(IdentityPolicyError, "^VERIFIED_IDENTITY_REQUIRED$"):
                    classify_google_identity(identity)

    def test_cannot_supply_client_school_role_or_token_in_identity(self):
        with self.assertRaises(TypeError):
            verified(school_id="school-ifma")
        with self.assertRaises(TypeError):
            verified(role="organizer")
        with self.assertRaises(TypeError):
            verified(owner_ref="other-user")
        with self.assertRaises(TypeError):
            verified(jwt="raw-token")

    def test_output_is_immutable(self):
        value = classify_google_identity(verified())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.enrollment_status = "ACTIVE"

    def test_identity_is_immutable(self):
        value = verified()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.hosted_domain = "school.edu.br"

    def test_no_network_or_execution(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("unexpected network")), \
             patch.object(subprocess, "Popen", side_effect=AssertionError("unexpected process")):
            self.assertEqual(classify_google_identity(verified()).enrollment_status, EnrollmentStatus.PENDING)


if __name__ == "__main__":
    unittest.main()
