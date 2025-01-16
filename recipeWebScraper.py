from utils.scraper import scrape_recipe
import json
import requests
from tqdm import tqdm  # Import tqdm for the progress bar

# Open and read the JSON file
with open('dataScraped/sitemapURLS.json', 'r') as file:
    data = json.load(file)

# Get the URLs to process
sites_to_process = data['post-sitemap'][1:]
sites_parsed = 0
sites_notParsed = 0
list_sitesNotParsed = []
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
                try:
                    recipe_data = scrape_recipe(site,recipe_data)
                    sites_parsed += 1
                except Exception as e:
                    print(f"\nError fetching {site}: {e}")
                    sites_notParsed += 1
                    list_sitesNotParsed.append(site)


        except requests.exceptions.RequestException as e:
            print(f"\nError fetching {site}: {e}")
            sites_notParsed += 1
            list_sitesNotParsed.append(site)

print(f"\nFinished processing {len(sites_to_process)} sites.")
print(f"Successfully parsed {sites_parsed} sites.")
print(f"Not successfully parsed {list_sitesNotParsed} sites.")


# Save to JSON file
if recipe_data:
    with open('dataScraped/recipe.json', 'w', encoding='utf-8') as f:
        json.dump(recipe_data, f, indent=4, ensure_ascii=False)
    print("Recipe data saved to recipe.json")
else:
    print("Failed to scrape recipe data")
    
# Save sites not parsed to a text file
with open('dataScraped/sites_not_parsed.txt', 'w') as f:
    for site in list_sitesNotParsed:
        f.write(f"{site}\n")
    print("Sites not parsed saved to sites_not_parsed.txt")
