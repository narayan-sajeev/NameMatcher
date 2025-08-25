# Customer Name Matching & Reconciliation

This project provides a **data reconciliation pipeline** for matching customer records across multiple business systems (**Towbook**, **Fullbay**, and **QuickBooks**).
It standardizes, cleans, and matches customer names using a mix of **fuzzy string similarity** and **rule-based filters**, producing a unified view of customer records.

---

## 📂 Project Structure

```
.
├── customer_reconciliation.csv   # Final reconciled output across Towbook, Fullbay, QuickBooks
├── tb_customer_names.csv         # Customer names from Towbook
├── fb_customer_names.csv         # Customer names from Fullbay
├── qb_customer_names.xlsx        # Customer data from QuickBooks (names, contacts, balances)
│
├── name_utils.py                 # Utilities for name cleaning & normalization
├── constants.py                  # Stopwords, regex, thresholds, config values
├── matching_engine.py            # Core fuzzy + rule-based matching engine
├── name_matcher.py               # Driver script that runs the full pipeline
├── file_splitter.py              # Splits large input files into smaller chunks
├── test_matching.py              # Unit tests for matching and normalization
```

---

## 🔑 Key Features

* **Normalization**: Cleans and standardizes business names (removes punctuation, suffixes like LLC/Inc, handles acronyms).
* **Rule-Based Matching**: Blocks false matches (e.g., differing websites).
* **Fuzzy Matching**: Uses similarity scores to find near-duplicates across datasets.
* **Multi-System Reconciliation**: Aligns **Towbook (TB)**, **Fullbay (FB)**, and **QuickBooks (QB)** records into one consolidated view.
* **Scalability**: File splitting to handle large customer lists without memory issues.
* **Testing**: Includes test harness for validating normalization and matching logic.

---

## ⚙️ How It Works

1. **Load Input Data**

   * Towbook names (`tb_customer_names.csv`)
   * Fullbay names (`fb_customer_names.csv`)
   * QuickBooks exports (`qb_customer_names.xlsx`)

2. **Preprocess & Normalize**

   * `name_utils.py` cleans names (case, punctuation, suffixes).
   * `constants.py` applies regex rules and stopword removal.

3. **Match Records**

   * `matching_engine.py` applies fuzzy similarity + rules.
   * Produces confidence scores for each candidate match.

4. **Reconcile Customers**

   * `name_matcher.py` orchestrates the pipeline.
   * Writes unified matches to `customer_reconciliation.csv`.

5. **Validate**

   * `test_matching.py` ensures correctness and consistency.

---

## 🚀 Usage

### Run the Full Pipeline

```bash
python name_matcher.py
```

### Run Tests

```bash
python test_matching.py
```

---

## 📊 Output

The output file `customer_reconciliation.csv` includes:

| standardized\_name             | tb\_names (Towbook)            | fb\_names (Fullbay)          | qb\_names (QuickBooks)                  |
| ------------------------------ | ------------------------------ | ---------------------------- | --------------------------------------- |
| \*cash/private Retail Customer | \*Cash/Private Retail Customer | NaN                          | NaN                                     |
| 1 Source Solutions Logistics   | NaN                            | 1 Source Solutions Logistics | 1 Source Solutions Logistics; wrecker 1 |
| 116 Industries                 | NaN                            | 116 INDUSTRIES               | 116 INDUSTRIES                          |

---

## 🛠️ Tech Stack

* **Python 3.x**
* **Pandas** (CSV/XLSX handling)
* **FuzzyWuzzy / RapidFuzz** (fuzzy string matching)
* **Regex** (cleaning & normalization)

---

## 📌 Notes

* QuickBooks export should be in `.xlsx` format.
* Towbook and Fullbay inputs should be `.csv` with customer names.
* Thresholds and stopword lists can be customized in `constants.py`.