from typing import Protocol
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from .models import Product, ProductImage as Image, ProductPrice as Price, FilePath
from .exceptions import *
from database.tables import ProductTable, ProductImageTable, PriceTable, FilePathTable



class ProductRepositoryProtocol(Protocol):
    def create_product(self, product: Product) -> Product:
        ...

    def update_product(self, product: Product) -> None:
        ...

    def remove_product(self, product_id: int) -> None:
        ...

    def get_by_id(self, product_id: int) -> Product | None:
        ...

    def get_all_products(self) -> list[Product]:
        ...

    def get_products_by_category(self, category_id: int) -> list[Product]:
        ...


class ProductRepository(ProductRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _image_to_domain(self, orm_image: ProductImageTable) -> Image:
        return Image(
            image_path=orm_image.image_path,
            order=orm_image.order
        )

    def _image_to_orm(self, image: Image) -> ProductImageTable:
        return ProductImageTable(
            image_path=image.image_path,
            order=image.order
        )

    def _price_to_domain(self, price: PriceTable) -> Price:
        return Price(
            price=price.price,
            valid_from=price.valid_from,
            valid_to=price.valid_to
        )

    def _price_to_orm(self, price: Price) -> PriceTable:
        return PriceTable(
            price=price.price,
            valid_from=price.valid_from,
            valid_to=price.valid_to
        )

    def _file_path_to_domain(self, file_path: FilePathTable) -> FilePath:
        return FilePath(
            path=file_path.path
        )

    def _file_path_to_orm(self, file_path: FilePath) -> FilePathTable:
        return FilePathTable(
            path=file_path.path
        )

    def _product_to_domain(self, orm_product: ProductTable) -> Product:
        return Product(
            id=orm_product.id,
            category_id=orm_product.category_id,
            name=orm_product.name,
            description=orm_product.description,
            hidden=orm_product.hidden,
            images=[self._image_to_domain(img) for img in orm_product.product_images],
            prices=[self._price_to_domain(price) for price in orm_product.prices],
            download_paths=[self._file_path_to_domain(fp) for fp in orm_product.file_paths]
        )

    def _get_product_orm(self, product_id: int) -> ProductTable | None:
        stmt = (
                select(ProductTable)
                .where(ProductTable.id == product_id)
                .options(
                    selectinload(ProductTable.product_images),
                    selectinload(ProductTable.prices),
                    selectinload(ProductTable.file_paths)
                )
                )
        return self._session.execute(stmt).scalar_one_or_none()

    def _get_products(self, category_id: int | None = None) -> list[Product]:
        stmt = (
            select(ProductTable)
            .options(
                selectinload(ProductTable.product_images),
                selectinload(ProductTable.prices),
                selectinload(ProductTable.file_paths)
            )
        )

        if category_id is not None:
            stmt = stmt.where(ProductTable.category_id == category_id)

        products: list[ProductTable] = list(self._session.execute(stmt).scalars().all())
        return [self._product_to_domain(product) for product in products]
    
    def create_product(self, product: Product) -> Product:
        if product.id is not None:
            raise AlreadyExistsException(f"Product id should be None when creating new object")

        product_images: list[ProductImageTable] = [self._image_to_orm(img) for img in product.images]
        prices: list[PriceTable] = [self._price_to_orm(price) for price in product.prices]
        file_paths: list[FilePathTable] = [self._file_path_to_orm(fp) for fp in product.download_paths]

        orm_product = ProductTable(
            category_id=product.category_id,
            name=product.name,
            description=product.description,
            hidden=product.hidden,
            product_images=product_images,
            prices=prices,
            file_paths=file_paths
        )

        self._session.add(orm_product)
        self._session.flush()

        return self._product_to_domain(orm_product)
    
    def update_product(self, product: Product) -> None:
        orm_product: ProductTable | None = self._get_product_orm(product.id)

        if orm_product is None:
            raise NotFoundException(f"Product with id={product.id} not found")

        orm_product.category_id = product.category_id
        orm_product.name = product.name
        orm_product.description = product.description
        orm_product.hidden = product.hidden
        orm_product.product_images = [self._image_to_orm(img) for img in product.images]
        orm_product.prices = [self._price_to_orm(price) for price in product.prices]
        orm_product.file_paths = [self._file_path_to_orm(fp) for fp in product.download_paths]

        self._session.flush()

    def remove_product(self, product_id: int) -> None:
        orm_product: ProductTable | None = self._get_product_orm(product_id)
        
        if orm_product is None:
            raise NotFoundException(f"Product with id={product_id} not found")

        self._session.delete(orm_product)
        self._session.flush()

    def get_by_id(self, product_id: int) -> Product | None:
        orm_product: ProductTable | None = self._get_product_orm(product_id)

        if orm_product is None:
            return None

        return self._product_to_domain(orm_product)

    def get_all_products(self) -> list[Product]:
        return self._get_products()

    def get_products_by_category(self, category_id: int) -> list[Product]:
        return self._get_products(category_id=category_id)
    