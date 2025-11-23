import csv
import re

print("\n" + "="*80)
print("CSV DATA ANALYSIS - ERRORS AND ISSUES")
print("="*80 + "\n")

with open('telegram_channels.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Issue 1: Empty or missing values
print("1. MISSING/EMPTY DATA:")
print("-" * 80)

empty_fields = {field: 0 for field in rows[0].keys()}
for row in rows:
    for field in row.keys():
        if not row[field] or row[field].strip() == '':
            empty_fields[field] += 1

for field, count in empty_fields.items():
    if count > 0:
        print(f"   {field:25} : {count:3} empty values ({count/len(rows)*100:.1f}%)")

# Issue 2: Whitespace issues
print("\n2. WHITESPACE ISSUES:")
print("-" * 80)

whitespace_issues = 0
fields_with_whitespace = {}

for row in rows:
    for field, value in row.items():
        if value and (value != value.strip() or '\n' in value or '  ' in value):
            whitespace_issues += 1
            fields_with_whitespace[field] = fields_with_whitespace.get(field, 0) + 1

for field, count in sorted(fields_with_whitespace.items(), key=lambda x: x[1], reverse=True):
    print(f"   {field:25} : {count:3} values with whitespace issues")

# Issue 3: Check category names
print("\n3. CATEGORY ISSUES:")
print("-" * 80)

categories = {}
for row in rows:
    cat = row['category'] if row['category'].strip() else '[EMPTY]'
    categories[cat] = categories.get(cat, 0) + 1

for cat, count in sorted(categories.items()):
    if cat == '[EMPTY]' or len(cat) < 2:
        print(f"   WARNING: '{cat}' has {count} channels")

# Issue 4: Check for duplicate channels
print("\n4. DUPLICATE CHANNELS:")
print("-" * 80)

usernames = {}
for i, row in enumerate(rows):
    username = row['username']
    if username in usernames:
        print(f"   DUPLICATE: {username} appears in rows {usernames[username]} and {i+2}")
    else:
        usernames[username] = i+2

if not any('DUPLICATE' in str(usernames.values()) for _ in [1]):
    duplicate_count = len(rows) - len(set(row['username'] for row in rows))
    if duplicate_count > 0:
        print(f"   Found {duplicate_count} duplicate channels")
    else:
        print("   No duplicates found")

# Issue 5: Data consistency
print("\n5. DATA CONSISTENCY:")
print("-" * 80)

inconsistencies = []

for i, row in enumerate(rows):
    row_num = i + 2  # +1 for 0-index, +1 for header

    # Check if username matches channel_id
    if row['username'] and row['channel_id'] and row['username'] != row['channel_id']:
        inconsistencies.append(f"   Row {row_num}: username ({row['username']}) != channel_id ({row['channel_id']})")

    # Check if members field matches members_count
    if row['members'] and row['members_count'] and row['members'] != row['members_count']:
        inconsistencies.append(f"   Row {row_num}: members ({row['members']}) != members_count ({row['members_count']})")

if inconsistencies:
    for issue in inconsistencies[:10]:  # Show first 10
        print(issue)
    if len(inconsistencies) > 10:
        print(f"   ... and {len(inconsistencies) - 10} more")
else:
    print("   No major inconsistencies found")

print("\n" + "="*80)
print("SUMMARY:")
print("="*80)
print(f"Total rows analyzed: {len(rows)}")
print(f"Total whitespace issues: {whitespace_issues}")
print(f"Fields with missing data: {sum(1 for v in empty_fields.values() if v > 0)}")
print("\n" + "="*80 + "\n")
