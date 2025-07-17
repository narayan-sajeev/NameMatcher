# Customer Name Reconciliation

This Python tool reconciles customer name records from three different sources using advanced fuzzy matching logic. It handles typos, punctuation variations, abbreviations, and other common data quality issues while grouping duplicates within and across files.

## 🔍 Features

* **Advanced name matching**:
  - Handles punctuation variations (A&N vs A N, A.P.R. vs APR)
  - Manages abbreviations (LLC vs Llc, & vs AND)
  - Detects typos and minor spelling differences (ALBERTSON vs ALBERTSONS)
  - Preserves business entity distinctions (won't match "3 ARROWS" with "ARROW SERVICE")

* **Duplicate handling**: Groups duplicate names within each file before cross-file matching
* **Performance optimized**: Uses signature-based indexing for fast matching on large datasets
* **Automatic file splitting**: Splits large outputs into manageable files

## 📂 Project Structure

```
├── name_matcher.py          # Main program entry point
├── name_utils.py           # Name processing utilities
├── matching_engine.py      # Core matching logic
├── file_splitter.py        # Output file management
├── constants.py            # Ignore words and geographic terms
├── test_matching.py        # Test script for matching logic
└── README.md              # This file
```

## 📥 Input Files

* `tb_customer_names.csv`: Contains column `account_name`
* `fb_customer_names.csv`: Contains column `customer`  
* `qb_customer_names.xlsx`: Excel file with "Active" sheet containing "Customer" column

## 📤 Output

* `customer_reconciliation.csv` (or multiple parts if >10,000 rows)
  - `standardized_name`: Best formatted version of the customer name
  - `tb_names`: All matching names from TB (semicolon-separated)
  - `fb_names`: All matching names from FB (semicolon-separated)
  - `qb_names`: All matching names from QB (semicolon-separated)

### Example Output

| standardized_name | tb_names | fb_names | qb_names |
|------------------|----------|----------|----------|
| A&N Towing And Transport | A N Towing And Transport; A N Towing And Transport Llc | A&N TOWING AND TRANSPORT | A&N TOWING AND TRANSPORT; A&N TOWING AND TRANSPORT LLC |
| Albertsons Companies - Shaws | Albertsons Companies - Shaws | | Albertons Companies - Shaws; ALBERTSON COMPANIES; Albertsons Companies - Shaws |

## 🚀 Usage

1. Ensure input files are in the working directory
2. Run the main script:
   ```bash
   python name_matcher.py
   ```
3. Check output file(s) in the same directory

### Testing the Matching Logic

To verify the matching algorithm works correctly:
```bash
python test_matching.py
```

## 📦 Dependencies

```bash
pip install pandas tqdm openpyxl
```

## 🔧 Configuration

### Adjusting Match Sensitivity

In `matching_engine.py`, you can adjust:
- `min_token_similarity`: Minimum similarity score for tokens (default: 0.85)
- `min_match_ratio`: Minimum ratio of matching tokens (default: 0.7)

### Customizing Ignore Words

Edit `constants.py` to modify:
- `IGNORE_WORDS`: Common business terms to ignore
- `GEO_TERMS`: Geographic terms to optionally strip

### File Splitting

In `name_matcher.py`, adjust `max_rows_per_file` (default: 10,000) to control output file sizes.

## 🎯 Matching Algorithm

The tool uses a multi-stage matching approach:

1. **Normalization**: Standardizes punctuation, spacing, and common abbreviations
2. **Tokenization**: Breaks names into meaningful words/tokens
3. **Signature Generation**: Creates multiple signatures for fuzzy matching
4. **Token Matching**: Uses similarity scoring to match tokens with minor variations
5. **Decision Logic**: Applies rules based on match quality and token overlap

## 📊 Performance

- Processes ~5,000 customers in under 30 seconds
- Memory efficient with streaming processing
- Automatic progress bars for long operations

## 🐛 Troubleshooting

If matches seem incorrect:
1. Run `test_matching.py` to verify basic logic
2. Check if names need to be added to `IGNORE_WORDS`
3. Adjust similarity thresholds if too strict/loose
4. Review the normalized output in debug mode

## 📝 License

This tool is provided as-is for internal use.
