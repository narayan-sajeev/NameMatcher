#!/usr/bin/env python3
"""
Customer Name Reconciliation Tool
Main program for matching customer names across multiple data sources.
"""

import pandas as pd
from tqdm import tqdm
from collections import defaultdict
import time
import csv

# Import all utilities
from constants import IGNORE_WORDS, GEO_TERMS
from name_utils import (
    clean_name, strip_common_words, normalize_for_matching,
    create_name_tokens, calculate_token_similarity
)
from matching_engine import NameMatcher
from file_splitter import split_results


def load_data():
    """Load data from all sources with proper quote handling."""
    print("Loading data files...")
    
    # Load TB and FB data with proper quote handling
    tb_df = pd.read_csv('tb_customer_names.csv', quoting=csv.QUOTE_ALL, quotechar='"')
    fb_df = pd.read_csv('fb_customer_names.csv', quoting=csv.QUOTE_ALL, quotechar='"')
    
    # Load QB data from Excel - only load Active sheet
    qb_all_customers = []
    xl_file = pd.ExcelFile('qb_customer_names.xlsx')
    
    if 'Active' in xl_file.sheet_names:
        sheet_df = pd.read_excel(xl_file, sheet_name='Active')
        
        if 'Customer' in sheet_df.columns:
            customers = sheet_df[sheet_df['Customer'].notna()]['Customer'].tolist()
            qb_all_customers.extend(customers)
            print(f"Loaded {len(customers)} active customers from QB")
    else:
        print("Warning: No 'Active' sheet found in QB file")
    
    qb_df = pd.DataFrame({'Customer': qb_all_customers})
    
    print(f"\nLoaded {len(tb_df)} TB records, {len(fb_df)} FB records, and {len(qb_df)} QB records (active only)")
    
    return tb_df, fb_df, qb_df


def find_best_representative(names):
    """Find the best representative name from a list of names."""
    if not names:
        return ""
    
    # Clean all names first
    cleaned_names = [(name, clean_name(name)) for name in names]
    
    # Prefer names with more complete information
    # Sort by: presence of punctuation/special chars (more formal), then length
    def name_score(name_tuple):
        original, cleaned = name_tuple
        has_punctuation = any(c in original for c in '.,&-\'')
        has_lowercase = any(c.islower() for c in original)
        # Prefer names without asterisks
        has_asterisk = '*' in original
        return (not has_asterisk, has_punctuation, has_lowercase, len(original))
    
    # Get the best original name
    best_name = sorted(cleaned_names, key=name_score, reverse=True)[0][0]
    
    return best_name


def main():
    """Main execution function."""
    start_time = time.time()
    
    # Load data
    tb_df, fb_df, qb_df = load_data()
    
    # Initialize matcher with stricter settings
    matcher = NameMatcher(
        min_token_similarity=0.95,  # Very high similarity required
        min_match_ratio=0.8,        # High ratio required
        min_meaningful_tokens=2     # At least 2 meaningful tokens must match
    )
    
    # Group duplicates within each file
    print("\nGrouping duplicates within each file...")
    tb_groups = matcher.group_duplicates_within_file(tb_df, 'account_name', 'TB')
    fb_groups = matcher.group_duplicates_within_file(fb_df, 'customer', 'FB')
    qb_groups = matcher.group_duplicates_within_file(qb_df, 'Customer', 'QB')
    
    print(f"Found {len(tb_groups)} unique TB groups, {len(fb_groups)} unique FB groups, {len(qb_groups)} unique QB groups")
    
    # Match across all three files
    matches = []
    all_matched = defaultdict(set)
    
    # First, match TB against FB and QB
    tb_fb_matches, matched_fb = matcher.match_across_groups(tb_groups, fb_groups, 'TB', 'FB')
    
    # For each TB-FB match, check if there's a QB match
    print("Finding three-way matches...")
    for tb_key, tb_names, fb_key, fb_names in tqdm(tb_fb_matches):
        qb_key = None
        qb_names = []
        
        # Try to find QB match through FB first, then direct TB-QB
        candidates = []
        if fb_key:
            candidates.append((fb_key, fb_names))
        candidates.append((tb_key, tb_names))
        
        for cand_key, cand_names in candidates:
            if not qb_key:
                cand_rep = find_best_representative(cand_names)
                for qb_k, qb_n in qb_groups.items():
                    if qb_k not in all_matched['qb']:
                        qb_rep = find_best_representative(qb_n)
                        if matcher.names_match(cand_rep, qb_rep):
                            qb_key = qb_k
                            qb_names = qb_n
                            break
        
        # Determine the best standardized name
        all_names = tb_names + (fb_names if fb_key else []) + qb_names
        best_name = find_best_representative(all_names)
        
        # Capitalize properly
        standardized_name = ' '.join(word.capitalize() for word in best_name.split())
        
        matches.append({
            'standardized_name': standardized_name,
            'tb_names': tb_names,
            'fb_names': fb_names if fb_key else None,
            'qb_names': qb_names if qb_key else None
        })
        
        all_matched['tb'].add(tb_key)
        if fb_key:
            all_matched['fb'].add(fb_key)
        if qb_key:
            all_matched['qb'].add(qb_key)
    
    # Match remaining FB against QB
    remaining_fb = {k: v for k, v in fb_groups.items() if k not in all_matched['fb']}
    remaining_qb = {k: v for k, v in qb_groups.items() if k not in all_matched['qb']}
    
    if remaining_fb and remaining_qb:
        fb_qb_matches, matched_qb = matcher.match_across_groups(remaining_fb, remaining_qb, 'FB', 'QB')
        
        for fb_key, fb_names, qb_key, qb_names in fb_qb_matches:
            all_names = fb_names + (qb_names if qb_key else [])
            best_name = find_best_representative(all_names)
            standardized_name = ' '.join(word.capitalize() for word in best_name.split())
            
            matches.append({
                'standardized_name': standardized_name,
                'tb_names': None,
                'fb_names': fb_names,
                'qb_names': qb_names if qb_key else None
            })
            
            all_matched['fb'].add(fb_key)
            if qb_key:
                all_matched['qb'].add(qb_key)
    
    # Add remaining unmatched entries
    print("Adding unmatched entries...")
    
    for source, groups, key in [
        ('tb', tb_groups, 'tb_names'),
        ('fb', fb_groups, 'fb_names'),
        ('qb', qb_groups, 'qb_names')
    ]:
        for group_key, names in groups.items():
            if group_key not in all_matched[source]:
                best_name = find_best_representative(names)
                standardized_name = ' '.join(word.capitalize() for word in best_name.split())
                
                match_dict = {
                    'standardized_name': standardized_name,
                    'tb_names': None,
                    'fb_names': None,
                    'qb_names': None
                }
                match_dict[key] = names
                matches.append(match_dict)
    
    # Create final DataFrame
    result = pd.DataFrame(matches)
    
    # Convert lists to semicolon-separated strings
    result['tb_names'] = result['tb_names'].apply(lambda x: '; '.join(x) if x else None)
    result['fb_names'] = result['fb_names'].apply(lambda x: '; '.join(x) if x else None)
    result['qb_names'] = result['qb_names'].apply(lambda x: '; '.join(x) if x else None)
    
    # Sort by standardized name
    result = result.sort_values('standardized_name').reset_index(drop=True)
    
    # Save with proper quote handling
    result.to_csv('customer_reconciliation.csv', index=False, quoting=csv.QUOTE_ALL)
    
    # Split results into multiple files if needed
    output_files = split_results(result, max_rows_per_file=10000)
    
    # Print summary
    elapsed_time = time.time() - start_time
    print(f"\nReconciliation complete in {elapsed_time:.1f} seconds!")
    print(f"Total unique customers: {len(result)}")
    print(f"Customers in all 3 systems: {len(result[(result['tb_names'].notna()) & (result['fb_names'].notna()) & (result['qb_names'].notna())])}")
    print(f"Customers in 2 systems: {len(result[((result['tb_names'].notna()) & (result['fb_names'].notna()) & (result['qb_names'].isna())) | ((result['tb_names'].notna()) & (result['fb_names'].isna()) & (result['qb_names'].notna())) | ((result['tb_names'].isna()) & (result['fb_names'].notna()) & (result['qb_names'].notna()))])}")
    print(f"Customers in 1 system only: {len(result[((result['tb_names'].notna()) & (result['fb_names'].isna()) & (result['qb_names'].isna())) | ((result['tb_names'].isna()) & (result['fb_names'].notna()) & (result['qb_names'].isna())) | ((result['tb_names'].isna()) & (result['fb_names'].isna()) & (result['qb_names'].notna()))])}")
    
    print(f"\nOutput saved to {len(output_files)} file(s):")
    for f in output_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
