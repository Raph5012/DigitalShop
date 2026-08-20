from repositories.category_repository import CategoryRepositoryProtocol
from repositories.models import Category
from typing import Protocol


class CategoryServiceProtocol(Category):
    def get(self, category_id: int) -> 