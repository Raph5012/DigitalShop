import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Protocol

from repositories.download_link_repository import DownloadLinkRepositoryProtocol
from repositories.models import DownloadLink
from .config import LINK_LIFETIME
from .exceptions import LinkError, NotFoundException


class DownloadLinkServiceProtocol(Protocol):
    def create_link(self, order_id: int, product_id: int, lifetime: bool = True) -> str:
        ...

    def create_links(self, order_id: int, product_ids: list[int], lifetime: bool = True) -> list[str]:
        ...

    def update(self, download_link: DownloadLink) -> None:
        ...

    def remove(self, download_link_id: int) -> None:
        ...

    def resolve(self, raw_token: str) -> DownloadLink:
        ...

    def revoke(self, raw_token: str) -> None:
        ...

    def revoke_for_order(self, order_id: int) -> int:
        ...

    def get_for_order(self, order_id: int) -> list[DownloadLink]:
        ...


class DownloadLinkService(DownloadLinkServiceProtocol):
    def __init__(
        self,
        links: DownloadLinkRepositoryProtocol,
        lifetime: timedelta = LINK_LIFETIME
    ):
        self._links = links
        self._lifetime = lifetime

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    
    def create_link(self, order_id: int, product_id: int, lifetime: bool = True) -> str:
        raw_token: str = secrets.token_urlsafe(32)
        now: datetime = datetime.now(timezone.utc)

        self._links.create_download_link(
            DownloadLink(
                order_id=order_id,
                product_id=product_id,
                created_at=now,
                valid_until=(now + self._lifetime) if lifetime else None,
                revoked_at=None,
                token_hash=self._hash_token(raw_token)
            )
        )

        return raw_token

    def create_links(self, order_id: int, product_ids: list[int], lifetime: bool = True) -> list[str]:
        return [self.create_link(order_id, product_id, lifetime) for product_id in product_ids]

    def update(self, download_link: DownloadLink) -> None:
        self._links.update_download_link(download_link)

    def remove(self, download_link_id: int) -> None:
        self._links.remove_download_link(download_link_id)

    def resolve(self, raw_token: str) -> DownloadLink:
        link: DownloadLink | None = self._links.get_download_link_by_token_hash(
            self._hash_token(raw_token)
        )

        if link is None:
            raise NotFoundException("Download link not found")

        if link.revoked_at is not None:
            raise LinkError("Download link has been revoked")

        if link.valid_until is not None and link.valid_until <= datetime.now(timezone.utc):
            raise LinkError("Download link has expired")

        return link

    def revoke(self, raw_token: str) -> None:
        link: DownloadLink | None = self._links.get_download_link_by_token_hash(
            self._hash_token(raw_token)
        )

        if link is None or link.revoked_at is not None:
            return

        link.revoked_at = datetime.now(timezone.utc)
        self._links.update_download_link(link)

    def revoke_for_order(self, order_id: int) -> int:
        revoked: int = 0
        for link in self._links.get_download_links_by_order_id(order_id):
            if link.revoked_at is not None:
                continue
            link.revoked_at = datetime.now(timezone.utc)
            self._links.update_download_link(link)
            revoked += 1

        return revoked

    def get_for_order(self, order_id: int) -> list[DownloadLink]:
        return self._links.get_download_links_by_order_id(order_id)

        