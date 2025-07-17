#!/usr/bin/env python3
"""
Test script to verify matching logic handles various edge cases.
"""

from matching_engine import NameMatcher


def test_matching():
    """Test various name matching scenarios."""
    matcher = NameMatcher(min_meaningful_tokens=2)
    
    test_cases = [
        # Original tests
        ("A&N TOWING AND TRANSPORT", "A N TOWING AND TRANSPORT", True, "& vs spaces"),
        ("A.P.R &R.I", "A P R R I", True, "Periods and & removal"),
        ("A.P.R. & R., INC", "A P R R Inc", True, "Complex punctuation"),
        ("ALBERTSON COMPANIES", "ALBERTSONS COMPANIES", True, "Missing 'S'"),
        ("Albertsons Companies - Shaws", "Albertons Companies Shaws", True, "Missing 'S' and dash"),
        ("3 ARROWS TRUCKING LLC", "ARROW SERVICE TOWING", False, "Different companies"),
        ("Abbott's Garage & Wrecker Service LLC", "I-70 WRECKER SERVICE & GARAGE", False, "Partial overlap but different"),
        ("A&A EXPRESS LLC", "A A Express Llc", True, "Case and & variations"),
        ("CLEAN RENTALS", "A A Express Llc", False, "Completely different names"),
        ("1 Source Solutions Logistics", "Resource Management", False, "Different despite 'source'"),
        ("ARC SOURCE, INC", "1 Source Solutions Logistics", False, "Different companies with 'source'"),
        ("WHITE ARROW", "3 ARROWS TRUCKING LLC", False, "Different arrow companies"),
        ("ARROW SERVICE", "3 ARROWS", False, "Number mismatch"),
        ("A&A", "A A", True, "Simple & replacement"),
        
        # New tests for identified issues
        ("*cash/private Retail Customer", "COD CASH CUSTOMERS", False, "Cash vs COD - different types"),
        ("United Construction & Forestry", "United Rentals", False, "Different United companies"),
        ("United Steel Inc", "United Transportation", False, "Different United companies 2"),
        ("1 Source Solutions", "CLEAN HARBORS 1", False, "Only share number 1"),
        ("1 Source Solutions", "wrecker 1", False, "Only share number 1 - different context"),
        ("A&G Construction", "G ENTERPRISE", False, "Only share letter G"),
        ("Nitco Forklift Concord", "Forklifts of NH", False, "Specific vs generic company"),
        ('"A Perfect Move, Inc."', '"A Perfect Move, Inc."', True, "Quotes should not prevent match"),
        ("A&J BEVERAGE", "BELLAVANCE BEVERAGE", False, "Different beverage companies"),
        ("Bob's Garage", "Dave's Garage", False, "Different garage owners"),
        
        # Edge cases
        ("AAA FREIGHT", "AAA FREIGHT", True, "Exact match with short name"),
        ("A1 TRANS LLC", "A R TRANS LLC", False, "Different letter-number combos"),
        ("CLEAN HARBORS", "CLEAN RENTALS", False, "Share 'CLEAN' but different business"),
        ("ARROW", "ARROWS", True, "Singular vs plural"),
        ("*COD Cash Customer", "COD CASH CUSTOMERS", True, "COD cash variations should match"),
    ]
    
    print("Testing name matching logic:\n")
    
    passed = 0
    failed = 0
    
    for name1, name2, expected, description in test_cases:
        result = matcher.names_match(name1, name2)
        status = "✓" if result == expected else "✗"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} {description}")
        print(f"  '{name1}' vs '{name2}'")
        print(f"  Expected: {expected}, Got: {result}")
        
        # Show tokens for debugging failed cases
        if result != expected:
            from name_utils import create_name_tokens, is_meaningful_token
            tokens1 = create_name_tokens(name1)
            tokens2 = create_name_tokens(name2)
            meaningful1 = [t for t in tokens1 if is_meaningful_token(t)]
            meaningful2 = [t for t in tokens2 if is_meaningful_token(t)]
            print(f"  Tokens1: {tokens1} (meaningful: {meaningful1})")
            print(f"  Tokens2: {tokens2} (meaningful: {meaningful2})")
        print()
    
    print(f"\nSummary: {passed} passed, {failed} failed")
    
    # Additional tests for normalization
    print("\nTesting normalization:")
    from name_utils import normalize_for_matching, create_name_tokens
    
    norm_tests = [
        ("A&N TOWING", "A AND N TOWING"),
        ("A.P.R. & R., INC", "A P R AND R INC"),
        ("Abbott's Garage", "ABBOTTS GARAGE"),
        ("A&A", "A AND A"),
        ('"Company Name, Inc."', "COMPANY NAME INC"),
    ]
    
    for original, expected in norm_tests:
        normalized = normalize_for_matching(original)
        print(f"'{original}' -> '{normalized}' (expected: '{expected}')")
        
    print("\nTesting tokenization:")
    token_tests = [
        "3 ARROWS TRUCKING LLC",
        "A.P.R. & R., INC",
        "1 Source Solutions Logistics",
        "A&A EXPRESS",
        "ARROW SERVICE",
        "United Construction & Forestry",
        "*cash/private Retail Customer",
    ]
    
    for name in token_tests:
        tokens = create_name_tokens(name)
        from name_utils import is_meaningful_token
        meaningful = [t for t in tokens if is_meaningful_token(t)]
        print(f"'{name}' -> all: {tokens}, meaningful: {meaningful}")


if __name__ == "__main__":
    test_matching()
