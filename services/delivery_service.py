from typing import Protocol

from database.enums import OrderStatus
from repositories.exceptions import NotFoundException
from repositories.models import Order
from repositories.order_repository import OrderRepositoryProtocol

from .download_link_service import DownloadLinkServiceProtocol
from .email_service import Email, EmailSenderProtocol


class DeliveryServiceProtocol(Protocol):
    def send_order(self, order_id: int) -> None:
        ...

    def get_order_links(self, order_id: int) -> list[str]:
        ...

    def revoke_order_links(self, order_id: int) -> int:
        ...


class DeliveryService(DeliveryServiceProtocol):
    def __init__(self,
                 order_repo: OrderRepositoryProtocol,
                 links: DownloadLinkServiceProtocol,
                 email_sender: EmailSenderProtocol,
                 download_url_base: str) -> None:
        self._order_repo = order_repo
        self._links = links
        self._email_sender = email_sender
        self._download_url_base = download_url_base

    def send_order(self, order_id: int) -> None:
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise NotFoundException(f"Order with id={order_id} not found")

        if order.status not in (OrderStatus.paid, OrderStatus.delivered):
            raise ValueError(f"Cannot deliver order with status={order.status}")

        urls = self._get_or_create_urls(order_id, order)
        self._send_email(order, urls)

        if order.status == OrderStatus.paid:
            order.status = OrderStatus.delivered
            self._order_repo.update(order)

    def get_order_links(self, order_id: int) -> list[str]:
        links = self._links.get_for_order(order_id)
        return [self._build_url(link.token) for link in links]

    def revoke_order_links(self, order_id: int) -> int:
        return self._links.revoke_for_order(order_id)

    def _get_or_create_urls(self, order_id: int, order: Order) -> list[str]:
        links = self._links.get_for_order(order_id)
        if not links:
            product_ids = list({snapshot.product_id for snapshot in order.product_snapshots})
            tokens = self._links.create_links(order_id, product_ids)
            return [self._build_url(token) for token in tokens]

        return [self._build_url(link.token) for link in links]

    def _build_url(self, token: str) -> str:
        return self._download_url_base + token

    def _send_email(self, order: Order, urls: list[str]) -> None:
        self._email_sender.send(Email(
            recipient=order.email,
            subject="Twoje pliki do pobrania",
            template_id="delivery",
            template_variables={"download_links": "\n".join(urls)},
        ))
