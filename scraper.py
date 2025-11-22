import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin
import sys

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://bestoftelegram.com"

def get_soup(url):
    """Fetch and parse HTML from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        time.sleep(1)  # Be respectful to the server
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}", flush=True)
        return None

def get_categories():
    """Scrape all categories from the main channels page"""
    print("Fetching categories...")
    soup = get_soup(f"{BASE_URL}/channels/")

    if not soup:
        return []

    categories = []
    category_grids = soup.find_all('div', class_='cgrid')

    for grid in category_grids:
        try:
            # Get category name and URL
            link = grid.find('a', href=True)
            if link:
                category_name = link.find('h2').text.strip()
                category_url = link['href']

                categories.append({
                    'name': category_name,
                    'url': category_url
                })
        except Exception as e:
            print(f"Error parsing category: {e}")
            continue

    print(f"Found {len(categories)} categories")
    return categories

def get_channels_from_category(category_url):
    """Scrape all channels from a category page"""
    # Ensure category URL includes /channels/ prefix
    if not category_url.startswith('/channels/'):
        category_url = f'/channels/{category_url}'
    full_url = urljoin(BASE_URL, category_url)
    print(f"Fetching channels from {full_url}...")

    soup = get_soup(full_url)
    if not soup:
        return []

    channels = []
    channel_areas = soup.find_all('div', class_='channel-area')

    for area in channel_areas:
        try:
            # Get channel name
            name_elem = area.find('h2', class_='font-style1')
            channel_name = name_elem.text.strip() if name_elem else ""

            # Get channel username
            username_elem = area.find('p', class_='color-gray')
            username = ""
            if username_elem and username_elem.find('i'):
                username = username_elem.find('i').text.strip()

            # Get member count
            members_elem = area.find('p', class_='fz-15')
            members = ""
            if members_elem:
                members_text = members_elem.text.strip()
                members = re.search(r'(\d+)', members_text.replace(' ', ''))
                members = members.group(1) if members else ""

            # Get description
            desc_elem = area.find('div', class_='channel-desc')
            description = ""
            if desc_elem and desc_elem.find('p'):
                description = desc_elem.find('p').text.strip()

            # Get channel URL
            view_link = area.find('a', class_='telegram-btn')
            channel_url = ""
            if view_link and view_link.get('href'):
                channel_url = view_link['href']

            if channel_url:
                channels.append({
                    'name': channel_name,
                    'username': username,
                    'members': members,
                    'description': description,
                    'url': channel_url
                })
        except Exception as e:
            print(f"Error parsing channel: {e}")
            continue

    print(f"Found {len(channels)} channels")
    return channels

def get_channel_details(channel_url):
    """Scrape detailed information from a channel page"""
    full_url = urljoin(BASE_URL, channel_url)
    print(f"Fetching details from {full_url}...")

    soup = get_soup(full_url)
    if not soup:
        return {}

    details = {}

    try:
        # Get channel details section
        details_section = soup.find('div', class_='reuse-grid', style=lambda x: x and 'padding-top:15px' in x)

        if details_section:
            text = details_section.get_text()

            # Extract Channel ID
            channel_id_match = re.search(r'Channel ID\s*:\s*(@\S+)', text)
            details['channel_id'] = channel_id_match.group(1) if channel_id_match else ""

            # Extract Category
            category_link = details_section.find('a', href=lambda x: x and '/channels/' in x)
            details['category'] = category_link.text.strip() if category_link else ""

            # Extract Language
            language_match = re.search(r'Language\s*:\s*(\w+)', text)
            details['language'] = language_match.group(1) if language_match else ""

            # Extract Members
            members_match = re.search(r'Members\s*:\s*([\d,]+)', text)
            details['members_count'] = members_match.group(1).replace(',', '') if members_match else ""

            # Extract Date Added
            date_match = re.search(r'Date Added\s*:\s*([\w\s,]+)', text)
            details['date_added'] = date_match.group(1).strip() if date_match else ""

        # Extract tags
        tags = []
        tag_links = soup.find_all('a', href=lambda x: x and '/tag/' in x)
        for tag_link in tag_links:
            tags.append(tag_link.text.strip())
        details['tags'] = ', '.join(tags)

        # Extract full description
        desc_sections = soup.find_all('div', class_='reuse-grid')
        for section in desc_sections:
            h2 = section.find('h2')
            if h2 and 'Channel Description' in h2.text:
                desc_p = section.find('p')
                if desc_p:
                    details['full_description'] = desc_p.text.strip()
                break

        # Extract rating
        rating_div = soup.find('div', class_='rating_widget')
        if rating_div:
            rating_text = rating_div.get_text()
            rating_match = re.search(r'Rated\s+(\S+)\s+out of\s+(\d+)', rating_text)
            if rating_match:
                details['rating'] = rating_match.group(1)
                details['total_reviews'] = rating_match.group(2)

    except Exception as e:
        print(f"Error parsing channel details: {e}")

    return details

def scrape_all_channels():
    """Main function to scrape all channels from all categories"""
    all_data = []

    # Get all categories
    categories = get_categories()

    for i, category in enumerate(categories, 1):
        print(f"\n[{i}/{len(categories)}] Processing category: {category['name']}")

        # Get all channels in this category
        channels = get_channels_from_category(category['url'])

        for j, channel in enumerate(channels, 1):
            print(f"  [{j}/{len(channels)}] Processing channel: {channel['name']}")

            # Get detailed information
            details = get_channel_details(channel['url'])

            # Combine all data
            channel_data = {
                'category': category['name'],
                'channel_name': channel['name'],
                'username': channel['username'],
                'members': channel['members'],
                'description': channel['description'],
                'channel_url': urljoin(BASE_URL, channel['url']),
                **details
            }

            all_data.append(channel_data)

    return all_data

def save_to_csv(data, filename='telegram_channels.csv'):
    """Save scraped data to CSV file"""
    if not data:
        print("No data to save")
        return

    # Define CSV columns
    fieldnames = [
        'category',
        'channel_name',
        'username',
        'channel_id',
        'members',
        'members_count',
        'language',
        'date_added',
        'tags',
        'description',
        'full_description',
        'rating',
        'total_reviews',
        'channel_url'
    ]

    print(f"\nSaving {len(data)} channels to {filename}...")

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

    print(f"Data saved successfully to {filename}")

if __name__ == "__main__":
    print("Starting web scraper for bestoftelegram.com...")
    print("=" * 60)

    # Scrape all channels
    channels_data = scrape_all_channels()

    # Save to CSV
    save_to_csv(channels_data)

    print("\n" + "=" * 60)
    print("Scraping completed!")
    print(f"Total channels scraped: {len(channels_data)}")
