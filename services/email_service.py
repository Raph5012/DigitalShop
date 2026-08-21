from typing import Protocol, Any
from pydantic import BaseModel, EmailStr, Field
import resend
from jinja2 import Environment, FileSystemLoader, select_autoescape


class Email(BaseModel):
    recipient: EmailStr = Field(min_length=5, max_length=128)
    subject: str = Field(min_length=5, max_length=64)
    template_id: str = Field(min_length=1)
    template_variables: dict[str, Any] | None = None


class EmailSenderProtocol(Protocol):
    def send(self, email: Email) -> None:
        ...


class EmailSenderResend(EmailSenderProtocol):
    def __init__(self, api_key: str, email_address: str, templates_dir: str = "email/templates") -> None:
        self._api_key = api_key
        resend.api_key = api_key
        self._email_address = email_address
        self._jinja_env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html"]),
        )

    def _render_html(self, email: Email) -> str:
        template = self._jinja_env.get_template(f"{email.template_id}.html")
        return template.render(**(email.template_variables or {}))

    def _build_mail_params(self, email: Email) -> resend.Emails.SendParams:
        return {
            "from": self._email_address,
            "to": email.recipient,
            "subject": email.subject,
            "html": self._render_html(email),
        }

    def send(self, email: Email) -> None:
        try:
            params: resend.Emails.SendParams = self._build_mail_params(email)
            resend.Emails.send(params)
        except Exception as e:
            raise ValueError(f"Failed to send email to {email.recipient}: {e}") from e
