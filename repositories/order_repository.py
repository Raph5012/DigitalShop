from database.tables import OrderTable, ProductSnapshotTable, CheckoutTable
from .models import Order, ProductSnapshot, Checkout
from .exceptions import *
from typing import Protocol
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select


class OrderRepositoryProtocol(Protocol):
    def create(self, order: Order) -> Order:
        ...

    def update(self, order: Order) -> None:
        ...

    def remove(self, order: Order) -> None:
        ...

    def get_by_id(self, order_id: int) -> Order | None:
        ...

    def get_by_phone_number(self, phone_number: str) -> list[Order]:
        ...

    def get_by_email(self, email: str) -> list[Order]:
        ...

    def get_all(self) -> list[Order]:
        ...


class OrderRepository(OrderRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _snapshot_to_orm(self, snapshot: ProductSnapshot) -> ProductSnapshotTable:
        return ProductSnapshotTable(
            product_id=snapshot.product_id,
            name=snapshot.name,
            price=snapshot.price
        )

    def _snapshot_to_domain(self, snapshot: ProductSnapshotTable) -> ProductSnapshot:
        return ProductSnapshot(
            name=snapshot.name,
            price=snapshot.price,
            product_id=snapshot.product_id
        )

    def _checkout_to_orm(self, checkout: Checkout) -> CheckoutTable:
        return CheckoutTable(
            provider=checkout.provider,
            session_id=checkout.session_id
        )

    def _checkout_to_domain(self, checkout: CheckoutTable) -> Checkout:
        return Checkout(
            id=checkout.id,
            order_id=checkout.order_id,
            provider=checkout.provider,
            session_id=checkout.session_id
        )

    def _order_to_domain(self, order: OrderTable) -> Order:
        return Order(
            id=order.id,
            phone_number=order.phone_number,
            email=order.email,
            order_time=order.order_time,
            status=order.status,
            product_snapshots=[self._snapshot_to_domain(snapshot) for snapshot in order.product_snapshots],
            checkout=self._checkout_to_domain(order.checkout) if order.checkout is not None else None
        )

    def _get_orm_orders(self, 
                       order_id: int | None = None,
                       phone_number: str | None = None,
                       email: str | None = None) -> list[OrderTable]:
        stmt = (
            select(OrderTable)
            .options(
                selectinload(OrderTable.product_snapshots),
                selectinload(OrderTable.checkout)
            )
        )

        if order_id is not None:
            stmt = stmt.where(OrderTable.id == order_id)
        if phone_number is not None:
            stmt = stmt.where(OrderTable.phone_number == phone_number)
        if email is not None:
            stmt = stmt.where(OrderTable.email == email)

        orders: list[OrderTable] = self._session.execute(stmt).scalars().all()
        return orders

    def create(self, order: Order) -> Order:
        if order.id is not None:
            raise AlreadyExistsException("Order id should be None when creating new Order")

        orm_order: OrderTable = OrderTable(
            phone_number=order.phone_number,
            email=order.email,
            order_time=order.order_time,
            status=order.status,
            product_snapshots=[self._snapshot_to_orm(s) for s in order.product_snapshots],
            checkout=self._checkout_to_orm(order.checkout) if order.checkout is not None else None
        )
        self._session.add(orm_order)
        self._session.flush()

        return self._order_to_domain(orm_order)

    def update(self, order: Order) -> None:
        if order.id is None:
            raise ValueError("order.id is required")
        
        orm_orders: list[OrderTable] = self._get_orm_orders(order.id)
        if not orm_orders:
            raise NotFoundException(f"Order with id={order.id} not found")

        orm_order = orm_orders[0]

        orm_order.phone_number = order.phone_number
        orm_order.email = order.email
        orm_order.order_time = order.order_time
        orm_order.status = order.status
        orm_order.product_snapshots = [self._snapshot_to_orm(s) for s in order.product_snapshots]
        if order.checkout is not None:
            if orm_order.checkout is not None:
                orm_order.checkout.provider = order.checkout.provider
                orm_order.checkout.session_id = order.checkout.session_id
            else:
                orm_order.checkout = self._checkout_to_orm(order.checkout)

        self._session.flush()

    def remove(self, order: Order) -> None:
        if order.id is None:
            raise ValueError("order.id is required")
        
        orm_orders: list[OrderTable] = self._get_orm_orders(order.id)
        if not orm_orders:
            raise NotFoundException(f"Order with id={order.id} not found")

        self._session.delete(orm_orders[0])
        self._session.flush()

    def get_by_id(self, order_id: int) -> Order | None:
        orm_orders: list[OrderTable] = self._get_orm_orders(order_id=order_id)
        if not orm_orders:
            return None 

        return self._order_to_domain(orm_orders[0])

    def get_by_phone_number(self, phone_number: str) -> list[Order]:
        orm_orders: list[OrderTable] = self._get_orm_orders(phone_number=phone_number)
        return [self._order_to_domain(order) for order in orm_orders]
        
    def get_by_email(self, email: str) -> list[Order]:
        orm_orders: list[OrderTable] = self._get_orm_orders(email=email)
        return [self._order_to_domain(order) for order in orm_orders]

    def get_all(self) -> list[Order]:
        orm_orders: list[OrderTable] = self._get_orm_orders()
        return [self._order_to_domain(order) for order in orm_orders]
        
