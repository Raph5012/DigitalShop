from database.tables import AccountTable
from .models import Account
from .exceptions import *
from typing import Protocol
from sqlalchemy.orm import Session
from sqlalchemy import select


class AccountRepositoryProtocol(Protocol):
    def create(self, account: Account) -> Account:
        ...

    def update(self, account: Account) -> None:
        ...

    def remove(self, account_id: int) -> None:
        ...

    def get_by_id(self, account_id: int) -> Account | None:
        ...

    def get_by_username(self, username: str) -> Account | None:
        ...

    def get_by_email(self, email: str) -> Account | None:
        ...

    def get_by_phone_number(self, phone_number: str) -> Account | None:
        ...


class AccountRepository(AccountRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _to_orm(self, account: Account) -> AccountTable:
        return AccountTable(
            id=account.id,
            username=account.username,
            email=account.email,
            phone_number=account.phone_number,
            password_hash=account.password_hash,
            role=account.role
        )

    def _to_domain(self, account: AccountTable) -> Account:
        return Account(
                id=account.id,
                username=account.username,
                email=account.email,
                phone_number=account.phone_number,
                password_hash=account.password_hash,
                role=account.role
            )

    def create(self, account: Account) -> Account:
        if account.id is not None:
            raise AlreadyExistsException("Account id should be None when creating")

        orm_account: AccountTable = self._to_orm(account)
        self._session.add(orm_account)
        self._session.flush()

        return self._to_domain(orm_account)

    def update(self, account: Account) -> None:
        if account.id is None:
            raise NotFoundException("Account id cannot be None")

        orm_account: AccountTable | None = self._session.get(AccountTable, account.id)
        if orm_account is None:
            raise NotFoundException(f"Account with id={account.id} not found")

        orm_account.username = account.username
        orm_account.email = account.email
        orm_account.phone_number = account.phone_number
        orm_account.password_hash = account.password_hash
        orm_account.role = account.role

        self._session.flush()

    def remove(self, account_id: int) -> None:
        if account_id is None:
            raise NotFoundException("Account id cannot be None")

        orm_account: AccountTable | None = self._session.get(AccountTable, account_id)
        if orm_account is None:
            raise NotFoundException(f"Account with id={account_id} not found")

        self._session.delete(orm_account)
        self._session.flush()

    def get_by_id(self, account_id: int) -> Account | None:
        orm_account: AccountTable | None = self._session.get(AccountTable, account_id)
        if orm_account is None:
            return None

        return self._to_domain(orm_account)

    def get_by_username(self, username: str) -> Account | None:
        stmt = select(AccountTable).where(AccountTable.username == username)
        orm_account: AccountTable | None = self._session.execute(stmt).scalar_one_or_none()
        if orm_account is None:
            return None

        return self._to_domain(orm_account)

    def get_by_email(self, email: str) -> Account | None:
        stmt = select(AccountTable).where(AccountTable.email == email)
        orm_account: AccountTable | None = self._session.execute(stmt).scalar_one_or_none()
        if orm_account is None:
            return None

        return self._to_domain(orm_account)

    def get_by_phone_number(self, phone_number: str) -> Account | None:
        stmt = select(AccountTable).where(AccountTable.phone_number == phone_number)
        orm_account: AccountTable | None = self._session.execute(stmt).scalar_one_or_none()
        if orm_account is None:
            return None

        return self._to_domain(orm_account)