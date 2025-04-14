# controllers/recipe_controller.py

import json
import os

DATA_FILE = "data/recipes.json"
recipe_list = []

# ======================= DATA HANDLING =========================
def load_recipes():
    global recipe_list
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                recipe_list = json.load(f)
                print("📁 Recipes loaded successfully.")
            except json.JSONDecodeError:
                recipe_list = []
                print("⚠️ Corrupted recipe data, starting fresh.")
    else:
        recipe_list = []
        print("📁 No recipe data found, starting fresh.")

def save_recipes():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(recipe_list, f, indent=4, ensure_ascii=False)
    print("💾 Recipes saved successfully.")

# ======================= CORE FUNCTION =========================
def view_recipes():
    if not recipe_list:
        print("📭 No recipes available.")
        return
    print("\n📖 Recipe List:")
    for i, recipe in enumerate(recipe_list, start=1):
        print(f"{i}. {recipe['name']} | Ingredients: {', '.join(recipe['ingredients'])}")

def add_recipe():
    name = input("Recipe name: ").strip()
    if not name:
        print("❌ Name cannot be empty.")
        return

    ingredients = input("Enter ingredients (comma separated): ").split(",")
    ingredients = [i.strip() for i in ingredients if i.strip()]
    
    if not ingredients:
        print("❌ Invalid ingredients.")
        return

    recipe = {
        "name": name,
        "ingredients": ingredients
    }
    recipe_list.append(recipe)
    save_recipes()
    print(f"✅ Recipe '{name}' added successfully!")

def delete_recipe():
    view_recipes()
    if not recipe_list:
        return
    try:
        idx = int(input("Enter the number of the recipe to delete: "))
        if 1 <= idx <= len(recipe_list):
            recipe = recipe_list.pop(idx - 1)
            save_recipes()
            print(f"🗑️ Recipe '{recipe['name']}' deleted successfully.")
        else:
            print("❌ Invalid number.")
    except ValueError:
        print("❌ Input must be a number.")

def edit_recipe():
    view_recipes()
    if not recipe_list:
        return
    try:
        idx = int(input("Enter the number of the recipe to edit: "))
        if 1 <= idx <= len(recipe_list):
            recipe = recipe_list[idx - 1]
            print(f"🔧 Editing Recipe: {recipe['name']}")
            new_name = input("New name (leave blank to keep unchanged): ").strip()
            new_ingredients = input("New ingredients (comma separated, leave blank to keep unchanged): ").strip()

            if new_name:
                recipe["name"] = new_name
            if new_ingredients:
                recipe["ingredients"] = [i.strip() for i in new_ingredients.split(",") if i.strip()]

            save_recipes()
            print("✅ Recipe updated successfully.")
        else:
            print("❌ Invalid number.")
    except ValueError:
        print("❌ Input must be a number.")

def search_recipe():
    keyword = input("Enter search keyword: ").lower()
    results = [r for r in recipe_list if keyword in r['name'].lower()]
    if not results:
        print("🔍 No matching recipes found.")
        return
    print("\n🎯 Search Results:")
    for i, r in enumerate(results, start=1):
        print(f"{i}. {r['name']} | Ingredients: {', '.join(r['ingredients'])}")

# ======================= MENU ====================
def recipe_menu():
    load_recipes()
    while True:
        print("\n📋 Recipe Menu")
        print("1. View Recipes")
        print("2. Add Recipe")
        print("3. Edit Recipe")
        print("4. Search Recipe")
        print("5. Exit")
        print("0. Back to Main Menu")

        choice = input("Choose an option: ")
        if choice == "1":
            view_recipes()
        elif choice == "2":
            add_recipe()
        elif choice == "3":
            delete_recipe()
        elif choice == "4":
            edit_recipe()
        elif choice == "5":
            search_recipe()
        elif choice == "0":
            break
        else:
            print("❌ Invalid choice.")
