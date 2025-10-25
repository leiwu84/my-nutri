# my-nutri
MyNutri – Track your meals, log nutrition for foods, and calculate nutrition for your recipes.

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