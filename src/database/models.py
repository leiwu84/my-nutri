from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel

from src.database.unit import Unit

_DEFAULT_KIND = "General"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


class RecipeFoodLink(SQLModel, table=True):
    recipe_id: int | None = Field(
        default=None, foreign_key="recipe.id", primary_key=True
    )
    food_id: int | None = Field(default=None, foreign_key="food.id", primary_key=True)
    amount: float = Field(description="The amount of the food in this recipe")
    unit: str = Field(description="The unit of the amount of the food in this recipe")

    recipe: "Recipe" = Relationship(back_populates="food_links")
    food: "Food" = Relationship(back_populates="recipe_links")


class _FoodBase(SQLModel):
    name: str = Field(
        description="The name of the food, e.g. Apple, Tomato, etc. It must be unique. Use <name>-<kind> to differentiate different kinds of the same food. E.g. Apple-Fuji, etc.",
        index=True,
    )
    kind: str = Field(
        description="E.g. Fuji is a kind of apple, Sable is a kind of grape, etc.",
        default=_DEFAULT_KIND,
        index=True,
    )
    amount: float = Field(
        description="<amount><unit> is the reference for nutrition data of the food, e.g. 100g or 100ml",
        default=100.0,
    )
    unit: str = Field(
        description="<amount><unit> is the reference for nutrition data of the food, e.g. 100g or 100ml",
        default=Unit.GRAM,
        index=True,
    )
    calories: float | None = Field(
        description="Nutrition data in [kcal].", default=None
    )
    fat: float | None = Field(description="Nutrition data in [g].", default=None)
    fat_saturated: float | None = Field(
        description="Nutrition data in [g].", default=None
    )
    carbohydrates: float | None = Field(
        description="Nutrition data in [g].", default=None
    )
    sugars: float | None = Field(description="Nutrition data in [g].", default=None)
    fiber: float | None = Field(description="Nutrition data in [g].", default=None)
    protein: float | None = Field(description="Nutrition data in [g].", default=None)


class Food(_FoodBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    recipe_links: list[RecipeFoodLink] = Relationship(back_populates="food")


class FoodCreate(_FoodBase):
    pass


class FoodPublic(_FoodBase):
    id: int


class _RecipeBase(SQLModel):
    name: str = Field(
        description="The name of the recipe, e.g. Chia Seed Pudding. The name must be unique.",
        index=True,
        unique=True,
    )
    kind: str = Field(
        description="E.g. Chia Seed Pudding is a recipe name. But can be with different kind, e.g. with milk, with yogurt, or with mango juice, etc.",
        default=_DEFAULT_KIND,
        index=True,
    )


class Recipe(_RecipeBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    food_links: list[RecipeFoodLink] = Relationship(back_populates="recipe")


class _FoodInRecipe(SQLModel):
    name: str = Field(description="The ID of the food item in the recipe.")
    kind: str = Field(
        description="The kind of the food item in the recipe.", default=_DEFAULT_KIND
    )
    amount: float = Field(description="The amount of the food item in the recipe.")
    unit: Unit = Field(
        description="The unit of the amount of the food item in the recipe."
    )


class RecipeCreate(_RecipeBase):
    foods: list[_FoodInRecipe] = Field(
        description="The list of food items included in the recipe along with their amounts and units."
    )


class RecipePublic(_RecipeBase):
    id: int
    foods: list[_FoodInRecipe] = Field(
        description="The list of food items included in the recipe along with their amounts and units."
    )


class Consumption(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(
        description="UTC timestamp of consumption. Default to now.",
    )
    recipe_id: int | None = Field(
        default=None,
        description="The recipe consumed. If you eat a recipe, which is a pre-defined combination of food items, you can use this field.",
        foreign_key="recipe.id",
    )
    food_id: int | None = Field(
        default=None,
        description="The food item consumed. If you just eat a food not included in a recipe, you can use this field.",
        foreign_key="food.id",
    )
    amount: float | None = Field(
        description="The amount of the food item consumed. E.g., 150.0 means 150g or 150ml depending on the unit of the food item.",
        default=None,
    )
    unit: str | None = Field(
        description="The unit of the amount of the food item consumed. E.g., g, mL, or %, etc.",
        default=None,
    )


class ConsumptionKind(str, Enum):
    RECIPE = "Recipe"
    FOOD = "Food"


class ConsumptionCreate(SQLModel):
    timestamp: str = Field(
        description=f"Format: {DATETIME_FORMAT}. The app will convert it to ISO 8601 format automatically.",
    )
    kind: ConsumptionKind = Field(
        description="The kind of the item consumed, either a recipe or a food item.",
    )
    item_name: str = Field(
        description="The name of the recipe or food item consumed. The combined name and kind uniquely identify the item.",
    )
    item_kind: str = Field(
        description="The kind of the item consumed, for food, it is food kind; for recipe, it is recipe kind. The combined name and kind uniquely identify the item.",
        default=_DEFAULT_KIND,
    )
    amount: float | None = Field(
        description="The amount of the food/recipe consumed. E.g., 15.0 means 15g, 15mL, or 15% depending on the unit of the food/recipe.",
        default=None,
    )
    unit: str | None = Field(
        description="The unit of the amount of the food/recipe consumed. E.g., g, mL, or %, etc.",
        default=None,
    )


class ConsumptionPatch(SQLModel):
    """All attributes are optional for patching."""

    timestamp: str | None = Field(
        description=f"Format: {DATETIME_FORMAT}. The app will convert it to ISO 8601 format automatically.",
        default=None,
    )
    kind: ConsumptionKind | None = Field(
        description="The kind of the item consumed, either a recipe or a food item.",
        default=None,
    )
    item_name: str | None = Field(
        description="The name of the recipe or food item consumed. The combined name and kind uniquely identify the item.",
        default=None,
    )
    item_kind: str | None = Field(
        description="The kind of the item consumed, for food, it is food kind; for recipe, it is recipe kind. The combined name and kind uniquely identify the item.",
        default=_DEFAULT_KIND,
    )
    amount: float | None = Field(
        description="The amount of the food/recipe consumed. E.g., 15.0 means 15g, 15mL, or 15% depending on the unit of the food/recipe.",
        default=None,
    )
    unit: str | None = Field(
        description="The unit of the amount of the food/recipe consumed. E.g., g, mL, or %, etc.",
        default=None,
    )


class ConsumptionPublic(ConsumptionCreate):
    id: int


def recipe_to_recipe_public(recipe: Recipe) -> RecipePublic:
    """Convert Recipe to RecipePublic.

    Args:
        recipe (Recipe): The recipe should be retrieved from the database so that recipe.id is not None.

    Returns:
        RecipePublic
    """
    foods_in_recipe = []
    for link in recipe.food_links:
        food_in_recipe = _FoodInRecipe(
            name=link.food.name,
            kind=link.food.kind,
            amount=link.amount,
            unit=Unit(link.unit),
        )
        foods_in_recipe.append(food_in_recipe)

    assert (
        recipe.id is not None
    ), "recipe must be retrieved from the database, so recipe.id cannot be None"

    recipe_public = RecipePublic(
        id=recipe.id,
        name=recipe.name,
        kind=recipe.kind,
        foods=foods_in_recipe,
    )
    return recipe_public


def consumption_to_consumption_public(
    consumption: Consumption, session
) -> ConsumptionPublic:
    """Convert Consumption to ConsumptionPublic.

    Args:
        consumption (Consumption): The consumption should be retrieved from the database so that consumption.id is not None.

    Returns:
        ConsumptionPublic
    """
    assert (
        consumption.id is not None
    ), "consumption must be retrieved from the database, so consumption.id cannot be None"

    # Get item_name and item_kind
    if consumption.recipe_id is not None:
        recipe = session.get(Recipe, consumption.recipe_id)
        if recipe:
            item_name = recipe.name
            item_kind = recipe.kind
    elif consumption.food_id is not None:
        food = session.get(Food, consumption.food_id)
        if food:
            item_name = food.name
            item_kind = food.kind

    consumption_public = ConsumptionPublic(
        id=consumption.id,
        timestamp=consumption.timestamp.strftime(DATETIME_FORMAT),
        kind=(
            ConsumptionKind.RECIPE
            if consumption.recipe_id is not None
            else ConsumptionKind.FOOD
        ),
        item_name=item_name,
        item_kind=item_kind,
        amount=consumption.amount,
        unit=consumption.unit,
    )
    return consumption_public
