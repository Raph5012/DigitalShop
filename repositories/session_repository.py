from datetime import datetime, timezone
from database.tables import SessionTable
from .models import Session
from typing import Protocol
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select
from .exceptions import NotFoundException, AlreadyExistsException


class SessionRepositoryProtocol(Protocol):
    def create(self, session: Session) -> Session:
        ...

    def update(self, session: Session) -> Session:
        ...

    def remove(self, session_id: int) -> None:
        ...

    def get_by_id(self, session_id: int) -> Session | None:
        ...

    def get_by_account(self, account_id: int) -> list[Session]:
        ...

    def get_valid_by_token_hash(self, token_hash: str) -> Session | None:
        ...


class SessionRepository(SessionRepositoryProtocol):
    def __init__(self, orm_session: OrmSession) -> None:
        self._orm_session = orm_session

    @staticmethod
    def _to_orm(session: Session) -> SessionTable:
        return SessionTable(
            account_id=session.account_id,
            created_at=session.created_at,
            ends_at=session.ends_at,
            revoked_at=session.revoked_at,
            session_token_hash=session.session_token_hash
        )

    @staticmethod
    def _to_domain(session: SessionTable) -> Session:
        return Session(
            id=session.id,
            account_id=session.account_id,
            created_at=session.created_at,
            ends_at=session.ends_at,
            revoked_at=session.revoked_at,
            session_token_hash=session.session_token_hash
        )

    def create(self, session: Session) -> Session:
        if session.id is not None:
            raise AlreadyExistsException("Session id should be None when creating")

        session_orm = self._to_orm(session)
        self._orm_session.add(session_orm)
        self._orm_session.flush()

        return self._to_domain(session_orm)

    def update(self, session: Session) -> Session:
        session_orm = self._orm_session.get(SessionTable, session.id)
        if session_orm is None:
            raise NotFoundException(f"Session with id={session.id} not found")

        session_orm.account_id = session.account_id
        session_orm.created_at = session.created_at
        session_orm.ends_at = session.ends_at
        session_orm.revoked_at = session.revoked_at
        session_orm.session_token_hash = session.session_token_hash

        self._orm_session.flush()
        return self._to_domain(session_orm)

    def remove(self, session_id: int) -> None:
        session_orm = self._orm_session.get(SessionTable, session_id)
        if session_orm is None:
            raise NotFoundException(f"Session with id={session_id} not found")

        self._orm_session.delete(session_orm)
        self._orm_session.flush()

    def get_by_id(self, session_id: int) -> Session | None:
        session_orm = self._orm_session.get(SessionTable, session_id)
        if session_orm is None:
            return None

        return self._to_domain(session_orm)

    def get_by_account(self, account_id: int) -> list[Session]:
        stmt = select(SessionTable).where(SessionTable.account_id == account_id)
        session_orms = self._orm_session.execute(stmt).scalars().all()
        return [self._to_domain(s) for s in session_orms]

    def get_valid_by_token_hash(self, token_hash: str) -> Session | None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(SessionTable)
            .where(
                SessionTable.session_token_hash == token_hash,
                SessionTable.revoked_at.is_(None),
                SessionTable.ends_at > now,
            )
        )
        session_orm = self._orm_session.execute(stmt).scalar_one_or_none()
        if session_orm is None:
            return None
        return self._to_domain(session_orm)