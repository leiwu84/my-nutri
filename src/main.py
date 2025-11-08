import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import Session, SQLModel, select

from src.database.database import DB_ENGINE
from src.database.models import (
    DATETIME_FORMAT,
    Consumption,
    ConsumptionCreate,
    ConsumptionKind,
    ConsumptionPatch,
    ConsumptionPublic,
    Food,
    FoodCreate,
    FoodPublic,
    Recipe,
    RecipeCreate,
    RecipeFoodLink,
    RecipePublic,
    consumption_to_consumption_public,
    recipe_to_recipe_public,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the db and the tables at startup, if they don't exist yet
    SQLModel.metadata.create_all(DB_ENGINE)
    yield


def get_session():
    """Create a new session for each request.
    Make it as a dependency so that it can be used in the FastAPI routes.
    """
    with Session(DB_ENGINE) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def check_health():
    return {"status": "OK"}


@app.post("/foods/")
async def create_foods(foods: list[FoodCreate], session: SessionDep):
    if not foods:
        return

    try:
        existing = []
        for food in foods:
            # Check existing to avoid duplicates
            statement = select(Food).where(
                Food.name == food.name, Food.kind == food.kind
            )
            existing_food = session.exec(statement).one_or_none()
            if existing_food:
                existing.append(existing_food)
                continue

            food_new = Food.model_validate(food)
            session.add(food_new)
        session.commit()
        return {
            "detail": f"Created {len(foods) - len(existing)} food items; skipped {len(existing)} duplicates based on name and kind."
        }
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail=f"Food already exists: name {food.name}."
        )
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.get("/foods/", response_model=list[FoodPublic])
async def read_foods(
    session: SessionDep, offset: int = 0, limit: int = Query(default=5, ge=1, le=100)
):
    try:
        foods = session.exec(select(Food).offset(offset).limit(limit)).all()
        return foods
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.get("/foods/{food_id}", response_model=FoodPublic)
async def read_food(food_id: int, session: SessionDep):
    try:
        food = session.get(Food, food_id)
        if not food:
            raise HTTPException(
                status_code=404, detail=f"Food with ID {food_id} not found."
            )
        return food
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.get("/foods_by_name_kind/{food_name}", response_model=list[FoodPublic])
async def read_food_by_name_kind(
    session: SessionDep, food_name: str, food_kind: str | None = None
):
    if not food_name:
        return []
    try:
        if food_kind:
            food = session.exec(
                select(Food).where(Food.name == food_name, Food.kind == food_kind)
            ).one()
            return [food]

        foods = session.exec(select(Food).where(Food.name == food_name)).all()
        return foods
    except NoResultFound:  # .one() raises NoResultFound if no results are found
        raise HTTPException(
            status_code=404,
            detail=f"Food not found: name {food_name} and kind {food_kind}.",
        )
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.patch("/foods/{food_id}", response_model=FoodPublic)
async def update_food(food_id: int, food: FoodCreate, session: SessionDep):
    try:
        food_db = session.get(Food, food_id)
        if not food_db:
            raise HTTPException(
                status_code=404, detail=f"Food with ID {food_id} not found."
            )

        food_new = food.model_dump(exclude_unset=True)
        food_db.sqlmodel_update(food_new)
        session.add(food_db)
        session.commit()
        session.refresh(food_db)
        return food_db
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.delete("/foods/{food_id}")
async def delete_food(food_id: int, session: SessionDep):
    try:
        food = session.get(Food, food_id)
        if not food:
            raise HTTPException(
                status_code=404, detail=f"Food with ID {food_id} not found."
            )

        session.delete(food)
        session.commit()
        return {"detail": f"Food with ID {food_id} deleted."}
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.post("/recipes/")
async def create_recipes(recipes: list[RecipeCreate], session: SessionDep):
    if not recipes:
        return

    try:
        existing = []
        for recipe in recipes:
            # Check existing to avoid duplicates
            statement = select(Recipe).where(
                Recipe.name == recipe.name, Recipe.kind == recipe.kind
            )
            existing_recipe = session.exec(statement).one_or_none()
            if existing_recipe:
                existing.append(existing_recipe)
                continue

            recipe_new = Recipe.model_validate(recipe)
            for food_input in recipe.foods:

                food = session.exec(
                    select(Food).where(
                        Food.name == food_input.name, Food.kind == food_input.kind
                    )
                ).one()

                link_new = RecipeFoodLink(
                    recipe=recipe_new,
                    food=food,
                    amount=food_input.amount,
                    unit=food_input.unit,
                )

                # No need to add recipe_new separately, as it will be added via the link_new relationship
                session.add(link_new)

        session.commit()
        return {
            "detail": f"Created {len(recipes) - len(existing)} recipes; skipped {len(existing)} duplicates based on name and kind."
        }
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"Recipe already exists: name {recipe.name} and kind {recipe.kind}.",
        )
    except NoResultFound:  # .one() raises NoResultFound if no results are found
        raise HTTPException(
            status_code=404,
            detail=f"Food not found when creating recipe: {food_input.name} and kind {food_input.kind}.",
        )
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.get("/recipes/", response_model=list[RecipePublic])
async def read_recipes(
    session: SessionDep, offset: int = 0, limit: int = Query(default=5, ge=1, le=100)
):
    try:
        recipes = session.exec(select(Recipe).offset(offset).limit(limit)).all()
        recipes_public = []
        for recipe in recipes:
            recipe_public = recipe_to_recipe_public(recipe=recipe)
            recipes_public.append(recipe_public)
        return recipes_public
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.get("/recipes/{recipe_id}", response_model=RecipePublic)
async def read_recipe(recipe_id: int, session: SessionDep):
    try:
        recipe = session.get(Recipe, recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=404, detail=f"Recipe with ID {recipe_id} not found."
            )
        recipe_public = recipe_to_recipe_public(recipe=recipe)
        return recipe_public
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.get("/recipes_by_name_kind/{recipe_name}", response_model=list[RecipePublic])
async def read_recipe_by_name_kind(
    session: SessionDep, recipe_name: str, recipe_kind: str | None = None
):
    if not recipe_name:
        return []
    try:
        if recipe_kind:
            recipe = session.exec(
                select(Recipe).where(
                    Recipe.name == recipe_name, Recipe.kind == recipe_kind
                )
            ).one()
            recipes = [recipe]
        else:
            recipes = session.exec(
                select(Recipe).where(Recipe.name == recipe_name)
            ).all()

        recipes_public = []
        for recipe in recipes:
            recipe_public = recipe_to_recipe_public(recipe=recipe)
            recipes_public.append(recipe_public)
        return recipes_public

    except NoResultFound:  # .one() raises NoResultFound if no results are found
        raise HTTPException(
            status_code=404,
            detail=f"Recipe not found: name {recipe_name} and kind {recipe_kind}.",
        )
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.patch("/recipes/{recipe_id}", response_model=RecipePublic)
async def update_recipe(recipe_id: int, recipe: RecipeCreate, session: SessionDep):
    try:
        recipe_db = session.get(Recipe, recipe_id)
        if not recipe_db:
            raise HTTPException(
                status_code=404, detail=f"Recipe with ID1 {recipe_id} not found."
            )

        recipe_new = recipe.model_dump(exclude_unset=True)
        recipe_db.sqlmodel_update(recipe_new)
        session.add(recipe_db)
        session.commit()
        session.refresh(recipe_db)
        return recipe_db
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: int, session: SessionDep):
    try:
        recipe = session.get(Recipe, recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=404, detail=f"Recipe with ID {recipe_id} not found."
            )

        session.delete(recipe)
        session.commit()
        return {"detail": f"Recipe with ID {recipe_id} deleted."}
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.post("/consumptions/")
async def create_consumption(
    consumptions: list[ConsumptionCreate], session: SessionDep
):
    if not consumptions:
        return

    try:
        for consumption_input in consumptions:
            timestamp = datetime.strptime(
                consumption_input.timestamp, DATETIME_FORMAT
            ).replace(tzinfo=timezone.utc)

            if consumption_input.kind == ConsumptionKind.RECIPE:
                recipe = session.exec(
                    select(Recipe).where(
                        Recipe.name == consumption_input.item_name,
                        Recipe.kind == consumption_input.item_kind,
                    )
                ).one()
                consumption = Consumption(
                    timestamp=timestamp,
                    recipe_id=recipe.id,
                    amount=consumption_input.amount,
                    unit=consumption_input.unit,
                )

            elif consumption_input.kind == ConsumptionKind.FOOD:
                food = session.exec(
                    select(Food).where(
                        Food.name == consumption_input.item_name,
                        Food.kind == consumption_input.item_kind,
                    )
                ).one()
                consumption = Consumption(
                    timestamp=timestamp,
                    food_id=food.id,
                    amount=consumption_input.amount,
                    unit=consumption_input.unit,
                )

            session.add(consumption)
        session.commit()
        return {"detail": f"{len(consumptions)} consumptions created successfully."}
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"Consumption with ID {consumption.id} already exists.",
        )
    except NoResultFound:  # .one() raises NoResultFound if no results are found
        raise HTTPException(
            status_code=404,
            detail=f"Item not found when creating consumption: consumption kind {consumption_input.kind}, item name {consumption_input.item_name}, and item kind {consumption_input.item_kind}.",
        )
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.get("/consumptions/", response_model=list[ConsumptionPublic])
async def read_consumptions(
    session: SessionDep, offset: int = 0, limit: int = Query(default=5, ge=1, le=100)
):
    try:
        consumptions = session.exec(
            select(Consumption).offset(offset).limit(limit)
        ).all()
        consumptions_public = []
        for consumption in consumptions:
            consumption_public = consumption_to_consumption_public(
                consumption=consumption, session=session
            )
            consumptions_public.append(consumption_public)
        return consumptions_public
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.get("/consumptions/{consumption_id}", response_model=ConsumptionPublic)
async def read_consumption(consumption_id: int, session: SessionDep):
    try:
        consumption = session.get(Consumption, consumption_id)
        if not consumption:
            raise HTTPException(
                status_code=404,
                detail=f"Consumption with ID {consumption_id} not found.",
            )
        return consumption_to_consumption_public(
            consumption=consumption, session=session
        )
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.get("/consumptions_by_duration/")
async def read_consumptions_by_duration(
    start_timestamp: str, end_timestamp: str, session: SessionDep
):
    try:
        start_ts = datetime.strptime(start_timestamp, DATETIME_FORMAT).replace(
            tzinfo=timezone.utc
        )
        end_ts = datetime.strptime(end_timestamp, DATETIME_FORMAT).replace(
            tzinfo=timezone.utc
        )

        consumptions = session.exec(
            select(Consumption).where(
                Consumption.timestamp >= start_ts, Consumption.timestamp <= end_ts
            )
        ).all()

        return [
            consumption_to_consumption_public(consumption=consumption, session=session)
            for consumption in consumptions
        ]
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.patch("/consumptions/{consumption_id}")
async def update_consumption(
    consumption_id: int, consumption: ConsumptionPatch, session: SessionDep
):
    try:
        consumption_db = session.get(Consumption, consumption_id)
        if not consumption_db:
            raise HTTPException(
                status_code=404,
                detail=f"Consumption with ID {consumption_id} not found.",
            )

        consumption_input = consumption.model_dump(exclude_unset=True)
        consumption_db.sqlmodel_update(consumption_input)
        session.add(consumption_db)
        session.commit()
        return {"detail": f"Consumption with ID {consumption_id} updated."}
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)


@app.delete("/consumptions/{consumption_id}")
async def delete_consumption(consumption_id: int, session: SessionDep):
    try:
        consumption = session.get(Consumption, consumption_id)
        if not consumption:
            raise HTTPException(
                status_code=404,
                detail=f"Consumption with ID {consumption_id} not found.",
            )

        session.delete(consumption)
        session.commit()
        return {"detail": f"Consumption with ID {consumption_id} deleted."}
    except Exception:
        msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=msg)
