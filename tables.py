from sqlalchemy import String, Integer, ForeignKey, Double, DateTime, Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship, mapped_column, Mapped
from datetime import datetime

from enums import OrderStatus, UserRole


Base = declarative_base()


class ProductTable(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    product_images = relationship("ProductImageTable", back_populates="product", cascade="all, delete-orphan")
    price = relationship("PriceTable", back_populates="product", cascade="all, delete-orphan")
    file_path = relationship("FilePathTable", back_populates="product", cascade="all, delete-orphan")
    download_links = relationship("DownloadLinkTable", back_populates="product", cascade="all, delete-orphan")

class CategoryTable(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)


class ProductImageTable(Base):
    __tablename__ = "product_images"

    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    image_path: Mapped[str] = mapped_column(String, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    product = relationship("ProductTable", back_populates="product_images")


class PriceTable(Base):
    __tablename__ = "prices"

    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    price: Mapped[float] = mapped_column(Double, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=False)

    product = relationship("ProductTable", back_populates="price")


class FilePathTable(Base):
    __tablename__ = "file_paths"

    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)

    product = relationship("ProductTable", back_populates="file_path")


class DownloadLinkTable(Base):
    __tablename__ = "download_links"

    file_path: Mapped[int] = mapped_column(Integer, ForeignKey("file_paths.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=False)

    product = relationship("ProductTable", back_populates="download_links")


class OrderTable(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    order_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), nullable=False)

    order_products = relationship("OrderProductTable", back_populates="order", cascade="all, delete-orphan")


class OrderProductTable(Base):
    __tablename__ = "order_products"

    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)

    order = relationship("OrderTable", back_populates="order_products")


class AccountTable(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)
    password_hash: Mapped[String] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False, default=UserRole.user)

    sessions = relationship("SessionTable", back_populates="account", cascade="all, delete-orphan")


class SessionTable(Base):
    __tablename__ = "sessions"

    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    account = relationship("AccountTable", back_populates="sessions")



