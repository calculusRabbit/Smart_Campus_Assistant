import unittest
from unittest.mock import patch

from fastapi import HTTPException

from services import institution_identity as identity
from services.username_policy import validate_student_username


SCORECARD = {
    "id": 123,
    "name": "Example University",
    "city": "Example",
    "state": "KS",
    "school_url": "www.example.edu",
}

UNIVERSITY = {
    "id": 9,
    "name": "Example University",
    "aliases": ["Example U"],
    "country_code": "US",
    "city": "Example",
    "state": "KS",
    "website": "https://example.edu/",
    "domains": ["example.edu"],
    "status": "active",
}


class IdentityPolicyTests(unittest.TestCase):
    def test_institution_domains(self):
        self.assertTrue(
            identity.domain_matches(
                "students.example.edu",
                ["example.edu"],
            )
        )

        for domain in (
            "notexample.edu",
            "example.edu.attacker.com",
            "example.edu.evil.edu",
        ):
            with self.subTest(domain=domain):
                self.assertFalse(
                    identity.domain_matches(
                        domain,
                        ["example.edu"],
                    )
                )

    def test_bare_edu_is_not_a_trust_anchor(self):
        self.assertFalse(
            identity.domain_matches(
                "attacker.edu",
                ["edu"],
            )
        )

    def test_email_must_match_institution(self):
        with self.assertRaises(HTTPException):
            identity.require_institution_email(
                "student@other.edu",
                UNIVERSITY,
            )

    def test_crosswalk_requires_location_and_website(self):
        self.assertTrue(
            identity.same_institution(
                SCORECARD,
                UNIVERSITY,
            )
        )

        for change in (
            {"city": "Other"},
            {"state": "MO"},
            {"website": "https://other.edu"},
        ):
            with self.subTest(change=change):
                self.assertFalse(
                    identity.same_institution(
                        SCORECARD,
                        UNIVERSITY | change,
                    )
                )

    def test_ambiguous_crosswalk_fails_closed(self):
        candidates = [
            UNIVERSITY,
            UNIVERSITY | {"id": 10},
        ]

        with patch.object(
            identity,
            "search_universities",
            return_value=candidates,
        ):
            with self.assertRaises(HTTPException):
                identity.resolve_identity(SCORECARD)

    def test_entity_comes_from_provider_metadata(self):
        metadata = {
            "entityID": "urn:example:idp",
            "country": "US",
            "type": "live",
            "organizations": [
                {
                    "name": "Example University",
                    "url": "https://example.edu",
                }
            ],
            "scopes": ["example.edu"],
        }

        with patch.object(
            identity,
            "_get_entity",
            return_value=metadata,
        ):
            self.assertTrue(
                identity.entity_matches(
                    UNIVERSITY,
                    "urn:example:idp",
                )
            )

    def test_wrong_entity_scope_fails(self):
        metadata = {
            "entityID": "urn:example:idp",
            "country": "US",
            "type": "live",
            "organizations": [
                {
                    "name": "Example University",
                    "url": "https://example.edu",
                }
            ],
            "scopes": ["other.edu"],
        }

        with patch.object(
            identity,
            "_get_entity",
            return_value=metadata,
        ):
            self.assertFalse(
                identity.entity_matches(
                    UNIVERSITY,
                    "urn:example:idp",
                )
            )


class UsernamePolicyTests(unittest.TestCase):
    def test_forbidden_usernames(self):
        for username in (
            "xAdMiNx",
            "SYSTEM_1",
            "NoTiFiCaTiOn7",
            "notification",
            "F_U_C_K",
            "sh1t123",
            "bitch123",
            "b1tch123",
        ):
            with (
                self.subTest(username=username),
                self.assertRaises(ValueError),
            ):
                validate_student_username(username)

    def test_innocent_usernames(self):
        for username in (
            "classmate",
            "assistant_7",
            "Dickinson",
            "student_1",
        ):
            with self.subTest(username=username):
                self.assertEqual(
                    validate_student_username(username),
                    username,
                )


if __name__ == "__main__":
    unittest.main()