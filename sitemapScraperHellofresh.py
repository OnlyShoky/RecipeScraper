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
    """ Parse the XML sitemap and extract URLs, handling optional namespaces """
    urls = []
    try:
        root = ET.fromstring(sitemap_xml)

        # Detect default namespace (if any)
        if root.tag.startswith("{"):
            ns_uri = root.tag.split("}")[0].strip("{")
            ns = {'ns': ns_uri}
            url_tag = 'ns:url'
            loc_tag = 'ns:loc'
        else:
            ns = {}
            url_tag = 'url'
            loc_tag = 'loc'

        # Extract all <loc> elements from <url>
        for url_elem in root.findall(f'.//{url_tag}', ns):
            loc = url_elem.find(loc_tag, ns)
            if loc is not None and loc.text:
                urls.append(loc.text.strip())

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
# Fetch the sitemap index
sitemap_url = "https://www.hellofresh.com/sitemap_index.xml"

sitemap_xml = fetch_sitemap(sitemap_url)


if sitemap_xml:
    # Parse the sitemap index to get individual sitemap URLs
    print("Parsing sitemap index...")
    sitemaps = parse_sitemap_index(sitemap_xml)

    categorized_urls = {
        "sitemap_transactional_pages": [],
        "sitemap_recipe_collections": [],
        "sitemap_recipe_pages": [],
        "sitemap_others" : []
    }

    for sitemap_url in sitemaps:
        print(f"Fetching {sitemap_url}...")
        sitemap_xml = fetch_sitemap(sitemap_url)
        if sitemap_xml:
            print(f"Parsing {sitemap_url}...")
            if "sitemap_transactional_pages" in sitemap_url:
                categorized_urls["sitemap_transactional_pages"].extend(parse_sitemap(sitemap_xml))
            elif "sitemap_recipe_collections" in sitemap_url:
                categorized_urls["sitemap_recipe_collections"].extend(parse_sitemap(sitemap_xml))
            elif "sitemap_recipe_pages" in sitemap_url:
                categorized_urls["sitemap_recipe_pages"].extend(parse_sitemap(sitemap_xml))
            elif "others" in sitemap_url:
                categorized_urls["sitemap_others"].extend(parse_sitemap(sitemap_xml))

    # Save all categorized URLs to a JSON file
    print(f"Saving categorized URLs to 'dataScraped/helloFresh/sitemapURLSHelloFresh.json'...")
    save_urls_to_json(categorized_urls, 'dataScraped/helloFresh/sitemapURLSHelloFresh.json')
    print("Done!")
