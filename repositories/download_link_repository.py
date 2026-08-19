from database.tables import DownloadLinkTable
from typing import Protocol
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import DownloadLink
from .exceptions import *



class DownloadLinkRepositoryProtocol(Protocol):
    def create_download_link(self, download_link: DownloadLink) -> DownloadLink:
        ...

    def update_download_link(self, download_link: DownloadLink) -> None:
        ...

    def remove_download_link(self, download_link_id: int) -> None:
        ...

    def get_download_link_by_id(self, download_link_id: int) -> DownloadLink | None:
        ...

    def get_download_link_by_token_hash(self, token_hash: str) -> DownloadLink | None:
        ...

    def get_download_links_by_order_id(self, order_id: int) -> list[DownloadLink]:
        ...


class DownloadLinkRepository(DownloadLinkRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _to_orm(self, dl: DownloadLink) -> DownloadLinkTable:
        return DownloadLinkTable(
            id=dl.id,
            product_id=dl.product_id,
            order_id=dl.order_id,
            created_at=dl.created_at,
            valid_until=dl.valid_until,
            revoked_at=dl.revoked_at,
            token_hash=dl.token_hash
        )

    def _to_domain(self, dl: DownloadLinkTable) -> DownloadLink:
        return DownloadLink(
            id=dl.id,
            product_id=dl.product_id,
            order_id=dl.order_id,
            created_at=dl.created_at,
            valid_until=dl.valid_until,
            revoked_at=dl.revoked_at,
            token_hash=dl.token_hash
        )

    def create_download_link(self, download_link: DownloadLink) -> DownloadLink:
        if download_link.id is not None:
            raise AlreadyExistsException(f"DownloadLink id should be None when creating new object")
        
        dl_orm: DownloadLinkTable = self._to_orm(download_link)

        self._session.add(dl_orm)
        self._session.flush()

        return self._to_domain(dl_orm)

    def update_download_link(self, download_link: DownloadLink) -> None:
        dl_orm: DownloadLinkTable | None = self._session.get(DownloadLinkTable, download_link.id)
        if dl_orm is None:
            raise NotFoundException(f"DownloadLink with id={download_link.id} not found")

        dl_orm.product_id = download_link.product_id
        dl_orm.order_id = download_link.order_id
        dl_orm.created_at = download_link.created_at
        dl_orm.valid_until = download_link.valid_until
        dl_orm.revoked_at = download_link.revoked_at
        dl_orm.token_hash = download_link.token_hash

        self._session.flush()

    def remove_download_link(self, download_link_id: int) -> None:
        dl_orm: DownloadLinkTable | None = self._session.get(DownloadLinkTable, download_link_id)
        if dl_orm is None:
            raise NotFoundException(f"DownloadLink with id={download_link_id} not found")

        self._session.delete(dl_orm)
        self._session.flush()

    def get_download_link_by_id(self, download_link_id: int) -> DownloadLink | None:
        dl_orm: DownloadLinkTable | None = self._session.get(DownloadLinkTable, download_link_id)
        if dl_orm is None:
            return None

        return self._to_domain(dl_orm)

    def get_download_link_by_token_hash(self, token_hash: str) -> DownloadLink | None:
        stmt = select(DownloadLinkTable).where(DownloadLinkTable.token_hash == token_hash)
        dl_orm: DownloadLinkTable | None = self._session.execute(stmt).scalar_one_or_none()
        if dl_orm is None:
            return None

        return self._to_domain(dl_orm)

    def get_download_links_by_order_id(self, order_id: int) -> list[DownloadLink]:
        stmt = select(DownloadLinkTable).where(DownloadLinkTable.order_id == order_id)
        dl_orms = self._session.execute(stmt).scalars().all()
        return [self._to_domain(dl) for dl in dl_orms]
    