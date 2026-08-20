import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Protocol

from repositories.models import Session
from repositories.session_repository import SessionRepositoryProtocol
from .config import SESSION_LIFETIME
from .exceptions import AuthError


class SessionServiceProtocol(Protocol):
    def create(self, account_id: int) -> str:
        ...

    def get_account_id(self, raw_token: str) -> int | None:
        ...

    def rotate(self, raw_token: str) -> str:
        ...

    def revoke(self, raw_token: str) -> None:
        ...

    def revoke_all(self, account_id: int) -> None:
        ...


class SessionService(SessionServiceProtocol):
    def __init__(
        self,
        sessions: SessionRepositoryProtocol,
        lifetime: timedelta = SESSION_LIFETIME
    ):
        self._sessions = sessions
        self._lifetime = lifetime

    def create(self, account_id: int) -> str:
        raw_token: str = secrets.token_urlsafe(32)
        now: datetime = datetime.now(timezone.utc)
        self._sessions.create(
            Session(
                account_id=account_id,
                created_at=now,
                ends_at=now + self._lifetime,
                revoked_at=None,
                session_token_hash=self._hash_token(raw_token)
            )
        )

        return raw_token

    def get_account_id(self, raw_token: str) -> int | None:
        session = self._sessions.get_valid_by_token_hash(self._hash_token(raw_token))
        return session.account_id if session is not None else None

    def rotate(self, raw_token: str) -> str:
        account_id = self.get_account_id(raw_token)
        if account_id is None:
            raise AuthError("Session invalid")

        self.revoke(raw_token)

        return self.create(account_id)

    def revoke(self, raw_token: str) -> None:
        session = self._sessions.get_valid_by_token_hash(self._hash_token(raw_token))
        if session is not None and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            self._sessions.update(session)

    def revoke_all(self, account_id: int) -> None:
        now = datetime.now(timezone.utc)
        for session in self._sessions.get_by_account(account_id):
            if session.revoked_at is None:
                session.revoked_at = now
                self._sessions.update(session)

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    