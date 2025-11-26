"""Schema definitions for the food chatbot application.

This module defines Pydantic models used for data validation and serialization
throughout the chatbot application, including nutrition filtering, recipe metadata,
and database query parameters.

Author: FoodChatbot Team
Version: 1.0.0
"""

from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field

from .chroma_manager import db_manager


# Create dynamic nutrition key enum from database
# Reuse the singleton db_manager instance to avoid duplicate initialization
nutrition_keys = {key: key for key in db_manager.set_of_nuts.keys()}
NutritionKey = Enum('NutritionKey', nutrition_keys)


class NutritionItem(BaseModel):
    """Represents a single nutrition key-value pair for filtering.
    
    This class defines a nutrition constraint with a key (e.g., 'calories'),
    value (e.g., 500), and optional unit multiplier for conversion.
    
    Attributes:
        key: The nutrition parameter to filter by (calories, protein, etc.)
        multiply: Unit conversion multiplier (e.g., 1000 for mg to g)
        value: The nutrition value threshold in the specified unit
        
    Example:
        >>> nutrition_item = NutritionItem(
        ...     key=NutritionKey.calories,
        ...     value=500.0,
        ...     multiply=1
        ... )
    """
    
    key: NutritionKey
    multiply: int = Field(
        default=1,
        description="Multiplier for unit conversion (e.g., 1000 for mg to g)."
    )
    value: float = Field(description="Nutrition value in the specified unit")


class Filter(BaseModel):
    """Pydantic model for generating ChromaDB filters with sorting support.
    
    This class represents search and filter criteria for recipe queries,
    including time constraints, serving sizes, nutritional requirements,
    and result sorting preferences.
    
    Attributes:
        prep_time_min: Minimum preparation time in minutes
        prep_time_max: Maximum preparation time in minutes
        cook_time_min: Minimum cooking time in minutes
        cook_time_max: Maximum cooking time in minutes
        servings_min: Minimum number of servings
        servings_max: Maximum number of servings
        dict_nutrition_min: List of minimum nutrition value constraints
        dict_nutrition_max: List of maximum nutrition value constraints
        sort_by_nutrition: Nutrition key to sort results by
        sort_order: Sort direction ('asc' for ascending, 'desc' for descending)
        result_limit: Maximum number of results to return
        
    Example:
        >>> recipe_filter = Filter(
        ...     prep_time_max=30,
        ...     dict_nutrition_max=[
        ...         NutritionItem(key=NutritionKey.calories, value=500.0)
        ...     ],
        ...     sort_by_nutrition=NutritionKey.calories,
        ...     sort_order="asc",
        ...     result_limit=10
        ... )
    """
    
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
    """Model for standard nutrition values with common dietary metrics.
    
    This class represents the basic nutritional information for recipes,
    containing the most commonly requested dietary metrics.
    
    Attributes:
        calories: Energy content in kilocalories (kcal)
        protein: Protein content in grams (g)
        fat: Total fat content in grams (g)
        carbohydrates: Total carbohydrate content in grams (g)
        sugar: Sugar content in grams (g)
        sodium: Sodium content in milligrams (mg)
        
    Example:
        >>> nutrition = Nutrition(
        ...     calories=350.0,
        ...     protein=25.0,
        ...     fat=12.0,
        ...     carbohydrates=40.0,
        ...     sugar=8.0,
        ...     sodium=650.0
        ... )
    """
    
    calories: Optional[float] = Field(None, description="Calories in kcal")
    protein: Optional[float] = Field(None, description="Protein in grams")
    fat: Optional[float] = Field(None, description="Fat in grams")
    carbohydrates: Optional[float] = Field(None, description="Carbohydrates in grams")
    sugar: Optional[float] = Field(None, description="Sugar in grams")
    sodium: Optional[float] = Field(None, description="Sodium in milligrams")
