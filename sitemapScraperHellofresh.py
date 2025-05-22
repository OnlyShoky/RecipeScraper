import json
import requests
import xml.etree.ElementTree as ET

def save_urls_to_json(urls, filename):
    """Save the categorized URLs to a JSON file."""
    with open(filename, 'w') as file:
        json.dump(urls, file, indent=4)

def parse_sitemap_index(sitemap_xml):
    """ Parse the XML sitemap index to extract URLs of individual sitemaps """
    urls = []
    try:
        # Parse the sitemap index XML
        root = ET.fromstring(sitemap_xml)
        
        # Define the namespace to search for elements with the correct namespace
        namespace = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Find all <loc> elements under <sitemap> tags
        for sitemap in root.findall('.//sitemap:sitemap/sitemap:loc', namespace):
            urls.append(sitemap.text)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    
    return urls

def parse_sitemap(sitemap_xml):
    """ Parse the XML sitemap to extract all URLs """
    urls = []
    try:
        root = ET.fromstring(sitemap_xml)
        
        # Define the namespace for handling the default namespace
        namespaces = {
            '': 'http://www.sitemaps.org/schemas/sitemap/0.9'  # Default namespace
        }

        # Find all <url> elements in the sitemap
        for url in root.findall('.//url', namespaces):
            loc = url.find('loc', namespaces)
            if loc is not None:
                # Extract the URL from the <loc> tag
                urls.append(loc.text)

    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    
    return urls

def fetch_sitemap(url):
    """ Fetch the sitemap content from a URL """
    try:
        # Send a GET request to the base page
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Fetch the sitemap index
sitemap_url = "https://preppykitchen.com/sitemap_index.xml"
sitemap_xml = fetch_sitemap(sitemap_url)

if sitemap_xml:
    # Parse the sitemap index to get individual sitemap URLs
    print("Parsing sitemap index...")
    sitemaps = parse_sitemap_index(sitemap_xml)

    categorized_urls = {
        "post-sitemap": [],
        "page-sitemap": [],
        "category-sitemap": []
    }

    for sitemap_url in sitemaps[1:5]:
        print(f"Fetching {sitemap_url}...")
        sitemap_xml = fetch_sitemap(sitemap_url)
        if sitemap_xml:
            print(f"Parsing {sitemap_url}...")
            if "post" in sitemap_url:
                categorized_urls["post-sitemap"].extend(parse_sitemap(sitemap_xml))
            elif "page" in sitemap_url:
                categorized_urls["page-sitemap"].extend(parse_sitemap(sitemap_xml))
            elif "category" in sitemap_url:
                categorized_urls["category-sitemap"].extend(parse_sitemap(sitemap_xml))

    # Save all categorized URLs to a JSON file
    print(f"Saving categorized URLs to 'recipes.json'...")
    save_urls_to_json(categorized_urls, 'dataScraped/sitemapURLS2.json')
    print("Done!")
