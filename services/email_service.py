from typing import Protocol
from pydantic import BaseModel, EmailStr, Field
import resend
from .exceptions import FailedToSendException


class Email(BaseModel):
    recipient: EmailStr = Field(min_length=5, max_length=128)
    subject: str = Field(min_length=5, max_length=64)
    template_id: str = Field(min_length=1)
    template_variables: dict[str, str] | None = None


class EmailSenderProtocol(Protocol):
    def send(self, email: Email) -> None:
        ...


class EmailSenderResend(EmailSenderProtocol):
    def __init__(self, api_key: str, email_address: str) -> None:
        self._api_key = api_key
        resend.api_key = api_key
        self._email_address = email_address

    def _build_mail_params(self, email: Email) -> resend.Emails.SendParams:
        return {
            "from": self._email_address,
            "to": email.recipient,
            "subject": email.subject,
            "template": {
                "id": email.template_id,
                "variables": email.template_variables or {}
            }
        }

    def send(self, email: Email) -> None:
        try:
            params: resend.Emails.SendParams = self._build_mail_params(email)
            resend.Emails.send(params)
        except Exception as e:
            raise FailedToSendException(f"Failed to send email to {email.recipient}") from e
        