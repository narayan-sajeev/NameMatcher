#!/usr/bin/env python3
"""
Name processing utilities for customer name reconciliation.
"""

import re
import pandas as pd
from constants import IGNORE_WORDS, GEO_TERMS


def clean_name(name):
    """Basic cleaning - uppercase, remove special characters and phone numbers."""
    if pd.isna(name):
        return ""
    name = str(name).upper().strip()
    
    # Remove phone numbers
    name = re.sub(r'\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '', name)
    
    # Remove all non-alphanumeric characters (preserve internal spaces)
    name = re.sub(r'[^A-Z0-9 ]+', ' ', name)
    
    # Normalize spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def normalize_for_matching(name):
    """Normalize name for matching - handles punctuation variations."""
    if pd.isna(name):
        return ""
    
    name = str(name).upper().strip()
    
    # Remove phone numbers first
    name = re.sub(r'\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '', name)
    
    # Handle special &R patterns more carefully
    # Convert &R.I to AND R I
    name = re.sub(r'&R\.I', ' AND R I', name)
    # Convert &R. to AND R
    name = re.sub(r'&R\.', ' AND R ', name)
    
    # Replace & with AND with proper spacing
    name = re.sub(r'\s*&\s*', ' AND ', name)
    
    # Now handle other replacements
    replacements = {
        r'\.': ' ',  # Remove periods
        r',': ' ',   # Remove commas
        r"'S\b": 'S',  # Remove possessive apostrophes
        r"'": '',    # Remove other apostrophes
        r'-': ' ',     # Replace hyphens with spaces
        r'/': ' ',     # Replace slashes with spaces
        r'\+': ' AND ',  # Plus sign to AND
        r':': ' ',     # Replace colons with spaces
        r';': ' ',     # Replace semicolons with spaces
        r'\*': '',     # Remove asterisks
        r'`': '',      # Remove backticks
        r'"': '',      # Remove quotes
    }
    
    for pattern, replacement in replacements.items():
        name = re.sub(pattern, replacement, name)
    
    # Remove other punctuation
    name = re.sub(r'[^A-Z0-9 ]+', ' ', name)
    
    # Normalize spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def strip_common_words(name):
    """Remove ignorable and common words from a name."""
    if not name:
        return ""
    
    words = name.split()
    
    # First pass: strip ignorable words (business terms, etc.)
    core_words = [w for w in words if w not in IGNORE_WORDS]
    
    # If we stripped everything, return the original
    if not core_words:
        return ' '.join(words)
    
    # Second pass: remove geographic-only names only if other words remain
    meaningful_words = [w for w in core_words if w not in GEO_TERMS]
    
    if meaningful_words:
        return ' '.join(meaningful_words)
    elif core_words:
        return ' '.join(core_words)
    else:
        # If everything was stripped, keep at least something
        return ' '.join(words)


def create_name_tokens(name):
    """Create tokens from a name for matching."""
    normalized = normalize_for_matching(name)
    stripped = strip_common_words(normalized)
    
    if not stripped:
        # If stripping removed everything, work with normalized version
        stripped = normalized
    
    if not stripped:
        return []
    
    # Get all tokens first
    all_tokens = stripped.split()
    
    # Filter tokens - be more inclusive
    tokens = []
    
    for token in all_tokens:
        # Always include numbers
        if any(c.isdigit() for c in token):
            tokens.append(token)
        # Include letters of any length for initials/abbreviations
        elif token.isalpha():
            tokens.append(token)
        # Include mixed alphanumeric
        elif token.isalnum():
            tokens.append(token)
    
    return list(set(tokens))  # Remove duplicates


def is_meaningful_token(token):
    """Check if a token is meaningful (not just a single letter or very short)."""
    if not token:
        return False
    
    # Numbers are always meaningful
    if token.isdigit():
        return True
    
    # Mixed alphanumeric is meaningful
    if any(c.isdigit() for c in token):
        return True
    
    # Single letters are not meaningful unless they're part of specific patterns
    if len(token) == 1:
        return False
    
    # Two-letter tokens - only meaningful if they're common abbreviations
    if len(token) == 2:
        # Common meaningful 2-letter abbreviations
        meaningful_2letter = {'CO', 'PC', 'PA', 'LP', 'AG', 'AC', 'RH'}
        return token in meaningful_2letter
    
    # Everything 3+ letters is meaningful
    return True


def get_company_type_words(name):
    """Extract company type words (like CONSTRUCTION, RENTALS, etc.)."""
    # Common company type indicators
    type_words = {
        'CONSTRUCTION', 'RENTALS', 'RENTAL', 'STEEL', 'TRANSPORTATION',
        'LOGISTICS', 'FREIGHT', 'TRUCKING', 'TOWING', 'GARAGE', 'WRECKER',
        'BEVERAGE', 'BEVERAGES', 'SUPPLY', 'SUPPLIES', 'FORESTRY',
        'EQUIPMENT', 'SOLUTIONS', 'SERVICES', 'SERVICE'
    }
    
    name_upper = name.upper()
    found_types = []
    
    for type_word in type_words:
        if type_word in name_upper:
            found_types.append(type_word)
    
    return found_types


def calculate_token_similarity(token1, token2):
    """Calculate similarity between two tokens - be strict."""
    if token1 == token2:
        return 1.0
    
    # Don't match different numbers
    if token1.isdigit() and token2.isdigit():
        return 0.0 if token1 != token2 else 1.0
    
    # Don't match number with non-number
    if token1.isdigit() != token2.isdigit():
        return 0.0
    
    # Handle plural forms for longer words only
    if len(token1) > 3 and len(token2) > 3:
        if token1 + 'S' == token2 or token2 + 'S' == token1:
            return 0.95
        if token1 + 'ES' == token2 or token2 + 'ES' == token1:
            return 0.95
    
    # For very short tokens (<=3 chars), require exact match
    if len(token1) <= 3 or len(token2) <= 3:
        return 0.0
    
    # For longer tokens, only match very similar ones (typos)
    if len(token1) > 4 and len(token2) > 4:
        # Check for single character difference (typo)
        if abs(len(token1) - len(token2)) <= 1:
            # Count matching characters in order
            matches = 0
            i, j = 0, 0
            while i < len(token1) and j < len(token2):
                if token1[i] == token2[j]:
                    matches += 1
                    i += 1
                    j += 1
                elif len(token1) > len(token2):
                    i += 1
                elif len(token2) > len(token1):
                    j += 1
                else:
                    i += 1
                    j += 1
            
            ratio = matches / max(len(token1), len(token2))
            if ratio >= 0.85:  # Very high similarity required
                return ratio
    
    return 0.0


def get_name_signatures(name):
    """Create multiple signatures for a name to enable fuzzy matching."""
    tokens = create_name_tokens(name)
    meaningful = [t for t in tokens if is_meaningful_token(t)]
    
    if not meaningful:
        # If no meaningful tokens, use all tokens
        meaningful = tokens
    
    if not meaningful:
        return []
    
    signatures = []
    
    # Primary signature: all meaningful tokens sorted
    signatures.append(' '.join(sorted(meaningful)))
    
    # For names with multiple meaningful tokens, create subset signatures
    if len(meaningful) > 2:
        # Don't create too many signatures - just the most important subsets
        # Signature without each token (for partial matches)
        for i in range(len(meaningful)):
            if len(meaningful) > 3 or i < 2:  # Limit subset creation
                subset = meaningful[:i] + meaningful[i+1:]
                if subset:
                    signatures.append(' '.join(sorted(subset)))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_sigs = []
    for sig in signatures:
        if sig not in seen and sig:  # Don't add empty signatures
            seen.add(sig)
            unique_sigs.append(sig)
    
    return unique_sigs
