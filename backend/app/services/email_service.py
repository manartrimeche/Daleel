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


def _build_login_security_html(
    full_name: str,
    login_time: str,
    ip_address: str,
    user_agent: str,
    action_url: str,
) -> str:
    import html

    full_name = html.escape(full_name or "utilisateur")
    login_time = html.escape(login_time or "non disponible")
    ip_address = html.escape(ip_address or "non disponible")
    user_agent = html.escape(user_agent or "non disponible")
    action_url = html.escape(action_url)
    return f"""\
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:40px 0">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <h2 style="color:#1a1a2e;margin-top:0">Nouvelle connexion à votre compte Daleel</h2>
    <p style="color:#555;line-height:1.6">
      Bonjour {full_name},<br><br>
      Nous avons détecté une nouvelle connexion à votre compte <strong>Daleel</strong>.
    </p>
    <div style="background:#f7f7f8;border:1px solid #e5e5e8;border-radius:10px;padding:18px;margin:24px 0;color:#333;line-height:1.7">
      <div><strong>Date et heure :</strong> {login_time}</div>
      <div><strong>Adresse IP :</strong> {ip_address}</div>
      <div><strong>Appareil / navigateur :</strong> {user_agent}</div>
    </div>
    <p style="color:#555;line-height:1.6">
      <strong>C'était vous ?</strong><br>
      Si oui, aucune action n'est nécessaire.
    </p>
    <p style="color:#555;line-height:1.6">
      Si vous ne reconnaissez pas cette activité, changez immédiatement votre mot de passe
      et contactez votre administrateur.
    </p>
    <div style="text-align:center;margin:32px 0">
      <a href="{action_url}"
         style="background:#1a1a2e;color:#fff;text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:600;display:inline-block">
        Sécuriser mon compte
      </a>
    </div>
    <p style="color:#999;font-size:13px">
      Cet email est envoyé automatiquement pour protéger votre compte. Ne le transférez pas.
    </p>
  </div>
</body>
</html>"""


async def send_login_security_email(
    to_email: str,
    *,
    full_name: str,
    login_time: str,
    ip_address: str,
    user_agent: str,
) -> bool:
    settings = get_settings()
    action_url = f"{settings.app_base_url}/login"

    if not settings.smtp_host:
        logger.warning("SMTP not configured — login security email not sent for %s", to_email)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Nouvelle connexion à votre compte Daleel"
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email

    text_body = (
        f"Bonjour {full_name or 'utilisateur'},\n\n"
        "Nous avons détecté une nouvelle connexion à votre compte Daleel.\n\n"
        "Détails de connexion :\n"
        f"- Date et heure : {login_time or 'non disponible'}\n"
        f"- Adresse IP : {ip_address or 'non disponible'}\n"
        f"- Appareil / navigateur : {user_agent or 'non disponible'}\n\n"
        "C'était vous ? Si oui, aucune action n'est nécessaire.\n\n"
        "Si vous ne reconnaissez pas cette activité, changez immédiatement votre mot de passe "
        "et contactez votre administrateur.\n\n"
        f"Accéder à Daleel : {action_url}"
    )
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(
        _build_login_security_html(full_name, login_time, ip_address, user_agent, action_url),
        "html",
        "utf-8",
    ))

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, partial(_send_smtp, msg))
        logger.info("Login security email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.exception("Failed to send login security email to %s: %s", to_email, exc)
        return False


def _build_verification_html(verify_url: str) -> str:
    import html
    verify_url = html.escape(verify_url)
    return f"""\
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:40px 0">
  <div style="max-width:500px;margin:0 auto;background:#fff;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <h2 style="color:#1a1a2e;margin-top:0">Confirmez votre adresse email</h2>
    <p style="color:#555;line-height:1.6">
      Bienvenue sur <strong>Daleel</strong>. Pour finaliser votre inscription,
      veuillez confirmer votre adresse email. Votre compte sera ensuite soumis
      à l'approbation du super administrateur.
    </p>
    <div style="text-align:center;margin:32px 0">
      <a href="{verify_url}"
         style="background:#1a1a2e;color:#fff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:600;display:inline-block">
        Confirmer mon email
      </a>
    </div>
    <p style="color:#999;font-size:13px">
      Ce lien expire dans 24 heures. Si vous n'avez pas demandé cette inscription, ignorez cet email.
    </p>
  </div>
</body>
</html>"""


async def send_verification_email(to_email: str, token: str) -> bool:
    settings = get_settings()

    if not settings.smtp_host:
        # Dev / staging : on log le lien pour pouvoir tester sans SMTP.
        verify_url = f"{settings.app_base_url}/verify-email?token={token}"
        logger.warning(
            "smtp.not_configured verify_url=%s (email=%s)", verify_url, to_email
        )
        return False

    verify_url = f"{settings.app_base_url}/verify-email?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Confirmez votre adresse email — Daleel"
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email

    text_body = (
        "Bienvenue sur Daleel.\n\n"
        f"Confirmez votre adresse email en cliquant sur ce lien : {verify_url}\n\n"
        "Ce lien expire dans 24 heures."
    )
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(_build_verification_html(verify_url), "html", "utf-8"))

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, partial(_send_smtp, msg))
        logger.info("Verification email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.exception("Failed to send verification email to %s: %s", to_email, exc)
        return False


def _build_phone_otp_html(phone: str, code: str) -> str:
    import html
    phone = html.escape(phone)
    code = html.escape(code)
    return f"""\
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:40px 0">
  <div style="max-width:500px;margin:0 auto;background:#fff;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <h2 style="color:#1a1a2e;margin-top:0">Vérification de votre téléphone</h2>
    <p style="color:#555;line-height:1.6">
      Pour confirmer le numéro <strong>{phone}</strong>, saisissez le code
      ci-dessous dans le formulaire d'inscription <strong>Daleel</strong>.
    </p>
    <div style="text-align:center;margin:32px 0">
      <span style="display:inline-block;background:#f0f0f0;padding:16px 32px;border-radius:8px;font-size:28px;font-weight:700;letter-spacing:6px;color:#1a1a2e">{code}</span>
    </div>
    <p style="color:#999;font-size:13px">
      Ce code expire dans 10 minutes. Si vous n'avez pas demandé cette vérification, ignorez cet email.
    </p>
  </div>
</body>
</html>"""


async def send_phone_otp_email(to_email: str, phone: str, code: str) -> bool:
    settings = get_settings()

    if not settings.smtp_host:
        logger.warning(
            "smtp.not_configured otp=%s phone=%s email=%s", code, phone, to_email
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Code de vérification Daleel : {code}"
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email

    text_body = (
        f"Votre code de vérification Daleel pour le numéro {phone} : {code}\n\n"
        "Ce code expire dans 10 minutes."
    )
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(_build_phone_otp_html(phone, code), "html", "utf-8"))

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, partial(_send_smtp, msg))
        logger.info("Phone OTP email sent to %s for phone %s", to_email, phone)
        return True
    except Exception as exc:
        logger.exception("Failed to send phone OTP email to %s: %s", to_email, exc)
        return False


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
