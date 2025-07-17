#!/usr/bin/env python3
"""
Core matching engine for customer name reconciliation.
"""

from collections import defaultdict
from tqdm import tqdm
import pandas as pd

from name_utils import (
    clean_name, normalize_for_matching, strip_common_words, 
    create_name_tokens, calculate_token_similarity, get_name_signatures,
    is_meaningful_token, get_company_type_words
)


class NameMatcher:
    """Main class for matching customer names."""
    
    def __init__(self, min_token_similarity=0.95, min_match_ratio=0.8, min_meaningful_tokens=2):
        """Initialize with strict default thresholds."""
        self.min_token_similarity = min_token_similarity
        self.min_match_ratio = min_match_ratio
        self.min_meaningful_tokens = min_meaningful_tokens
    
    def names_match(self, name1, name2):
        """
        Check if two names match using strict fuzzy logic.
        Returns True if names are considered the same entity.
        """
        # Quick exact match check on cleaned names
        clean1 = clean_name(name1)
        clean2 = clean_name(name2)
        
        if clean1 == clean2:
            return True
        
        # Normalize for more flexible matching
        norm1 = normalize_for_matching(name1)
        norm2 = normalize_for_matching(name2)
        
        if norm1 == norm2:
            return True
        
        # Get stripped versions
        stripped1 = strip_common_words(norm1)
        stripped2 = strip_common_words(norm2)
        
        # If stripping removed everything, use normalized
        if not stripped1:
            stripped1 = norm1
        if not stripped2:
            stripped2 = norm2
            
        if not stripped1 or not stripped2:
            return False
        
        if stripped1 == stripped2:
            return True
        
        # Get tokens for fuzzy matching
        tokens1 = create_name_tokens(name1)
        tokens2 = create_name_tokens(name2)
        
        if not tokens1 or not tokens2:
            return False
        
        # Get meaningful tokens only
        meaningful1 = [t for t in tokens1 if is_meaningful_token(t)]
        meaningful2 = [t for t in tokens2 if is_meaningful_token(t)]
        
        # Special checks for preventing false matches
        
        # 1. Check for "United X" vs "United Y" type mismatches
        company_type1 = get_company_type_words(norm1)
        company_type2 = get_company_type_words(norm2)
        
        if company_type1 and company_type2 and company_type1 != company_type2:
            # Different company types (e.g., "Construction" vs "Rentals")
            # even if they share "United"
            return False
        
        # 2. Check for number-only matches (like "1" in different contexts)
        if len(meaningful1) == 1 and len(meaningful2) == 1:
            # Single meaningful token each
            if meaningful1[0].isdigit() or meaningful2[0].isdigit():
                # One is just a number - require exact match
                return meaningful1[0] == meaningful2[0]
        
        # 3. Check for cash/cod confusion
        lower1 = norm1.lower()
        lower2 = norm2.lower()
        
        # Don't match *cash with COD cash
        if ('*cash' in lower1 and 'cod' in lower2 and '*cod' not in lower1) or \
           ('*cash' in lower2 and 'cod' in lower1 and '*cod' not in lower2):
            return False
        
        # 4. Match tokens with fuzzy logic
        matched_tokens = 0
        matched_meaningful = 0
        used_tokens2 = set()
        token_pairs = []
        
        for t1 in tokens1:
            best_match = 0
            best_idx = -1
            best_t2 = None
            
            for idx, t2 in enumerate(tokens2):
                if idx not in used_tokens2:
                    similarity = calculate_token_similarity(t1, t2)
                    if similarity > best_match:
                        best_match = similarity
                        best_idx = idx
                        best_t2 = t2
            
            if best_match >= self.min_token_similarity:
                matched_tokens += 1
                if best_idx >= 0:
                    used_tokens2.add(best_idx)
                    token_pairs.append((t1, best_t2, best_match))
                    
                    # Count meaningful matches
                    if is_meaningful_token(t1) and is_meaningful_token(best_t2):
                        matched_meaningful += 1
        
        # 5. Strict requirements for matching
        
        # Need at least min_meaningful_tokens meaningful matches
        if matched_meaningful < self.min_meaningful_tokens:
            # Exception: if both names have only 1 meaningful token and they match perfectly
            if len(meaningful1) == 1 and len(meaningful2) == 1 and matched_meaningful == 1:
                # Check if it's a strong match
                for t1, t2, sim in token_pairs:
                    if t1 in meaningful1 and t2 in meaningful2 and sim >= 0.95:
                        return True
            return False
        
        # Calculate match ratios on meaningful tokens only
        if meaningful1 and meaningful2:
            meaningful_ratio1 = matched_meaningful / len(meaningful1)
            meaningful_ratio2 = matched_meaningful / len(meaningful2)
            min_meaningful_ratio = min(meaningful_ratio1, meaningful_ratio2)
            
            # Require high ratio of meaningful token matches
            if min_meaningful_ratio < self.min_match_ratio:
                return False
        
        # 6. Additional checks for specific patterns
        
        # Don't match if numbers don't align
        nums1 = [t for t in tokens1 if t.isdigit()]
        nums2 = [t for t in tokens2 if t.isdigit()]
        
        if nums1 and nums2:
            # Both have numbers - they should match
            if set(nums1) != set(nums2):
                return False
        elif nums1 or nums2:
            # One has numbers, other doesn't - be careful
            if matched_meaningful < 3:  # Need extra evidence
                return False
        
        # 7. Final decision
        return True
    
    def group_duplicates_within_file(self, df, name_column, file_label=""):
        """Group duplicate names within a single file."""
        name_groups = {}
        signature_map = defaultdict(list)
        
        # Pre-process all names
        names_data = []
        for idx, row in df.iterrows():
            if pd.isna(row[name_column]):
                continue
            
            original = str(row[name_column])
            signatures = get_name_signatures(original)
            
            names_data.append({
                'original': original,
                'signatures': signatures
            })
        
        # Group names
        for data in tqdm(names_data, desc=f"Grouping {file_label} duplicates"):
            original = data['original']
            signatures = data['signatures']
            found_match = False
            
            # Check all signatures for potential matches
            potential_groups = set()
            
            for sig in signatures:
                if sig in signature_map:
                    potential_groups.update(signature_map[sig])
            
            # Check each potential group
            for group_key in potential_groups:
                if group_key in name_groups and self.names_match(original, group_key):
                    name_groups[group_key].append(original)
                    for sig in signatures:
                        if group_key not in signature_map[sig]:
                            signature_map[sig].append(group_key)
                    found_match = True
                    break
            
            # If no match found, create new group
            if not found_match:
                name_groups[original] = [original]
                for sig in signatures:
                    signature_map[sig].append(original)
        
        return name_groups
    
    def match_across_groups(self, groups1, groups2, label1, label2):
        """Match groups from two different sources."""
        matches = []
        matched_keys2 = set()
        
        # Create signature map for groups2
        sig_map2 = defaultdict(list)
        
        for key2, names2 in groups2.items():
            # Use first name as representative
            rep2 = names2[0] if names2 else ""
            sigs2 = get_name_signatures(rep2)
            for sig in sigs2:
                sig_map2[sig].append(key2)
        
        # Match groups1 against groups2
        for key1, names1 in tqdm(groups1.items(), desc=f"Matching {label1} to {label2}"):
            rep1 = names1[0] if names1 else ""
            sigs1 = get_name_signatures(rep1)
            
            matched_key2 = None
            
            # Find potential matches via signatures
            potential_matches = set()
            for sig in sigs1:
                if sig in sig_map2:
                    potential_matches.update(sig_map2[sig])
            
            # Test each potential match
            for key2 in potential_matches:
                if key2 not in matched_keys2:
                    rep2 = groups2[key2][0] if groups2[key2] else ""
                    if self.names_match(rep1, rep2):
                        matched_key2 = key2
                        break
            
            if matched_key2:
                matched_keys2.add(matched_key2)
                matches.append((key1, names1, matched_key2, groups2[matched_key2]))
            else:
                matches.append((key1, names1, None, []))
        
        return matches, matched_keys2
