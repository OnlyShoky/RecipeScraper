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

def save_image(image, save_path='/recipe_imagesHF/card/'):
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
    """Extract ingredients information from HelloFresh-style HTML"""
    ingredients_list = []
    
    ingredients_container = soup.find('div', attrs={'data-test-id': 'ingredients-list'})
    
    if ingredients_container:
        ingredient_items = ingredients_container.find_all('div', attrs={'data-test-id': 'ingredient-item-shipped'})
        
        for item in ingredient_items:
            text_blocks = item.find_all('p')
            
            # Get quantity and unit
            quantity_unit = text_blocks[0].text.strip() if len(text_blocks) > 0 else None
            quantity = None
            unit = None
            
            if quantity_unit:
                # Split quantity and unit using the first space
                parts = quantity_unit.split(' ', 1)
                if len(parts) == 2:
                    try:
                        quantity = convert_fraction_text(parts[0].strip())
                        unit = parts[1].strip()
                    except ValueError:
                        quantity = None
                        unit = quantity_unit  # fallback to full string if parsing fails
                else:
                    try:
                        quantity = convert_fraction_text(parts[0].strip())
                        unit = "whole"
                    except ValueError:
                        quantity = None
                        unit = "whole"

            # Get ingredient name
            name = text_blocks[1].text.strip() if len(text_blocks) > 1 else None

            # Get notes like allergens (optional)
            notes = text_blocks[2].text.strip() if len(text_blocks) > 2 else None

            ingredient_dict = {
                "ingredient": {
                    "name": name,
                    "nutrition": None
                },
                "quantity": quantity,
                "unit": unit,
                "groupName": None,  # No group names in this layout
                "notes": notes
            }
            ingredients_list.append(ingredient_dict)

    return ingredients_list



import re

def extract_instructions(soup):
    """Extract cooking instructions as a single string and notes separately"""
    instructions = []
    notes = []

    # Locate all steps
    instruction_steps = soup.find_all('div', attrs={'data-test-id': 'instruction-step'})

    for step in instruction_steps:
        # Extract step number
        number_tag = step.find('span', class_='fhZPKU')
        step_number = number_tag.text.strip() if number_tag else '?'

        # Extract step description
        description_tag = step.find('p')
        step_text = description_tag.get_text(separator=' ', strip=True) if description_tag else 'No instruction text found.'
        step_text = step_text.replace('\n', ' ')

        # Detect and extract TIPS (e.g., "TIP: Do this." or "TIPS: Do that.")
        tips_found = re.findall(r'TIPS?:.*?[.•!)]', step_text)
        for tip in tips_found:
            step_text = step_text.replace(tip, '')
            tip = tip.replace('TIP:', '').replace('•', '')
            notes.append(tip.strip())
            step_text = step_text.replace(tip, '')

        # Add formatted instruction string
        if step_text:
            instructions.append(f"{step_number}. {step_text}")

    # Join all instructions with newline characters
    return "\n".join(instructions), "\n".join(notes)



def extract_equipment(soup):
    """Extract cooking equipment (utensils) from new structure"""
    equipment = []

    # Start from the section
    section = soup.find('div', {'data-section-id': 'utensilsSection'})
    if section:
        # Now get the list container
        list_container = section.find('div', {'data-test-id': 'utensils-list'})
        if list_container:
            items = list_container.find_all('div', {'data-test-id': 'utensils-list-item'})
            for item in items:
                # Each item has two spans: one for bullet (•), one for name
                spans = item.find_all('span')
                if len(spans) >= 2:
                    equipment_name = spans[1].get_text(strip=True)
                    equipment.append(equipment_name)

    return "\n".join(equipment)




def extract_nutrition(soup):
    """Extract nutrition information as a dictionary from the HTML soup."""

    # Encuentra todos los bloques de nutrición individuales
    nutrition_elements = soup.select('div[data-test-id="nutrition-step"]')

    if not nutrition_elements:
        return None

    nutrition_dict = {}

    for element in nutrition_elements:
        # Label: ej. Calories, Fat, etc.
        label_tag = element.select_one('.khSFcA')
        # Value y unidad están en el mismo span
        value_unit_tag = element.select_one('.gHvgPY')

        if label_tag and value_unit_tag:
            label = label_tag.text.strip(': ')
            
            # Extraer el valor numérico y la unidad con una expresión regular
            import re
            match = re.match(r'(\d+)\s*([a-zA-Z]+)', value_unit_tag.text.strip())
            if match:
                value = match.group(1)
                unit = match.group(2)
                nutrition_dict[label] = (value, unit)

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
        
        script_tag = soup.find('script', {'type': 'application/ld+json', 'id': 'schema-org'})
        
        # Step 3: Parse the JSON content
        if script_tag:
            data = json.loads(script_tag.string)
        else:
            print("No structured data found")
    
        #Data scrap for 1 element
        if(not dataScraped):
            recipe_data = {"recipes": []}
        else:
            recipe_data = dataScraped
            
        # Difficulty
        difficulty_label = soup.find('span', attrs={'data-translation-id': 'recipe-detail.difficulty'})
        if difficulty_label:
            difficulty = difficulty_label.find_parent().find_next_sibling('span', class_='sc-54d3413f-0 gHvgPY').get_text(strip=True)
        else:
            difficulty = None
            
        # Prep Time
        prep_time_label = soup.find('span', attrs={'data-translation-id': 'recipe-detail.cooking-time'})
        if prep_time_label:
            prep_time = extract_time(prep_time_label.find_parent().find_next_sibling('span', class_='sc-54d3413f-0 gHvgPY'))
        else:
            prep_time = None
        
        
        instructions, notes = extract_instructions(soup)
        data = {"data": {
                    "type": "RecipeDetailAPIView",
                    "id": -1,
                    "attributes": {
                        "title": soup.find('h1', class_='sc-54d3413f-0 hwFcHr').text.strip(),
                        "difficulty": difficulty,
                        "image_card": save_image(soup.find('div', class_='sc-54d3413f-0 gUmaWK'), save_path='/recipe_imagesHF/card/') ,
                        "image" : save_image(soup.find('div', class_='sc-54d3413f-0 gUmaWK'), save_path='/recipe_imagesHF/featured/') ,
                        "courses": [data.get("recipeCategory")],
                        "cuisines": [data.get("recipeCuisine")],
                        'tags': data.get("keywords"),
                        "prep_time": prep_time,
                        "cook_time": extract_time(soup.findAll('span', class_='wprm-recipe-cook_time')),
                        "cool_time": extract_time(soup.findAll('span', class_='wprm-recipe-custom_time')),
                        "total_time": extract_time(soup.findAll('span', class_='sc-54d3413f-0 gHvgPY')),
                        "created": None,
                        "modified": None,
                        "description": data.get("description"),
                        "status": 1,
                        "activate_date": None,
                        "deactivate_date": None,
                        "servings": data.get("recipeYield"),
                        "equipment" : extract_equipment(soup),
                        "ingredients": extract_ingredients(soup),
                        "instructions": instructions,
                        "author": data.get("author"),
                        "source": "Hello Fresh",
                        "notes" : notes if notes else None,
                        "rating": {
                            "average": None,
                            "count": None
                        },
                        "video_url": None,
                        "nutrition" : extract_nutrition(soup)
                    }
                }
            }
        


        
        recipe_data['recipes'].append(data)
        
        return recipe_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None