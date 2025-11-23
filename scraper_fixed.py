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

def clean_text(text):
    """Clean text by removing extra whitespace and newlines"""
    if not text:
        return ""
    # Replace multiple spaces/newlines with single space
    cleaned = ' '.join(text.split())
    return cleaned.strip()

def get_categories():
    """Scrape all categories from the main channels page"""
    print("Fetching categories...", flush=True)
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
                category_name = clean_text(link.find('h2').text)
                category_url = link['href']

                categories.append({
                    'name': category_name,
                    'url': category_url
                })
        except Exception as e:
            print(f"Error parsing category: {e}", flush=True)
            continue

    print(f"Found {len(categories)} categories", flush=True)
    return categories

def get_channels_from_category(category_url):
    """Scrape all channels from a category page"""
    # Ensure category URL includes /channels/ prefix
    if not category_url.startswith('/channels/'):
        category_url = f'/channels/{category_url}'
    full_url = urljoin(BASE_URL, category_url)
    print(f"Fetching channels from {full_url}...", flush=True)

    soup = get_soup(full_url)
    if not soup:
        return []

    channels = []
    channel_areas = soup.find_all('div', class_='channel-area')

    for area in channel_areas:
        try:
            # Get channel name
            name_elem = area.find('h2', class_='font-style1')
            channel_name = clean_text(name_elem.text) if name_elem else ""

            # Get channel username
            username_elem = area.find('p', class_='color-gray')
            username = ""
            if username_elem and username_elem.find('i'):
                username = clean_text(username_elem.find('i').text)

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
                description = clean_text(desc_elem.find('p').text)

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
            print(f"Error parsing channel: {e}", flush=True)
            continue

    print(f"Found {len(channels)} channels", flush=True)
    return channels

def get_channel_details(channel_url):
    """Scrape detailed information from a channel page"""
    full_url = urljoin(BASE_URL, channel_url)
    print(f"Fetching details from {full_url}...", flush=True)

    soup = get_soup(full_url)
    if not soup:
        return {}

    details = {}

    try:
        # Get channel details section
        details_section = soup.find('div', class_='reuse-grid', style=lambda x: x and 'padding-top:15px' in x)

        if details_section:
            # Find the main <p> tag with all details
            detail_p = details_section.find('p')

            if detail_p:
                # Get text but split by line breaks properly
                # Replace <br/> with newlines first
                for br in detail_p.find_all('br'):
                    br.replace_with('\n')

                # Now get the text with newlines
                full_text = detail_p.get_text()

                # Split into lines
                lines = full_text.split('\n')

                for line in lines:
                    line = clean_text(line)
                    if not line or ':' not in line:
                        continue

                    # Extract Channel ID
                    if 'Channel ID' in line:
                        match = re.search(r'Channel ID\s*:\s*(@\S+)', line)
                        if match:
                            details['channel_id'] = match.group(1).strip()

                    # Extract Language
                    elif 'Language' in line:
                        match = re.search(r'Language\s*:\s*(.+?)$', line)
                        if match:
                            details['language'] = match.group(1).strip()

                    # Extract Members
                    elif 'Members' in line:
                        match = re.search(r'Members\s*:\s*([\d,]+)', line)
                        if match:
                            details['members_count'] = match.group(1).replace(',', '').strip()

                    # Extract Date Added
                    elif 'Date Added' in line:
                        match = re.search(r'Date Added\s*:\s*([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})', line)
                        if match:
                            details['date_added'] = match.group(1).strip()

            # Extract Category from link in details section
            category_link = details_section.find('a', href=lambda x: x and '/channels/' in x)
            if category_link:
                details['category'] = clean_text(category_link.get_text())

        # Extract tags - find all tag links on the page
        tags = []
        tag_links = soup.find_all('a', href=lambda x: x and '/tag/' in x)
        for tag_link in tag_links:
            tag_text = clean_text(tag_link.get_text())
            if tag_text and tag_text not in tags:  # Avoid duplicates
                tags.append(tag_text)
        details['tags'] = ', '.join(tags) if tags else ""

        # Extract full description
        desc_sections = soup.find_all('div', class_='reuse-grid')
        for section in desc_sections:
            h2 = section.find('h2')
            if h2 and 'Channel Description' in h2.text:
                desc_p = section.find('p')
                if desc_p:
                    details['full_description'] = clean_text(desc_p.get_text())
                break

        # Extract rating
        rating_div = soup.find('div', class_='rating_widget')
        if rating_div:
            rating_text = rating_div.get_text()
            rating_match = re.search(r'Rated\s+(\S+)\s+out of\s+(\d+)', rating_text)
            if rating_match:
                details['rating'] = rating_match.group(1).strip()
                details['total_reviews'] = rating_match.group(2).strip()

    except Exception as e:
        print(f"Error parsing channel details: {e}", flush=True)

    return details

def scrape_all_channels():
    """Main function to scrape all channels from all categories"""
    all_data = []
    seen_usernames = set()  # Track usernames to avoid duplicates

    # Get all categories
    categories = get_categories()

    for i, category in enumerate(categories, 1):
        print(f"\n[{i}/{len(categories)}] Processing category: {category['name']}", flush=True)

        # Get all channels in this category
        channels = get_channels_from_category(category['url'])

        for j, channel in enumerate(channels, 1):
            # Skip if we've already scraped this channel
            if channel['username'] in seen_usernames:
                print(f"  [{j}/{len(channels)}] Skipping duplicate: {channel['username']}", flush=True)
                continue

            print(f"  [{j}/{len(channels)}] Processing channel: {channel['name']}", flush=True)

            # Get detailed information
            details = get_channel_details(channel['url'])

            # Use category from details if available, otherwise use current category
            final_category = details.get('category', '') or category['name']

            # Combine all data
            channel_data = {
                'category': final_category,
                'channel_name': channel['name'],
                'username': channel['username'],
                'channel_id': details.get('channel_id', ''),
                'members': channel['members'],
                'members_count': details.get('members_count', ''),
                'language': details.get('language', ''),
                'date_added': details.get('date_added', ''),
                'tags': details.get('tags', ''),
                'description': channel['description'],
                'full_description': details.get('full_description', ''),
                'rating': details.get('rating', ''),
                'total_reviews': details.get('total_reviews', ''),
                'channel_url': urljoin(BASE_URL, channel['url']),
            }

            all_data.append(channel_data)
            seen_usernames.add(channel['username'])

    return all_data

def save_to_csv(data, filename='telegram_channels.csv'):
    """Save scraped data to CSV file"""
    if not data:
        print("No data to save", flush=True)
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

    print(f"\nSaving {len(data)} channels to {filename}...", flush=True)

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

    print(f"Data saved successfully to {filename}", flush=True)

if __name__ == "__main__":
    print("Starting web scraper for bestoftelegram.com...", flush=True)
    print("=" * 60, flush=True)

    # Scrape all channels
    channels_data = scrape_all_channels()

    # Save to CSV
    save_to_csv(channels_data)

    print("\n" + "=" * 60, flush=True)
    print("Scraping completed!", flush=True)
    print(f"Total channels scraped: {len(channels_data)}", flush=True)
