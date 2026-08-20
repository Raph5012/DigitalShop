from pydantic import BaseModel, Field, AfterValidator, field_validator, EmailStr
from typing import Annotated, Any, Optional
from datetime import datetime, timezone
from re import fullmatch
from decimal import Decimal
from .config import MAX_LENGTH_FOR_NAMES
from database import enums


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(timezone.utc)


def ensure_utc_or_none(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def ensure_non_negative(price: Decimal) -> Decimal:
    if price < 0:
        raise ValueError("Invalid price given")

    return price


UtcDatetime = Annotated[datetime, AfterValidator(ensure_utc)]
UtcDatetimeOrNone = Annotated[datetime | None, AfterValidator(ensure_utc_or_none)]
PriceType = Annotated[Decimal, Field(max_digits=10, decimal_places=2), AfterValidator(ensure_non_negative)]


class Product(BaseModel):
    id: int | None = None
    category_id: int
    name: str = Field(max_length=MAX_LENGTH_FOR_NAMES)
    description: str

    images: list['ProductImage'] = Field(default_factory=list)
    prices: list['ProductPrice'] = Field(default_factory=list)
    download_paths: list['FilePath'] = Field(default_factory=list)

    @field_validator('prices', mode='after')
    @classmethod
    def _ensure_only_one_valid_price(cls, prices: list['ProductPrice']) -> list['ProductPrice']:
        price_found: bool = False
        for price in prices:
            if not price.is_active_now():
                continue

            if price_found:
                raise ValueError("Too many valid prices at the time")

            price_found = True

        return prices

    @field_validator('images', mode='after')
    @classmethod
    def _ensure_no_images_with_the_same_order(cls, images: list['ProductImage']) -> list['ProductImage']:
        image_orders = [image.order for image in images]
        if len(set(image_orders)) == len(image_orders):
            return images 
        else:
            raise ValueError("At least two images have the same order")

    @field_validator('download_paths', mode='after')
    @classmethod
    def _ensure_at_least_one_download(cls, downloads: list['FilePath']) -> list['FilePath']:
        if downloads:
            return downloads
        else:
            raise ValueError("Product requires at least one download file.")


class Category(BaseModel):
    id: int | None = None
    name: str = Field(max_length=MAX_LENGTH_FOR_NAMES)
    description: str


class ProductImage(BaseModel):
    model_config = {"frozen": True}

    image_path: str
    order: int

    @field_validator('order', mode='after')
    @classmethod
    def _check_order_positive(cls, order: int) -> int:
        if order <= 0:
            raise ValueError("image order must be greater than 0")

        return order


class ProductPrice(BaseModel):
    model_config = {"frozen": True}

    price: PriceType
    valid_from: UtcDatetime
    valid_to: UtcDatetimeOrNone

    def is_active_now(self) -> bool:
        now = datetime.now(timezone.utc)
        return self.valid_from < now and (self.valid_to is None or self.valid_to > now)


class FilePath(BaseModel):
    model_config = {"frozen": True}

    path: str

    @field_validator("path", mode='after')
    @classmethod
    def validate_path(cls, path: str) -> str:
        if not path.startswith("/"):
            raise ValueError("Path to file must start with a slash")

        return path


class DownloadLink(BaseModel):
    id: int | None = None
    product_id: int
    created_at: UtcDatetime
    valid_until: UtcDatetimeOrNone
    revoked_at: UtcDatetimeOrNone


class Order(BaseModel):
    id: int | None = None
    phone_number: str
    email: EmailStr
    order_time: UtcDatetime
    status: enums.OrderStatus
    product_snapshots: list['ProductSnapshot'] = Field(default_factory=list)
    checkout: Optional['Checkout'] = None

    @field_validator('phone_number', mode='after')
    @classmethod
    def validate_phone_number(cls, phone_number: str) -> str:
        if not fullmatch(r"^\+\d{6,15}$", phone_number):
            raise ValueError("Invalid phone number format")

        return phone_number

    @field_validator('email', mode='after')
    @classmethod
    def casefold_email(cls, email: str) -> str:
        return email.casefold()

    @field_validator('product_snapshots', mode='after')
    @classmethod
    def check_for_at_least_one_order_product(cls, products: list['ProductSnapshot']) -> list['ProductSnapshot']:
        if len(products) == 0:
            raise ValueError("Product count must be greater than 0")

        return products


class ProductSnapshot(BaseModel):
    model_config = {"frozen": True}

    name: str = Field(max_length=MAX_LENGTH_FOR_NAMES)
    price: PriceType
    product_id: int


class Checkout(BaseModel):
    model_config = {"frozen": True}

    id: int | None = None
    order_id: int
    provider: enums.CheckoutProvider
    session_id: str


class Account(BaseModel):
    id: int | None = None
    username: str = Field(max_length=MAX_LENGTH_FOR_NAMES)
    email: EmailStr
    phone_number: str | None
    password_hash: str
    role: enums.UserRole

    @field_validator('phone_number', mode='after')
    @classmethod
    def validate_phone_number(cls, phone_number: str | None) -> str | None:
        if phone_number is None:
            return None

        if not fullmatch(r"^\+\d{6,15}$", phone_number):
            raise ValueError("Invalid phone number format")

        return phone_number

    @field_validator('email', mode='after')
    @classmethod
    def casefold_email(cls, email: str) -> str:
        return email.casefold()


class Session(BaseModel):
    id: int | None = None
    account_id: int
    created_at: UtcDatetime
    ends_at: UtcDatetime
    revoked_at: UtcDatetimeOrNone
    session_token_hash: str
