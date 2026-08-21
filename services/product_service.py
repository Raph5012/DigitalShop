# PRODUCTS:
# * User should be able to see products, information, images and prices.
# * User should be able to add and remove products from cart, which is stored in local storage. (front end)

from typing import Protocol
from pydantic import BaseModel
from repositories.product_repository import ProductRepositoryProtocol
from repositories.models import Product, ProductImage as Image, PriceType


class ProductPreview(BaseModel):
    model_config = {"frozen": True}

    id: int
    name: str
    description: str
    price: PriceType | None
    main_image: Image | None


class ProductDetails(BaseModel):
    model_config = {"frozen": True}

    id: int
    category_id: int
    name: str
    description: str
    images: list[Image]
    price: PriceType | None


class ProductServiceProtocol(Protocol):
    def create(self, product: Product) -> Product:
        ...

    def update(self, product: Product) -> None:
        ...

    def remove(self, product_id: int) -> None:
        ...

    def get_full(self, product_id: int) -> Product | None:
        ...

    def get_preview(self, product_id: int) -> ProductPreview | None:
        ...

    def get_details(self, product_id: int) -> ProductDetails | None:
        ...

    def list_previews(self, category_id: int | None = None) -> list[ProductPreview]:
        ...


class ProductService(ProductServiceProtocol):
    def __init__(self, product_repository: ProductRepositoryProtocol) -> None:
        self._repo = product_repository

    def _get_current_price(self, product: Product) -> PriceType | None:
        for price in product.prices:
            if price.is_active_now():
                return price.price

        return None

    def _get_main_image(self, product: Product) -> Image | None:
        if not product.images:
            return None
        
        return sorted(product.images, key=lambda img: img.order)[0]

    def _product_to_preview(self, product: Product) -> ProductPreview:
        return ProductPreview(
            id=product.id,
            name=product.name,
            description=product.description,
            price=self._get_current_price(product),
            main_image=self._get_main_image(product)
        )

    def create(self, product: Product) -> Product:
        return self._repo.create_product(product)

    def update(self, product: Product) -> None:
        self._repo.update_product(product)

    def remove(self, product_id: int) -> None:
        self._repo.remove_product(product_id)

    def get_full(self, product_id: int) -> Product | None:
        return self._repo.get_by_id(product_id)

    def get_preview(self, product_id: int) -> ProductPreview | None:
        product: Product | None = self._repo.get_by_id(product_id)
        if product is None or product.hidden:
            return None

        return self._product_to_preview(product)

    def get_details(self, product_id: int) -> ProductDetails | None:
        product: Product | None = self._repo.get_by_id(product_id)
        if product is None or product.hidden:
            return None

        return ProductDetails(
            id=product_id,
            category_id=product.category_id,
            name=product.name,
            description=product.description,
            images=product.images,
            price=self._get_current_price(product)
        )

    def list_previews(self, category_id: int | None = None) -> list[ProductPreview]:
        if category_id is None:
            products: list[Product] = self._repo.get_all_products()
        else:
            products: list[Product] = self._repo.get_products_by_category(category_id)

        visible = [product for product in products if not product.hidden]
        return [self._product_to_preview(product) for product in visible]
