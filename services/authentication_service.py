from repositories.account_repository import AccountRepositoryProtocol
from repositories.models import Account
from .hasher import Hasher
from .session_service import SessionService
from .exceptions import AuthError


class AuthenticationService:
    def __init__(
        self,
        accounts: AccountRepositoryProtocol,
        sessions_service: SessionService,
        hasher: Hasher
    ) -> None:
        self._accounts = accounts
        self._sessions_service = sessions_service
        self._hasher = hasher

    def login(self, username: str, password: str) -> str:
        account = self._accounts.get_by_username(username)
        if account is None or not self._hasher.verify(password, account.password_hash):
            raise AuthError("Invalid credentials")

        return self._sessions_service.create(account.id)

    def rotate_session(self, raw_token: str) -> str:
        return self._sessions_service.rotate(raw_token)

    def me(self, raw_token: str) -> Account:
        account_id = self._sessions_service.get_account_id(raw_token)
        if account_id is None:
            raise AuthError("Invalid or expired session")

        account = self._accounts.get_by_id(account_id)
        if account is None:
            raise AuthError(f"Account with id={account_id} not found")

        return account

    def logout(self, raw_token: str) -> None:
        self._sessions_service.revoke(raw_token)

    def logout_all(self, account_id: int) -> None:
        self._sessions_service.revoke_all(account_id)
            
        



