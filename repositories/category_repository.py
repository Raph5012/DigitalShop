from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Protocol
from database.tables import CategoryTable
from .exceptions import *
from .models import Category


class CategoryRepositoryProtocol(Protocol):
    def create_category(self, category: Category) -> Category:
        ...

    def update_category(self, category: Category) -> None:
        ...

    def remove_category(self, category_id: int) -> None:
        ...

    def get_category_by_id(self, category_id: int) -> Category | None:
        ...

    def get_category_by_name(self, name: str) -> Category | None:
        ...

    def get_all_categories(self) -> list[Category]:
        ...


class CategoryRepository(CategoryRepositoryProtocol):
    def __init__(self, db_session: Session) -> None:
        self._session = db_session

    @staticmethod
    def to_orm(category: Category) -> CategoryTable:
        return CategoryTable(
            id=category.id,
            name=category.name,
            description=category.description
        )

    @staticmethod
    def to_domain(category: CategoryTable) -> Category:
        return Category(
            id=category.id,
            name=category.name,
            description=category.description
        )
        
    def create_category(self, category: Category) -> Category:
        if category.id is not None:
            raise AlreadyExistsException("object id is expected to be None when creating object")
        
        category_orm: CategoryTable = self.to_orm(category)
        self._session.add(category_orm)
        self._session.flush()
        return self.to_domain(category_orm)

    def update_category(self, category: Category) -> None:
        category_orm: CategoryTable | None = self._session.get(CategoryTable, category.id)
        if category_orm is None:
            raise NotFoundException(f"Category with id={category.id} not found")

        category_orm.name = category.name
        category_orm.description = category.description

        self._session.flush()

    def remove_category(self, category_id: int) -> None:
        category_orm: CategoryTable | None = self._session.get(CategoryTable, category_id)
        if category_orm is None:
            raise NotFoundException(f"Category with id={category_id} not found")

        self._session.delete(category_orm)
        self._session.flush()

    def get_category_by_id(self, category_id: int) -> Category | None:
        category_orm: CategoryTable | None = self._session.get(CategoryTable, category_id)

        if category_orm is None:
            return None

        return self.to_domain(category_orm)

    def get_all_categories(self) -> list[Category]:
        stmt = select(CategoryTable)
        categories: list[CategoryTable] = list(self._session.scalars(stmt).all())
        return [self.to_domain(category) for category in categories]

    def get_category_by_name(self, name: str) -> Category | None:
        stmt = select(CategoryTable).where(CategoryTable.name == name)
        category_orm: CategoryTable | None = self._session.scalars(stmt).one_or_none()

        if category_orm is None:
            return None
        
        return self.to_domain(category_orm)
