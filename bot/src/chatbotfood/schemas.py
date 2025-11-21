"""Schema definitions for the chatbot application."""

from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field

from .chroma_manager import db_manager


# Create dynamic nutrition key enum from database
# Reuse the singleton db_manager instance to avoid duplicate initialization
nutrition_keys = {key: key for key in db_manager.set_of_nuts.keys()}
NutritionKey = Enum('NutritionKey', nutrition_keys)


class NutritionItem(BaseModel):
    """Represents a single nutrition key-value pair for filtering."""
    
    key: NutritionKey
    multiply: int = Field(
        default=1,
        description="Multiplier for unit conversion (e.g., 1000 for mg to g)."
    )
    value: float = Field(description="Nutrition value in the specified unit")


class Filter(BaseModel):
    """Pydantic model for generating ChromaDB filters with sorting support."""
    
    prep_time_min: Optional[int] = Field(None, description="Minimum preparation time in minutes.")
    prep_time_max: Optional[int] = Field(None, description="Maximum preparation time in minutes.")
    cook_time_min: Optional[int] = Field(None, description="Minimum cooking time in minutes.")
    cook_time_max: Optional[int] = Field(None, description="Maximum cooking time in minutes.")
    servings_min: Optional[int] = Field(None, description="Minimum number of servings.")
    servings_max: Optional[int] = Field(None, description="Maximum number of servings.")
    dict_nutrition_min: Optional[List[NutritionItem]] = Field(
        None,
        description="List of minimum nutrition values."
    )
    dict_nutrition_max: Optional[List[NutritionItem]] = Field(
        None,
        description="List of maximum nutrition values."
    )
    sort_by_nutrition: Optional[NutritionKey] = Field(
        None,
        description="Nutrition key to sort results by (e.g., for 'lowest calories' or 'highest protein')"
    )
    sort_order: Optional[str] = Field(
        None,
        description="Sort order: 'asc' for lowest/ascending, 'desc' for highest/descending"
    )
    result_limit: Optional[int] = Field(
        10,
        description="Maximum number of results to return (e.g., 'top 10'). Default is 10 if not specified."
    )


class Nutrition(BaseModel):
    """Model for standard nutrition values with common dietary metrics."""
    
    calories: Optional[float] = Field(None, description="Calories in kcal")
    protein: Optional[float] = Field(None, description="Protein in grams")
    fat: Optional[float] = Field(None, description="Fat in grams")
    carbohydrates: Optional[float] = Field(None, description="Carbohydrates in grams")
    sugar: Optional[float] = Field(None, description="Sugar in grams")
    sodium: Optional[float] = Field(None, description="Sodium in milligrams")
