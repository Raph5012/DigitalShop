from enum import Enum


class OrderStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"
    refunded = "refunded"
    delivered = "delivered"


class UserRole(str, Enum):
    user = "user"
    admin = "admin"
