# my-nutri
MyNutri – Track your meals, log nutrition for foods, and calculate nutrition for your recipes.

## Highlights
1. The foods/meals that **you** eat.
1. Identity your food and meal by the combination of name and kind. 
    
    !!! note

        Having a common name while further distinguished by kind allows easier query of all kinds of items that share the same name.

    !!! example

        1. `Apple` is a food name; while `Fuji` is its food kind.
        1. `Chia Seed Pudding` is a meal name; while `with Milk`, `with Yogurt`, and `with Mango Juice` can be its meal kind, so that you can easily record variations of your meal.

1. The consumption table allows you to specify the portion (in the unit of percentage [%]) of a meal. **Very useful when you cook for your family and you measure the amount of the ingradients for the whole meal, and you only eat a portion.**



## Introduction
This is a simple Python application that you can install and run locally on your computer: Windows, Linux, Mac.

**UI** - Swagger UI by `Uvicorn` and `FastAPI`.
**Backend** - Python
**Database** - SQLite3


## Installation
1. `git clone` or download this repo to your local machine.
1. Change directory to this repo, and create a dedicated Python virtual environment.

    ```terminal
    python -m venv venv
    ```

1. Acitvate the environment

    Windows
    
    ```terminal
    venv\Scripts\activate
    ```

    Linux/Mac

    ```terminal
    source venv/bin/activate
    ```

1. Install

    ```
    pip install -e .
    ```

## How to Use
1. Make sure you have changed directory to this repo and activated the dedicated Python virtual environment.
1. Run this command

    ```terminal
    fastapi dev main.py
    ```
1. Use
    1. **UI** - Visit <http://127.0.0.1:8000/docs> with your browser.
    1. **API** - URL <http://127.0.0.1:8000>. Call with any (separate) application, e.g. using Python `request` library.