import re

import pandas as pd
from tqdm import tqdm

from constants import IGNORE_WORDS, GEO_TERMS


def clean_name(name):
    """Basic cleaning - uppercase, remove special characters and phone numbers."""
    if pd.isna(name):
        return ""
    name = str(name).upper().strip()

    # Remove phone numbers (patterns like (603) 228-3611, 603-228-3611, 6032283611, etc.)
    name = re.sub(r'\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '', name)

    # Remove all non-alphanumeric characters (preserve internal spaces)
    name = re.sub(r'[^A-Z0-9 ]+', ' ', name)

    # Normalize spaces
    name = re.sub(r'\s+', ' ', name).strip()

    return name


def strip_common_words(name):
    """Remove ignorable and common words from a name."""
    if not name:
        return ""

    # Normalize and split
    name = re.sub(r'[^\w\s\-]', ' ', name)
    words = name.split()

    # First pass: strip ignorable words
    core_words = [w for w in words if w not in IGNORE_WORDS]

    # Second pass: remove geographic-only names *only* if other words remain
    meaningful_words = [w for w in core_words if w not in GEO_TERMS]

    if meaningful_words:
        return ' '.join(meaningful_words)
    else:
        return ' '.join(core_words)


# Still allow full containment with word boundaries
def contains_whole_phrase(shorter, longer):
    pattern = r'\b' + re.escape(shorter) + r'\b'
    return re.search(pattern, longer) is not None


def names_match(name1, name2):
    """Check if two names match using strict criteria."""
    clean1 = clean_name(name1)
    clean2 = clean_name(name2)

    if clean1 == clean2:
        return True

    stripped1 = strip_common_words(clean1)
    stripped2 = strip_common_words(clean2)

    if stripped1 == stripped2:
        return True

    if not stripped1 or not stripped2:
        return False

    # Only apply plural-suffix logic if base name is at least 2 characters
    if len(stripped1) >= 2 and stripped1 + 'S' in stripped2:
        return True
    if len(stripped2) >= 2 and stripped2 + 'S' in stripped1:
        return True

    # Require at least 2 shared meaningful words (longer than 1 character)
    words1 = set(w for w in stripped1.split() if len(w) > 1)
    words2 = set(w for w in stripped2.split() if len(w) > 1)
    common = words1 & words2

    if len(common) >= 2:
        return True

    if contains_whole_phrase(stripped1, stripped2) or contains_whole_phrase(stripped2, stripped1):
        # If one name contains the other as a whole phrase
        if len(common) >= 1 and min(len(words1), len(words2)) >= 2:
            return True
        # Or if the common word is a significant part of the name
        if len(common) == 1 and min(len(stripped1), len(stripped2)) >= 5:
            return True

    return False


# Capitalize the first letter of each word
def capitalize_words(name):
    """Capitalize the first letter of each word in a name."""
    # Clean the name first
    name = re.sub(r'\s+', ' ', re.sub(r"[^A-Za-z0-9']", ' ', str(name))).strip()
    # Then capitalize each word
    return ' '.join(word.capitalize() for word in name.split())


# Load data
tb_df = pd.read_csv('tb_customer_names.csv')
fb_df = pd.read_csv('fb_customer_names.csv')

print(f"Loaded {len(tb_df)} TB records and {len(fb_df)} FB records")

# Remove exact duplicates
tb_df = tb_df.drop_duplicates(subset=['account_name'])
fb_df = fb_df.drop_duplicates(subset=['customer'])

# Find matches
matches = []
matched_tb_indices = set()
matched_fb_indices = set()

for tb_idx, tb_row in tqdm(tb_df.iterrows(), total=len(tb_df), desc="Matching TB customers"):
    if pd.isna(tb_row['account_name']):
        continue

    matched = False
    for fb_idx, fb_row in fb_df.iterrows():
        if fb_idx in matched_fb_indices or pd.isna(fb_row['customer']):
            continue

        if names_match(tb_row['account_name'], fb_row['customer']):
            # Use the longer name
            if len(str(tb_row['account_name'])) >= len(str(fb_row['customer'])):
                name = tb_row['account_name']
            else:
                name = fb_row['customer']

            # Capitalize the standardized name
            name = capitalize_words(name)

            matches.append({
                'standardized_name': name,
                'tb_name': tb_row['account_name'],
                'fb_name': fb_row['customer']
            })
            matched_tb_indices.add(tb_idx)
            matched_fb_indices.add(fb_idx)
            matched = True
            break

# Add unmatched TB customers
for idx, row in tb_df.iterrows():
    if idx not in matched_tb_indices and pd.notna(row['account_name']):
        # Capitalize the TB name
        name = capitalize_words(row['account_name'])

        matches.append({
            'standardized_name': name,
            'tb_name': row['account_name'],
            'fb_name': None
        })

# Add unmatched FB customers
for idx, row in fb_df.iterrows():
    if idx not in matched_fb_indices and pd.notna(row['customer']):
        # Capitalize the FB name
        name = capitalize_words(row['customer'])

        matches.append({
            'standardized_name': name,
            'tb_name': None,
            'fb_name': row['customer']
        })

# Create final DataFrame and save
result = pd.DataFrame(matches).sort_values('standardized_name').reset_index(drop=True)
result.to_csv('customer_reconciliation.csv', index=False)
