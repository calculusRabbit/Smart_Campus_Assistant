import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from services import institution_identity as identity
from services import verification_service as service

IDENTITY = {"domains": ["example.edu"], "name": "Example University"}
SCHOOL = {"school_id": 7, "scorecard_id": 1}
USER = {"username": "student_1", "student_id": 1}


def entity(**changes):
    return {
        "entityID": "urn:example:idp",
        "country": "US",
        "type": "live",
        "scopes": ["example.edu"],
    } | changes


class EntityScopeTests(unittest.TestCase):
    def test_scope_alone_matches(self):
        with patch.object(identity, "_get_entity", return_value=entity()):
            self.assertTrue(identity.entity_matches(IDENTITY, "urn:example:idp"))

    def test_wrong_or_bare_scope_fails(self):
        for scopes in (["other.edu"], ["edu"]):
            with patch.object(identity, "_get_entity", return_value=entity(scopes=scopes)):
                self.assertFalse(identity.entity_matches(IDENTITY, "urn:example:idp"))

    def test_search_does_not_send_premium_limit(self):
        identity._search_universities.cache_clear()
        with (
            patch.object(identity.httpx, "get") as get,
            patch.dict(identity.os.environ, {"API_NINJAS_API_KEY": "test-key"}),
        ):
            get.return_value.json.return_value = []
            identity._search_universities("example", 1)
        self.assertNotIn("limit", get.call_args.kwargs["params"])


class RoleTests(unittest.TestCase):
    def test_staff_affiliation(self):
        for roles in ({"faculty"}, {"staff", "member"}, {"employee"}):
            self.assertTrue(service.staff_affiliation(roles))

    def test_student_worker_and_unknown_roles_pass(self):
        for roles in ({"student", "employee", "member"}, {"student"}, set()):
            self.assertFalse(service.staff_affiliation(roles))

    def test_first_last_email_is_not_a_staff_signal(self):
        self.assertEqual(service.staff_reasons("jane.doe@example.edu"), [])
        self.assertEqual(service.staff_reasons("payroll@example.edu"), ["payroll"])


class StudidTests(unittest.TestCase):
    def test_parse_normalizes_roles(self):
        parsed = service._parse_studid_session(
            {"entityId": "e", "authIdentifier": None, "affiliations": ["Student@x.edu", "member"]}
        )
        self.assertEqual(parsed["roles"], ["member", "student"])

    def test_parse_rejects_bad_shapes(self):
        for bad in (
            {"entityId": ""},
            {"entityId": "e", "authIdentifier": 5},
            {"entityId": "e", "affiliations": [1]},
        ):
            with self.assertRaises(HTTPException):
                service._parse_studid_session(bad)

    def test_unmatched_entity_stores_nothing(self):
        conn = MagicMock()
        parsed = {"entity_id": "e", "identifier": None, "roles": ["staff"]}
        result = service._apply_studid(conn, 1, SCHOOL, parsed, False)
        self.assertTrue(result["email_required"])
        conn.execute.assert_not_called()

    def test_email_shaped_identifier_still_requires_otp(self):
        parsed = {"entity_id": "e", "identifier": "a@example.edu", "roles": ["student"]}
        with patch.object(service, "_pending_manual", return_value=False):
            result = service._apply_studid(MagicMock(), 1, SCHOOL, parsed, True)
        self.assertTrue(result["email_required"])
        self.assertNotIn("approved", result)

    def test_return_url_is_https(self):
        self.assertTrue(service.STUDID_RETURN_URL.startswith("https://"))


class SendOrderTests(unittest.TestCase):
    def context(self, order):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = None
        manager = MagicMock()
        manager.__enter__.return_value = conn
        manager.__exit__.side_effect = lambda *args: order.append("commit") or False
        return manager, conn

    def test_email_is_sent_after_commit(self):
        order = []
        manager, _ = self.context(order)
        with (
            patch.object(service, "get_connection", return_value=manager),
            patch.object(service, "_school_identity", return_value=(SCHOOL, IDENTITY)),
            patch.object(service, "_lock_account"),
            patch.object(service, "school_for", return_value=SCHOOL),
            patch.object(service, "send_email", side_effect=lambda *a: order.append("send")),
        ):
            result = service.start_otp(USER, "student@example.edu")
        self.assertTrue(result["sent"])
        self.assertEqual(order, ["commit", "send"])

    def test_failed_send_consumes_code_without_manual_review(self):
        manager, conn = self.context([])
        with (
            patch.object(service, "get_connection", return_value=manager),
            patch.object(service, "_school_identity", return_value=(SCHOOL, IDENTITY)),
            patch.object(service, "_lock_account"),
            patch.object(service, "school_for", return_value=SCHOOL),
            patch.object(service, "send_email", side_effect=HTTPException(503, "down")),
        ):
            result = service.start_otp(USER, "student@example.edu")
        self.assertFalse(result["sent"])
        self.assertIn("consumed = TRUE", conn.execute.call_args_list[-1].args[0])

    def test_wrong_domain_rejected_before_database_access(self):
        with (
            patch.object(service, "get_connection") as connect,
            patch.object(service, "_school_identity", return_value=(SCHOOL, IDENTITY)),
        ):
            with self.assertRaises(HTTPException):
                service.start_otp(USER, "student@other.edu")
        connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()