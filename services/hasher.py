from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError, VerificationError


class Hasher:
    def __init__(self, time_cost: int = 3, memory_cost: int = 65536, parallelism: int = 4):
        self._ph = PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism
        )

    def hash(self, plain_secret: str) -> str:
        return self._ph.hash(plain_secret)

    def verify(self, plain_secret: str, hashed_secret: str) -> bool:
        try:
            self._ph.verify(hashed_secret, plain_secret)
            return True
        except (VerifyMismatchError, InvalidHashError, VerificationError):
            return False

    def needs_rehash(self, hashed_secret) -> bool:
        return self._ph.check_needs_rehash(hashed_secret)

