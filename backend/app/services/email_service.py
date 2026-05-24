"""
Email service: send invitation and password reset emails via SMTP.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial
from urllib.parse import quote

from app.config import get_settings

logger = logging.getLogger(__name__)


def _build_invitation_html(org_name: str, invite_url: str) -> str:
    import html
    org_name = html.escape(org_name)
    invite_url = html.escape(invite_url)
    return f"""\
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:40px 0">
  <div style="max-width:500px;margin:0 auto;background:#fff;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <h2 style="color:#1a1a2e;margin-top:0">Vous êtes invité(e) à rejoindre {org_name}</h2>
    <p style="color:#555;line-height:1.6">
      Un administrateur de <strong>{org_name}</strong> vous invite à rejoindre
      la plateforme <strong>Daleel</strong> en tant que membre.
    </p>
    <div style="text-align:center;margin:32px 0">
      <a href="{invite_url}"
         style="background:#1a1a2e;color:#fff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:600;display:inline-block">
        Accepter l'invitation
      </a>
    </div>
    <p style="color:#999;font-size:13px">
      Ce lien expire dans 72 heures. Si vous n'avez pas demandé cette invitation, ignorez cet email.
    </p>
  </div>
</body>
</html>"""


def _send_smtp(msg: MIMEMultipart) -> None:
    settings = get_settings()
    logger.info("Connecting to SMTP %s:%s ...", settings.smtp_host, settings.smtp_port)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        server.set_debuglevel(0)
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


async def send_invitation_email(
    to_email: str,
    org_name: str,
    token: str,
) -> bool:
    settings = get_settings()

    if not settings.smtp_host:
        logger.warning("SMTP not configured — invitation email not sent for %s", to_email)
        return False

    invite_url = f"{settings.app_base_url}/invite?token={token}&org={quote(org_name)}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Invitation à rejoindre {org_name} sur Daleel"
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email

    text_body = (
        f"Vous êtes invité(e) à rejoindre {org_name} sur Daleel.\n\n"
        f"Cliquez sur ce lien pour accepter : {invite_url}\n\n"
        f"Ce lien expire dans 72 heures."
    )
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(_build_invitation_html(org_name, invite_url), "html", "utf-8"))

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, partial(_send_smtp, msg))
        logger.info("Invitation email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.exception("Failed to send invitation email to %s: %s", to_email, exc)
        return False


def _build_reset_html(reset_url: str) -> str:
    import html
    reset_url = html.escape(reset_url)
    return f"""\
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:40px 0">
  <div style="max-width:500px;margin:0 auto;background:#fff;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <h2 style="color:#1a1a2e;margin-top:0">Réinitialisation de mot de passe</h2>
    <p style="color:#555;line-height:1.6">
      Vous avez demandé la réinitialisation de votre mot de passe sur <strong>Daleel</strong>.
      Cliquez sur le bouton ci-dessous pour choisir un nouveau mot de passe.
    </p>
    <div style="text-align:center;margin:32px 0">
      <a href="{reset_url}"
         style="background:#1a1a2e;color:#fff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:600;display:inline-block">
        Réinitialiser le mot de passe
      </a>
    </div>
    <p style="color:#999;font-size:13px">
      Ce lien expire dans 1 heure. Si vous n'avez pas fait cette demande, ignorez cet email.
    </p>
  </div>
</body>
</html>"""


async def send_password_reset_email(to_email: str, token: str) -> bool:
    settings = get_settings()

    if not settings.smtp_host:
        logger.warning("SMTP not configured — password reset email not sent for %s", to_email)
        return False

    reset_url = f"{settings.app_base_url}/reset-password?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Réinitialisation de mot de passe — Daleel"
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email

    text_body = (
        "Vous avez demandé la réinitialisation de votre mot de passe sur Daleel.\n\n"
        f"Cliquez sur ce lien : {reset_url}\n\n"
        "Ce lien expire dans 1 heure."
    )
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(_build_reset_html(reset_url), "html", "utf-8"))

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, partial(_send_smtp, msg))
        logger.info("Password reset email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.exception("Failed to send password reset email to %s: %s", to_email, exc)
        return False
