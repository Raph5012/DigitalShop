from repositories.category_repository import CategoryRepositoryProtocol
from repositories.product_repository import ProductRepositoryProtocol
from .exceptions import NotFoundException, AlreadyExistsException, CategoryError
from repositories.models import Category


class CategoryService:
    def __init__(
        self,
        categories: CategoryRepositoryProtocol,
        products: ProductRepositoryProtocol
    ):
        self._categories = categories
        self._products = products

    def create_category(self, category: Category) -> Category:
        if category.id is not None:
            raise AlreadyExistsException("Category id must be None when creating a new category")

        self._ensure_name_is_available(category.name)

        return self._categories.create_category(category)

    def update_category(self, category: Category) -> None:
        if category.id is None:
            raise NotFoundException("Category id must not be None when updating a category")

        existing = self._categories.get_category_by_id(category.id)
        if existing is None:
            raise NotFoundException(f"Category with id={category.id} not found")

        if existing.name != category.name:
            self._ensure_name_is_available(category.name)

        self._categories.update_category(category)

    def remove_category(self, category_id: int) -> None:
        if self._categories.get_category_by_id(category_id) is None:
            raise NotFoundException(f"Category with id={category_id} not found")

        if self._products.get_products_by_category(category_id):
            raise CategoryError(f"Category with id={category_id} cannot be removed because it still contains product")

        self._categories.remove_category(category_id)

    def get_category_by_id(self, category_id: int) -> Category:
        category = self._categories.get_category_by_id(category_id)
        if category is None:
            raise NotFoundException(f"Category with id={category_id} not found")

        return category

    def get_category_by_name(self, name: str) -> Category:
        category = self._categories.get_category_by_name(name)
        if category is None:
            raise NotFoundException(f"Category with name='{name}' not found")

        return category

    def get_all_categories(self) -> list[Category]:
        return self._categories.get_all_categories()

    def _ensure_name_is_available(self, name: str) -> None:
        if not name.strip():
            raise ValueError("Category must not be empty")

        if self._categories.get_category_by_name(name) is not None:
            raise AlreadyExistsException(f"Category with name='{name}' already exists")

    
    
    

    