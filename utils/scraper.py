import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os
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
    
    
    #Treat fractions 
    quantity_list = quantity_text.split()
    #We need to treat examples like '1 1/2'
    if(len(quantity_list) > 1):
        sum = 0
        for quantity in quantity_list:
            sum += Fraction(quantity)
        quantity_text = str(sum)  
         
    
        
    return Fraction(quantity_text)

# Function to download the image and save it locally
def save_image(image,save_path = 'media/card/'):
    
    # Extract image URL
    image_url = image.find('img')['src']
    
    if 'jpg' not in image_url:
        try:
            image_url = image.find('img')['data-lazy-src']
        except KeyError as e :
            print(f"\nError fetching {image_url}: {e}")


    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(image_url, headers=headers,stream=True)
        response.raise_for_status()
        
        
        match = re.search(r'([^/]+\.jpg)$', image_url)
        
        if match:
            jpg_name = match.group(1)
        else:
            print("No match found")

        if jpg_name:
            save_path = os.path.join(save_path, jpg_name)
        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        


        
        # Save the image
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return save_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None

def extract_time(time):
    """Convert time string to HH:MM:SS format"""
    if not time:
        return None
    time_string = time.text
    minutes = int(re.search(r'\d+', time_string).group())
    return f"{minutes//60:02d}:{minutes%60:02d}:00"


def extract_ingredients(soup):
    """Extract ingredients information with fractional quantities"""
    ingredients_list = []
    ingredients_container = soup.find('div', class_='wprm-recipe-ingredients-container')

    if ingredients_container:
        # ingredient_items = ingredients_container.find_all('li', class_='wprm-recipe-ingredient')
        groups_ingredients = ingredients_container.find_all('div', class_='wprm-recipe-ingredient-group')

        for group in groups_ingredients:
            groupname = group.find('h4', class_='wprm-recipe-group-name')
            ingredient_items = group.find_all('li', class_='wprm-recipe-ingredient')
            for item in ingredient_items:
                amount = item.find('span', class_='wprm-recipe-ingredient-amount')
                unit = item.find('span', class_='wprm-recipe-ingredient-unit')
                name = item.find('span', class_='wprm-recipe-ingredient-name')
                notes = item.find('span', class_='wprm-recipe-ingredient-notes')

                # # Handle fractional quantities (like ½, ¼)
                # if amount:
                #     quantity_text = amount.text.strip()
                #     try:
                #         # Convert the fraction to a float if it's a valid fraction
                #         quantity_text = convert_fraction_text(quantity_text)
                #         quantity = float(Fraction(quantity_text))

                #     except ValueError:
                #         # If it's not a valid fraction (or not a number), keep it as None
                #         print(f"it's not a valid fraction (or not a number), keep it as None")
                #         quantity = None
                # else:
                #     quantity = None

                ingredient_dict = {
                    "ingredient": {
                        "name": name.text.strip() if name else None,
                        "nutrition": None
                    },
                    "quantity": amount.text if amount else None,
                    "unit": unit.text.strip() if unit else "whole",
                    "groupName" : groupname.text if groupname else None,
                    "notes": notes.text.strip() if notes else None
                }
                ingredients_list.append(ingredient_dict)

    return ingredients_list


def extract_instructions(soup):
    """Extract cooking instructions"""
    instructions_container = soup.find('div', class_='wprm-recipe-instructions-container')
    instructions = []
    
    groups_instructions = instructions_container.find_all('div', class_='wprm-recipe-instruction-group')

    for group in groups_instructions:
        groupname = group.find('h4', class_='wprm-recipe-group-name')
        instructions_group = group.find_all('ul', class_='wprm-recipe-instructions')
        
        if groupname :
            instructions.append(f"GroupName : {groupname.text}")
            for instruction in instructions_group:
                instruction_items = instruction.find_all('li', class_='wprm-recipe-instruction')
                # instructions = [f"{i+1}. {item.text.strip()}" for i, item in enumerate(instruction_items)]
                instructions.extend([f"{i+1}. {item.text.strip()}" for i, item in enumerate(instruction_items)])
        else :
            if instructions_container:
                instruction_items = instructions_container.find_all('li', class_='wprm-recipe-instruction')
                instructions = [f"{i+1}. {item.text.strip()}" for i, item in enumerate(instruction_items)]
    
    return "\n".join(instructions)


def extract_nutrition(soup):
    """Find all nutrition containers"""
    
    nutrition_elements = soup.select('.wprm-nutrition-label-text-nutrition-container')


    if not nutrition_elements :
        return None
    # Initialize an empty dictionary to store the nutrition data
    nutrition_dict = {}

    # Loop through each element and extract the nutrition details
    for element in nutrition_elements:
        # Extract the label (e.g., Calories, Carbohydrates)
        label = element.select_one('.wprm-nutrition-label-text-nutrition-label').text.strip(': ')
        
        # Extract the value (e.g., 443, 76)
        value = element.select_one('.wprm-nutrition-label-text-nutrition-value').text
        
        # Extract the unit (e.g., kcal, g, mg)
        unit = element.select_one('.wprm-nutrition-label-text-nutrition-unit').text
        
        # Store the data in the dictionary
        nutrition_dict[label] = f"{value} {unit}"
        
    return nutrition_dict    
    

def scrape_recipe(url,dataScraped = None):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        

        
        #Data scrap for 1 element
        if(not dataScraped):
            recipe_data = {"recipes": []}
        else:
            recipe_data = dataScraped
        
        data = {"data": {
                    "type": "RecipeDetailAPIView",
                    "id": -1,
                    "attributes": {
                        "title": soup.find('h2', class_='wprm-recipe-name').text.strip(),
                        "difficulty": None,
                        "image_card": save_image(soup.find('div', class_='wprm-recipe-image')) ,
                        "image" : save_image(soup.find('div', class_='featured-image-class'), save_path='media/featured/') ,
                        "course": {
                            "id": -1,
                            "name": soup.find('span', class_='wprm-recipe-course').text.strip() if soup.find('span', class_='wprm-recipe-course') else None,
                            "type": "Course"
                        },
                        "cuisine": {
                            "id": -1,
                            "name": soup.find('span', class_='wprm-recipe-cuisine').text.strip() if soup.find('span', class_='wprm-recipe-cuisine') else None,
                            "type": "Cuisine"
                        },
                        "prep_time": extract_time(soup.find('span', class_='wprm-recipe-prep_time')),
                        "cook_time": extract_time(soup.find('span', class_='wprm-recipe-cook_time')),
                        "cool_time": extract_time(soup.find('span', class_='wprm-recipe-custom_time')),
                        "total_time": extract_time(soup.find('span', class_='wprm-recipe-total_time')),
                        "created": None,
                        "modified": None,
                        "description": soup.find('div', class_='wprm-recipe-summary').text.strip() if soup.find('div', class_='wprm-recipe-summary') else None,
                        "status": 1,
                        "activate_date": None,
                        "deactivate_date": None,
                        
                        "servings": int(soup.find('span', class_='wprm-recipe-servings').text) if soup.find('span', class_='wprm-recipe-servings') else None,
                        "ingredients": extract_ingredients(soup),
                        "instructions": extract_instructions(soup),
                        "author": soup.find('span', class_='wprm-recipe-author').text.strip() if soup.find('span', class_='wprm-recipe-author') else None,
                        "source": "Preppy Kitchen",
                        "rating": {
                            "average": soup.find('div', id='wprm-recipe-user-rating-0')['data-average'],
                            "count": soup.find('div', id='wprm-recipe-user-rating-0')['data-count']
                        },
                        "video_url": soup.find('div', class_='rll-youtube-player')['data-src'] if soup.find('div', class_='rll-youtube-player') else None,
                        "Nutrition" : extract_nutrition(soup)
                    }
                }
            }
        
        recipe_data['recipes'].append(data)
        
        return recipe_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None