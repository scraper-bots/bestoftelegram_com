import csv

with open('telegram_channels.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETE - SUMMARY")
    print(f"{'='*80}")
    print(f"Total channels scraped: {len(rows)}")
    print(f"Total categories: {len(set(row['category'] for row in rows))}")
    print(f"\n{'='*80}")
    print("SAMPLE DATA (First 5 channels):")
    print(f"{'='*80}\n")

    for i, row in enumerate(rows[:5], 1):
        print(f"{i}. {row['channel_name']} ({row['username']})")
        print(f"   Category: {row['category']}")
        print(f"   Members: {row['members_count']}")
        print(f"   Language: {row['language']}")
        print(f"   Date Added: {row['date_added']}")
        print(f"   Tags: {row['tags']}")
        print(f"   URL: {row['channel_url']}")
        print()

    print(f"{'='*80}")
    print("Categories breakdown:")
    print(f"{'='*80}")

    categories = {}
    for row in rows:
        cat = row['category']
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"{cat:30} : {count:3} channels")

    print(f"\n{'='*80}")
    print(f"Data saved to: telegram_channels.csv")
    print(f"{'='*80}\n")
