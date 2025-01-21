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
        '¼': '0.25',  # Quarter
        '½': '0.5',   # Half
        '¾': '0.75',  # Three-quarters
        '⅓': '0.333', # One-third
        '⅔': '0.666', # Two-thirds
        '⅕': '0.2',   # One-fifth
        '⅖': '0.4',   # Two-fifths
        '⅗': '0.6',   # Three-fifths
        '⅘': '0.8',   # Four-fifths
        '⅙': '0.166', # One-sixth
        '⅚': '0.833', # Five-sixths
        '⅛': '0.125', # One-eighth
        '⅜': '0.375', # Three-eighths
        '⅝': '0.625', # Five-eighths
        '⅞': '0.875', # Seven-eighths
        '⅐': '0.142', # One-seventh
        '⅑': '0.111', # One-ninth
        '⅒': '0.1',   # One-tenth
    }

    # Check if the quantity text is in the mapping
    firstNumber = '0'
    if quantity_text[0] not in fraction_map:
        firstNumber = quantity_text[0]
    for number in quantity_text:
        if number in fraction_map:
            quantity_text =  firstNumber + fraction_map[number]
    
    #Treat examples like 1-2
    division = 1
    if '-' in quantity_text or 'to' in quantity_text :
        quantity_text = quantity_text.replace('-',' ')
        quantity_text = quantity_text.replace('to',' ')
        division = 2
    
    #Treat fractions 
    quantity_list = quantity_text.split()
    #We need to treat examples like '1 1/2'
    if(len(quantity_list) > 1):
        sum = 0
        for quantity in quantity_list:
            sum += Fraction(quantity)
        sum = sum/division
        quantity_text = str(sum)  
 
    return float(Fraction(quantity_text))

# Function to download the image and save it locally
import re
import os
import requests

import re
import os
import requests

def save_image(image, save_path='/recipe_images/card/'):
    """
    Save an image to the specified path.
    
    Parameters:
        image: BeautifulSoup tag containing the image
        save_path: Path to save the image
    
    Returns:
        Path to the saved image or None if the process fails
    """
    # Extract image URL
    try:
        image_url = image.find('img')['src']
    except (KeyError, TypeError) as e:
        print(f"\nError extracting image URL: {e}")
        return None
    
    # Handle 'data-lazy-src' as a fallback
    if not image_url or not any(ext in image_url for ext in ['.jpg', '.jpeg', '.png']):
        try:
            image_url = image.find('img')['data-lazy-src']
        except KeyError as e:
            print(f"\nError fetching lazy image URL: {e}")
            return None

    try:
        # Set headers for the request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(image_url, headers=headers, stream=True)
        response.raise_for_status()

        # Match valid image extensions (.jpg, .jpeg, .png, etc.)
        match = re.search(r'([^/]+\.(jpg|jpeg|png))$', image_url, re.IGNORECASE)

        if match:
            image_name = match.group(1)  # Extract the image name with extension
        else:
            print("No valid image URL found.")
            return None

        if image_name:
            save_path = 'media' + os.path.join(save_path, image_name)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save the image
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        
        return save_path.removeprefix('media')  # Return relative path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None



def extract_time(time):
    """Convert time string to HH:MM:SS format"""
    if not time:
        return None
    
    time_string = ' '.join([x.text for x in time])
    
    hours = re.search(r'(\d+)\s*hours?', time_string, re.IGNORECASE)
    minutes = re.search(r'(\d+)\s*minutes?', time_string)
    seconds = re.search(r'(\d+)\s*seconds?', time_string)
    
    hours = int(hours.group(1)) if hours else 0
    minutes = int(minutes.group(1)) if minutes else 0
    seconds = int(seconds.group(1)) if seconds else 0
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


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
                if amount:
                    quantity_text = amount.text.strip()
                    try:
                        # Convert the fraction to a float if it's a valid fraction
                        quantity = convert_fraction_text(quantity_text)
                        

                    except ValueError:
                        # If it's not a valid fraction (or not a number), keep it as None
                        print(f"it's not a valid fraction (or not a number), keep it as None")
                        quantity = None
                else:
                    quantity = None

                ingredient_dict = {
                    "ingredient": {
                        "name": name.text.strip() if name else None,
                        "nutrition": None
                    },
                    "quantity": quantity,
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

def extract_equipment(soup):
    """Extract cooking equipment"""
    equipment_container = soup.find('div', class_='wprm-recipe-equipment-container')
    equipment = []
    if equipment_container :
        equipment_items = equipment_container.find_all('div', class_='wprm-recipe-equipment-name')
        
        for item in equipment_items:
            item.text.replace('▢','')
            equipment.append(item.text.strip())
    
    return "\n".join(equipment)


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
 
def extract_notes(soup):
    """Extract cooking notes"""
    notes_container = soup.find('div', class_='wprm-recipe-notes-container')
    notes = []
    if notes_container :
        notes_items = notes_container.find_all('li')
        for item in notes_items:
            notes.append(item.text.strip())
    
    return "\n".join(notes)

def extract_tags(soup):
    tags_list = []
    tags_container = soup.find_all('meta', property='slick:category')
    if tags_container:
        for category in tags_container:
            tag = category['content'].split(':')[0]
            tags_list.append(tag)

    return tags_list

def extract_cuisines(soup):
    cuisine_list = []
    cuisine_container = soup.find('span', class_='wprm-recipe-cuisine').text.strip().split(',')
    if cuisine_container:
        for cuisine in cuisine_container:
            cuisine = cuisine.replace(' ', '').capitalize()
            cuisine_list.append(cuisine)

    return cuisine_list

def extract_courses(soup):
    course_list = []
    course_container = soup.find('span', class_='wprm-recipe-course').text.strip().split(',')
    if course_container:
        for course in course_container:
            course = course.replace(' ', '').capitalize()
            course_list.append(course)

    return course_list

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
                        "image" : save_image(soup.find('div', class_='featured-image-class'), save_path='/recipe_images/featured/') ,
                        "courses": extract_courses(soup),
                        "cuisines": extract_cuisines(soup),
                        'tags': extract_tags(soup),
                        "prep_time": extract_time(soup.findAll('span', class_='wprm-recipe-prep_time')),
                        "cook_time": extract_time(soup.findAll('span', class_='wprm-recipe-cook_time')),
                        "cool_time": extract_time(soup.findAll('span', class_='wprm-recipe-custom_time')),
                        "total_time": extract_time(soup.findAll('span', class_='wprm-recipe-total_time')),
                        "created": None,
                        "modified": None,
                        "description": soup.find('div', class_='wprm-recipe-summary').text.strip() if soup.find('div', class_='wprm-recipe-summary') else None,
                        "status": 1,
                        "activate_date": None,
                        "deactivate_date": None,
                        "servings": int(soup.find('span', class_='wprm-recipe-servings').text) if soup.find('span', class_='wprm-recipe-servings') else None,
                        "equipment" : extract_equipment(soup),
                        "ingredients": extract_ingredients(soup),
                        "instructions": extract_instructions(soup),
                        "author": soup.find('span', class_='wprm-recipe-author').text.strip() if soup.find('span', class_='wprm-recipe-author') else None,
                        "source": "Preppy Kitchen",
                        "notes" : extract_notes(soup),
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