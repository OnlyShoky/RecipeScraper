from utils.scraper import scrape_recipe
import json
import requests
from tqdm import tqdm  # Import tqdm for the progress bar

# Open and read the JSON file
with open('dataScraped/sitemapURLS.json', 'r') as file:
    data = json.load(file)

# Get the URLs to process
sites_to_process = data['post-sitemap'][1:3]
sites_parsed = 0
recipe_data = None

# Use tqdm to show the progress bar
print("Processing sites:")
with tqdm(sites_to_process, desc="Progress", unit="site") as progress_bar:
    for site in progress_bar:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            }
            response = requests.get(site, headers=headers)
            response.raise_for_status()
            
             # Update the progress bar to show the current URL
            progress_bar.set_postfix({"url": response.url[:50]})  # Truncate URL for readability

            if response.url != 'https://preppykitchen.com':
                sites_parsed += 1
                recipe_data = scrape_recipe(site,recipe_data)


        except requests.exceptions.RequestException as e:
            print(f"\nError fetching {site}: {e}")

print(f"\nFinished processing {len(sites_to_process)} sites.")
print(f"Successfully parsed {sites_parsed} sites.")


# Save to JSON file
if recipe_data:
    with open('dataScraped/recipe.json', 'w', encoding='utf-8') as f:
        json.dump(recipe_data, f, indent=4, ensure_ascii=False)
    print("Recipe data saved to recipe.json")
else:
    print("Failed to scrape recipe data")