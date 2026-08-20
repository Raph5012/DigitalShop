from enum import Enum
import stripe
from stripe.params.checkout import (SessionCreateParams, 
                                    SessionListParams,
                                    SessionCreateParamsLineItem, 
                                    SessionCreateParamsLineItemPriceData,
                                    SessionCreateParamsLineItemPriceDataProductData)
from repositories.models import PriceType
from pydantic import BaseModel, EmailStr, field_validator
from typing import Protocol, Literal, Final
from .exceptions import CheckoutSessionException
from database.enums import CheckoutSessionStatus, CheckoutProvider


Currency = Literal['usd', 'eur', 'pln']


class CheckoutSession(BaseModel):
    checkout_provider: CheckoutProvider
    session_id: str
    order_id: int


class CheckoutLine(BaseModel):
    name: str
    unit_price: PriceType


class CheckoutOrderInfo(BaseModel):
    order_id: int
    email: EmailStr
    currency: Currency = "usd"
    lines: list[CheckoutLine]

    @field_validator('lines', mode='after')
    @classmethod
    def _check_for_at_least_one_line(cls, lines: list[CheckoutLine]) -> list[CheckoutLine]:
        if not lines:
            raise ValueError("At least one product is needed to generate checkout session")

        return lines


class PaymentProviderIntegration(Protocol):
    def generate_checkout_session(self, info: CheckoutOrderInfo) -> CheckoutSession:
        ...

    def get_session_status(self, provider_session_id: str) -> CheckoutSessionStatus | None:
        ...


class StripeIntegration(PaymentProviderIntegration):
    def __init__(self, 
                 stripe_api_key: str,
                 success_url: str,
                 cancel_url: str) -> None:
        self._success_url = success_url
        self._cancel_url = cancel_url
        self._client = stripe.StripeClient(api_key=stripe_api_key)

    def _get_stripe_line_item(self, line: CheckoutLine, currency: Currency) -> SessionCreateParamsLineItem:
        price_data = SessionCreateParamsLineItemPriceData(
            currency=currency,
            product_data=SessionCreateParamsLineItemPriceDataProductData(
                name=line.name
            ),
            unit_amount=int(line.unit_price*100)
        )

        return SessionCreateParamsLineItem(
            quantity=1,
            price_data=price_data
        )

    def generate_checkout_session(self, info: CheckoutOrderInfo) -> CheckoutSession:
        try:
            session = self._client.v1.checkout.sessions.create(
                SessionCreateParams(
                    client_reference_id=str(info.order_id),
                    line_items=[self._get_stripe_line_item(line, info.currency) for line in info.lines],
                    mode="payment",
                    ui_mode="hosted_page",
                    success_url=self._success_url,
                    cancel_url=self._cancel_url,
                    customer_email=info.email
                )
            )
        except stripe.StripeError as e:
            raise CheckoutSessionException("Failed to create checkout session") from e

        return CheckoutSession(
            checkout_provider=CheckoutProvider.stripe,
            session_id=session.id,
            order_id=info.order_id
        )

    def _map_stripe_status(self, 
                           stripe_status: Literal['complete', 'expired', 'open']) -> CheckoutSessionStatus | None:
        match stripe_status:
            case 'complete':
                return CheckoutSessionStatus.paid
            case 'expired':
                return CheckoutSessionStatus.cancelled
            case 'open':
                return CheckoutSessionStatus.pending

    def get_session_status(self, provider_session_id: str) -> CheckoutSessionStatus | None:
        try:
            session = self._client.v1.checkout.sessions.retrieve(session=provider_session_id)
        except stripe.StripeError as e:
            raise CheckoutSessionException("Failed to get checkout session") from e 

        status: CheckoutSessionStatus = self._map_stripe_status(session.status)
        return status
