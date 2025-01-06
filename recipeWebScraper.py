import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

from fractions import Fraction

def convert_fraction_text(quantity_text):
    # Define a mapping from fraction symbols to numeric string equivalents
    fraction_map = {
        '¼': '.25',
        '½': '.5',
        '¾': '.75',
        '⅓': '.33',
        '⅔': '.66',
        '⅕': '.2',
        '⅖': '.4',
        '⅗': '.6',
        '⅘': '.8'
    }

    # Check if the quantity text is in the mapping
    firstNumber = '0'
    if quantity_text[0] not in fraction_map:
        firstNumber = quantity_text[0]
    for number in quantity_text:
        if number in fraction_map:
            quantity_text =  firstNumber + fraction_map[number]
    

    return Fraction(quantity_text)

def extract_time(time_string):
    """Convert time string to HH:MM:SS format"""
    if not time_string:
        return None
    minutes = int(re.search(r'\d+', time_string).group())
    return f"{minutes//60:02d}:{minutes%60:02d}:00"

from fractions import Fraction

def extract_ingredients(soup):
    """Extract ingredients information with fractional quantities"""
    ingredients_list = []
    ingredients_container = soup.find('div', class_='wprm-recipe-ingredients-container')

    if ingredients_container:
        ingredient_items = ingredients_container.find_all('li', class_='wprm-recipe-ingredient')

        for item in ingredient_items:
            amount = item.find('span', class_='wprm-recipe-ingredient-amount')
            unit = item.find('span', class_='wprm-recipe-ingredient-unit')
            name = item.find('span', class_='wprm-recipe-ingredient-name')
            notes = item.find('span', class_='wprm-recipe-ingredient-notes')

            # Handle fractional quantities (like ½, ¼)
            if amount:
                quantity_text = amount.text.strip()
                try:
                    # Convert the fraction to a float if it's a valid fraction
                    quantity_text = convert_fraction_text(quantity_text)
                    quantity = float(Fraction(quantity_text))

                except ValueError:
                    # If it's not a valid fraction (or not a number), keep it as None
                    print(f"it's not a valid fraction (or not a number), keep it as None")
                    quantity = None
            else:
                quantity = None

            ingredient_dict = {
                "ingredient": {
                    "name": name.text.strip() if name else None,
                    "nutrition": notes.text.strip() if notes else None
                },
                "quantity": quantity,
                "unit": unit.text.strip() if unit else "whole"
            }
            ingredients_list.append(ingredient_dict)

    return ingredients_list


def extract_instructions(soup):
    """Extract cooking instructions"""
    instructions_container = soup.find('div', class_='wprm-recipe-instructions-container')
    instructions = []
    
    if instructions_container:
        instruction_items = instructions_container.find_all('li', class_='wprm-recipe-instruction')
        instructions = [f"{i+1}. {item.text.strip()}" for i, item in enumerate(instruction_items)]
    
    return "\n".join(instructions)

def scrape_recipe(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract recipe details
        recipe_data = {
            "recipes": [{
                "data": {
                    "type": "RecipeDetailAPIView",
                    "id": -1,
                    "attributes": {
                        "ingredients": extract_ingredients(soup),
                        "course": {
                            "id": 1,
                            "name": soup.find('span', class_='wprm-recipe-course').text.strip(),
                            "type": "Course"
                        },
                        "cuisine": {
                            "id": 1,
                            "name": soup.find('span', class_='wprm-recipe-cuisine').text.strip(),
                            "type": "Cuisine"
                        },
                        "prep_time": extract_time(soup.find('span', class_='wprm-recipe-prep_time').text),
                        "cook_time": extract_time(soup.find('span', class_='wprm-recipe-cook_time').text),
                        "cool_time": None,
                        "total_time": extract_time(soup.find('span', class_='wprm-recipe-total_time').text),
                        "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "title": soup.find('h2', class_='wprm-recipe-name').text.strip(),
                        "description": soup.find('div', class_='wprm-recipe-summary').text.strip(),
                        "status": 1,
                        "activate_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "deactivate_date": None,
                        "image": soup.find('div', class_='wprm-recipe-image').find('img')['src'],
                        "servings": int(soup.find('span', class_='wprm-recipe-servings').text),
                        "difficulty": "Easy",
                        "instructions": extract_instructions(soup),
                        "author": soup.find('span', class_='wprm-recipe-author').text.strip(),
                        "source": "Preppy Kitchen",
                        "video_url": None
                    }
                }
            }]
        }
        
        return recipe_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Use the scraper
url = 'https://preppykitchen.com/wprm_print/banana-waffles-recipe'
recipe_data = scrape_recipe(url)

# Save to JSON file
if recipe_data:
    with open('recipe.json', 'w', encoding='utf-8') as f:
        json.dump(recipe_data, f, indent=4, ensure_ascii=False)
    print("Recipe data saved to recipe.json")
else:
    print("Failed to scrape recipe data")