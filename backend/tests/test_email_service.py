"""Tests for email_service — HTML builders and structure."""

from app.services.email_service import (
    _build_invitation_html,
    _build_login_security_html,
    _build_reset_html,
)


class TestBuildInvitationHtml:
    def test_contains_org_name(self):
        html = _build_invitation_html("ACME Corp", "https://example.com/invite")
        assert "ACME Corp" in html

    def test_contains_invite_url(self):
        html = _build_invitation_html("Test", "https://daleel.tn/invite?token=abc")
        assert "https://daleel.tn/invite?token=abc" in html

    def test_html_escapes_xss(self):
        html = _build_invitation_html("<script>alert(1)</script>", "https://ok.com")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_contains_expiration_notice(self):
        html = _build_invitation_html("Org", "https://ok.com")
        assert "72 heures" in html

    def test_is_valid_html(self):
        html = _build_invitation_html("Test", "https://ok.com")
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html


class TestBuildResetHtml:
    def test_contains_reset_url(self):
        html = _build_reset_html("https://daleel.tn/reset?token=xyz")
        assert "https://daleel.tn/reset?token=xyz" in html

    def test_contains_expiration_notice(self):
        html = _build_reset_html("https://ok.com")
        assert "1 heure" in html

    def test_html_escapes_special_chars(self):
        html = _build_reset_html("https://ok.com?a=1&b=2")
        assert "&amp;" in html

    def test_is_valid_html(self):
        html = _build_reset_html("https://ok.com")
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_mentions_daleel(self):
        html = _build_reset_html("https://ok.com")
        assert "Daleel" in html


class TestBuildLoginSecurityHtml:
    def test_contains_login_details_and_action(self):
        html = _build_login_security_html(
            "Amina",
            "2026-06-04 10:30 UTC",
            "203.0.113.10",
            "Firefox",
            "https://daleel.tn/login",
        )
        assert "Nouvelle connexion" in html
        assert "Amina" in html
        assert "203.0.113.10" in html
        assert "Firefox" in html
        assert "https://daleel.tn/login" in html

    def test_html_escapes_login_details(self):
        html = _build_login_security_html(
            "<script>alert(1)</script>",
            "now",
            "127.0.0.1",
            "<img src=x>",
            "https://ok.com?a=1&b=2",
        )
        assert "<script>" not in html
        assert "<img" not in html
        assert "&lt;script&gt;" in html
        assert "&amp;" in html
