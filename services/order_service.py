from repositories.models import Order, ProductSnapshot, Checkout
from repositories.order_repository import OrderRepositoryProtocol
from database.enums import OrderStatus
from typing import Protocol
from pydantic import BaseModel, field_validator
from .payment_integrations import (CheckoutSession,
                                   CheckoutProvider,
                                   CheckoutSessionStatus,
                                   PaymentProviderIntegration,
                                   CheckoutOrderInfo,
                                   CheckoutLine)
from repositories.exceptions import NotFoundException



class UpdateOrder(BaseModel):
    id: int
    status: OrderStatus
    product_snapshots: list['ProductSnapshot']

    @field_validator('product_snapshots', mode='after')
    @classmethod
    def check_for_at_least_one_order_product(cls, products: list['ProductSnapshot']) -> list['ProductSnapshot']:
        if len(products) == 0:
            raise ValueError("Product count must be greater than 0")

        return products


class OrderServiceProtocol(Protocol):
    def create(self, order: Order) -> Order:
        ...

    def get(self, order_id: int, email: str) -> Order | None:
        ...

    def generate_checkout_session(self, 
                                  order_id: int, 
                                  email: str, 
                                  checkout_provider: CheckoutProvider) -> CheckoutSession:
        ...

    def confirm_payment(self, order_id: int, email: str) -> None:
        ...

    def cancel(self, order_id: int, email: str) -> None:
        ...

    # for admins
    def update(self, order: UpdateOrder) -> None:
        ...

    def remove(self, order_id: int) -> None:
        ...

    def get_by_id(self, order_id: int) -> Order | None:
        ...


class OrderService(OrderServiceProtocol):
    def __init__(self, 
                 order_repository: OrderRepositoryProtocol,
                 integrations: dict[CheckoutProvider, PaymentProviderIntegration]) -> None:
        self._repo = order_repository
        self._integrations = integrations

    def _map_integration(self, provider: CheckoutProvider) -> PaymentProviderIntegration:
        integration: PaymentProviderIntegration | None = self._integrations.get(provider)
        if integration is None:
            raise ValueError(f"No integration configured for provider {provider}")

        return integration

    def create(self, order: Order) -> Order:
        return self._repo.create(order)

    def get(self, order_id: int, email: str) -> Order | None:
        order: Order | None = self._repo.get_by_id(order_id)
        if order is None or order.email != email.casefold():
            return None

        return order

    def _parse_order_or_raise(self, order_id: int, email: str) -> Order:
        order: Order | None = self._repo.get_by_id(order_id)
        if order is None:
            raise NotFoundException(f"Couldn't find order with id={order_id}")

        if order.email != email.casefold():
            raise ValueError("Email from the order doesn't match the email provided")

        return order

    def generate_checkout_session(self, 
                                  order_id: int, 
                                  email: str, 
                                  checkout_provider: CheckoutProvider) -> CheckoutSession:
        order: Order = self._parse_order_or_raise(order_id, email)

        if order.status != OrderStatus.pending:
            raise ValueError(f"Cannot generate checkout session for order status={order.status}")

        integration: PaymentProviderIntegration = self._map_integration(checkout_provider)
        info = CheckoutOrderInfo(
            order_id=order_id,
            email=order.email,
            lines=[CheckoutLine(name=snapshot.name, unit_price=snapshot.price)
                   for snapshot in order.product_snapshots],
        )

        checkout_session: CheckoutSession = integration.generate_checkout_session(info)

        order.checkout = Checkout(
            order_id=order_id,
            provider=checkout_session.checkout_provider,
            session_id=checkout_session.session_id,
        )
        self._repo.update(order)

        return checkout_session
        
    def confirm_payment(self, order_id: int, email: str) -> None:
        order: Order = self._parse_order_or_raise(order_id, email)

        if order.checkout is None:
            raise ValueError("No checkout session found for this order")

        if order.status == OrderStatus.paid:
            return  # idempotencja — webhook mógł już potwierdzić

        if order.status != OrderStatus.pending:
            raise ValueError(f"Cannot confirm payment for order status={order.status}")

        integration: PaymentProviderIntegration = self._map_integration(order.checkout.provider)
        status: CheckoutSessionStatus | None = integration.get_session_status(order.checkout.session_id)

        if status is not CheckoutSessionStatus.paid:
            return  # nie opłacono — nic nie zmieniaj

        order.status = OrderStatus.paid
        self._repo.update(order)

    def cancel(self, order_id: int, email: str) -> None:
        order: Order = self._parse_order_or_raise(order_id, email)

        if order.status == OrderStatus.cancelled:
            return

        if order.status != OrderStatus.pending:
            raise ValueError(f"Cannot cancel order with status={order.status}")

        order.status = OrderStatus.cancelled
        self._repo.update(order)

    # for admins
    def update(self, order: UpdateOrder) -> None:
        existing: Order | None = self._repo.get_by_id(order.id)
        if existing is None:
            raise NotFoundException(f"Couldn't find order with id={order.id}")

        existing.status = order.status
        existing.product_snapshots = order.product_snapshots
        self._repo.update(existing)

    def remove(self, order_id: int) -> None:
        order: Order | None = self._repo.get_by_id(order_id)
        if order is None:
            raise NotFoundException(f"Couldn't find order with id={order_id}")

        self._repo.remove(order)

    def get_by_id(self, order_id: int) -> Order | None:
        return self._repo.get_by_id(order_id)