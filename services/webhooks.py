from database.enums import OrderStatus
from .order_service import OrderServiceProtocol
from .delivery_service import DeliveryServiceProtocol
from .exceptions import NotFoundException
from repositories.models import Order
from stripe import Webhook
from typing import Any


class StripeWebhookHandler:
    def __init__(
        self,
        order_service: OrderServiceProtocol,
        delivery_service: DeliveryServiceProtocol,
        stripe_webhook_secret: str,
    ) -> None:
        self._order_service = order_service
        self._delivery_service = delivery_service
        self._stripe_webhook_secret = stripe_webhook_secret

    def _extract_order_id(self, checkout: dict[str, Any]) -> int:
        raw_order_id = checkout.get("client_reference_id")
        if raw_order_id is None:
            raise ValueError("Webhook didn't provide client_reference_id")

        return int(raw_order_id)

    def _get_order(self, order_id: int) -> Order:
        order = self._order_service.get_by_id(order_id)
        if order is None:
            raise NotFoundException(f"Order with id={order_id} not found")

        return order

    def handle(self, payload: bytes, signature: str) -> None:
        event = Webhook.construct_event(payload, signature, self._stripe_webhook_secret)
        event_type: str = event["type"]

        match event_type:
            case "checkout.session.completed":
                session: dict[str, Any] = event["data"]["object"]
                if session.get("payment_status") != "paid":
                    return

                order_id = self._extract_order_id(session)
                order = self._get_order(order_id)

                if order.status in (OrderStatus.paid, OrderStatus.delivered):
                    return

                self._order_service.confirm_payment_from_webhook(order_id)
                self._delivery_service.send_order(order_id)

            case "checkout.session.expired":
                session: dict[str, Any] = event["data"]["object"]
                order_id = self._extract_order_id(session)
                order = self._get_order(order_id)

                if order.status != OrderStatus.pending:
                    return

                self._order_service.cancel_from_webhook(order_id)
