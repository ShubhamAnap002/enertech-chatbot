from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    status: str  # queued | sent | failed | retrying
    provider_message_id: str = ""
    error: str = ""


class EmailProvider(Protocol):
    def send(self, *, to: str, subject: str, html: str, bcc: str | None = None) -> EmailResult: ...


class ConsoleEmailProvider:
    def send(self, *, to: str, subject: str, html: str, bcc: str | None = None) -> EmailResult:
        logger.info("EMAIL to=%s bcc=%s subject=%s bytes=%s", to, bcc, subject, len(html))
        return EmailResult(status="sent", provider_message_id="console-local")


class SMTPEmailProvider:
    def send(self, *, to: str, subject: str, html: str, bcc: str | None = None) -> EmailResult:
        # Minimal SMTP path; prefer console in local/dev.
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.email_from
            msg["To"] = to
            msg["Subject"] = subject
            if bcc:
                msg["Bcc"] = bcc
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                server.starttls()
                if settings.smtp_user:
                    server.login(settings.smtp_user, settings.smtp_password)
                recipients = [to] + ([bcc] if bcc else [])
                server.sendmail(settings.email_from, recipients, msg.as_string())
            return EmailResult(status="sent", provider_message_id="smtp")
        except Exception as exc:  # noqa: BLE001
            logger.exception("SMTP send failed")
            return EmailResult(status="failed", error=str(exc))


class EmailService:
    def __init__(self, provider: EmailProvider | None = None):
        if provider:
            self.provider = provider
        elif settings.email_provider == "smtp" and settings.smtp_host:
            self.provider = SMTPEmailProvider()
        else:
            self.provider = ConsoleEmailProvider()

    def send(self, *, to: str, subject: str, html: str, bcc: str | None = None) -> EmailResult:
        return self.provider.send(to=to, subject=subject, html=html, bcc=bcc)
