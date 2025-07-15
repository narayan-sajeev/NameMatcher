# Customer Name Reconciliation

This Python tool reconciles customer name records from two different sources using rule-based name matching logic. It
standardizes formatting, strips common noise words, and compares names to identify matches and unique entries.

## 🔍 Features

* Cleans and normalizes names (removes punctuation, phone numbers, spacing issues)
* Ignores common business words (e.g. *LLC*, *Inc*, *Group*) and geographic terms
* Handles plural word variants and partial phrase containment
* Outputs a standardized name list with matched and unmatched entries

## 📂 Inputs

* `tb_customer_names.csv`: Contains a column `account_name`
* `fb_customer_names.csv`: Contains a column `customer`

## 🛠️ Output

* `customer_reconciliation.csv`: A merged list of all names with standardized formatting:

    * `standardized_name`: Cleaned, capitalized result
    * `tb_name`: Original name from TB dataset
    * `fb_name`: Original name from FB dataset

## 🚀 Usage

1. Make sure your input CSVs (`tb_customer_names.csv`, `fb_customer_names.csv`) are in the working directory.
2. Run the script:

   ```bash
   python customer_name_matcher.py
   ```
3. Check the `customer_reconciliation.csv` for results.

## 📦 Dependencies

* Python 3.7+
* pandas
* tqdm

Install with:

```bash
pip install pandas tqdm
```

## 🔧 Customization

You can adjust:

* `IGNORE_WORDS` and `GEO_TERMS` in `constants.py` to better suit your domain.
* Matching thresholds or logic in `names_match()` if your data behaves differently.
