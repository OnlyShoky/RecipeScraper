

import requests
import xml.etree.ElementTree as ET

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

def parse_sitemap(sitemap_xml):
    """ Parse the XML sitemap to extract URLs """
    urls = []
    try:
        root = ET.fromstring(sitemap_xml)
        for url in root.findall('.//url/loc'):
            urls.append(url.text)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    return urls

def save_urls(urls, filename):
    """ Save the URLs to a file """
    with open(filename, 'w') as f:
        for url in urls:
            f.write(url + '\n')

def main():
    sitemap_url = "https://preppykitchen.com/post-sitemap.xml"
    print("Fetching sitemap index...")

    sitemap_xml = fetch_sitemap(sitemap_url)
    if sitemap_xml:
        # Parse the sitemap index to get individual sitemap URLs
        print("Parsing sitemap index...")
        sitemaps = parse_sitemap(sitemap_xml)

        all_urls = []
        for sitemap_url in sitemaps:
            print(f"Fetching {sitemap_url}...")
            sitemap_xml = fetch_sitemap(sitemap_url)
            if sitemap_xml:
                print(f"Parsing {sitemap_url}...")
                recipe_urls = parse_sitemap(sitemap_xml)
                all_urls.extend(recipe_urls)

        # Save all URLs to a file
        print(f"Saving {len(all_urls)} URLs to 'recipes.txt'...")
        save_urls(all_urls, 'recipes.txt')
        print("Done!")

if __name__ == '__main__':
    main()

