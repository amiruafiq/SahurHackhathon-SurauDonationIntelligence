"""
Bank Statement PDF → CSV Extractor
For: Surau/Mosque Finance Dashboard Hackathon
Tested on: Bank Islam statement (Surau Raudhatul Salam)
"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────
PDF_PATH       = "statementFeb_unlocked.pdf"
OUTPUT_CSV     = "surau_transactions.csv"
ACCOUNT_NUMBER = "05012010104558"
SURAU_NAME     = "SURAU RAUDHATUL SALAM TAMAN IRINGAN BAYU"
BRANCH         = "SEREMBAN"
STATEMENT_MONTH = "2026-02"
OPENING_BALANCE = 146938.59   # ← update each month from BAL B/F on page 1
# ────────────────────────────────────────────────────────

DATE_RE   = re.compile(r"^\d{2}/\d{2}/\d{2}$")
AMOUNT_RE = re.compile(r"^\d{1,3}(?:,\d{3})*\.\d{2}$")

SKIP_PATTERNS = [
    re.compile(r"SURAU RAUDHATUL|U/P:|PRECINT|70300|TARIKH PENYATA|"
               r"STATEMENT DATE|HALAMAN|NOMBOR AKAUN|ACCOUNT NUMBER|"
               r"CAWANGAN|PENYATA AKAUN|AKAUN SEMASA|Dilindungi|"
               r"Protected by PIDM|\bTARIKH\b|\bDATE\b|\bKETERANGAN\b|"
               r"\bDESCRIPTION\b|\bDEBIT\b|\bKREDIT\b|\bCREDIT\b|"
               r"\bBAKI\b|\bBALANCE\b|\(RM\)"),
    re.compile(r"^\d+ of \d+$"),
    re.compile(r"^:\s"),
]

HEADER_BLEED_RE = re.compile(
    r"\s*(BRANCH|ACCOUNT STATEMENT|KETERANGAN|DEBIT|DESCRIPTION|"
    r"CREDIT|BALANCE|KREDIT|BAKI|\(RM\))\s*", re.IGNORECASE
)

def should_skip(text):
    return any(p.search(text) for p in SKIP_PATTERNS)

def parse_amount(s):
    try:
        return float(s.replace(",", ""))
    except:
        return None

def group_by_row(words, tol=3):
    rows = {}
    for w in words:
        y = round(w["top"] / tol) * tol
        rows.setdefault(y, []).append(w)
    return sorted(rows.items())

def extract_transactions(pdf_path):
    transactions = []
    prev_balance = OPENING_BALANCE
    all_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        W = pdf.pages[0].width  # ~595 for A4

        for page in pdf.pages:
            words = page.extract_words()
            if not words:
                continue

            for top, row_words in group_by_row(words):
                date_words   = [w["text"] for w in row_words if w["x0"] <= W * 0.13]
                desc_words   = [w["text"] for w in row_words if W * 0.13 < w["x0"] <= W * 0.65]
                debit_words  = [w["text"] for w in row_words if W * 0.65 < w["x0"] <= W * 0.78]
                credit_words = [w["text"] for w in row_words if W * 0.78 < w["x0"] <= W * 0.89]
                bal_words    = [w["text"] for w in row_words if w["x0"] > W * 0.89]

                date_str   = " ".join(date_words).strip()
                desc_str   = " ".join(desc_words).strip()
                debit_str  = " ".join(debit_words).strip()
                credit_str = " ".join(credit_words).strip()
                bal_str    = " ".join(bal_words).strip()

                combined = (date_str + " " + desc_str).strip()
                if not combined or should_skip(combined):
                    continue

                all_rows.append({
                    "date_str": date_str, "desc_str": desc_str,
                    "debit_str": debit_str, "credit_str": credit_str,
                    "bal_str": bal_str
                })

    # Merge multi-line transactions
    merged = []
    current = None
    for row in all_rows:
        if DATE_RE.match(row["date_str"]):
            if current:
                merged.append(current)
            current = dict(row)
        elif current:
            current["desc_str"] += " " + row["desc_str"]
            for col in ["debit_str", "credit_str", "bal_str"]:
                if not current[col] and row[col]:
                    current[col] = row[col]
    if current:
        merged.append(current)

    # Parse into records
    for row in merged:
        if not DATE_RE.match(row["date_str"]):
            continue

        # In this Bank Islam layout, credit_str contains the balance value
        balance = parse_amount(row["credit_str"]) if AMOUNT_RE.match(row["credit_str"]) else None
        if balance is None:
            continue

        diff = round(balance - prev_balance, 2)
        if diff > 0:
            direction, debit_rm, credit_rm = "CREDIT", None, diff
        elif diff < 0:
            direction, debit_rm, credit_rm = "DEBIT", abs(diff), None
        else:
            direction, debit_rm, credit_rm = "CREDIT", None, 0.0

        desc = re.sub(r"\s+", " ", HEADER_BLEED_RE.sub(" ", row["desc_str"])).strip()

        try:
            date_parsed = datetime.strptime(row["date_str"], "%d/%m/%y").strftime("%Y-%m-%d")
        except:
            date_parsed = row["date_str"]

        transactions.append({
            "date":           date_parsed,
            "description":    desc,
            "debit_rm":       debit_rm,
            "credit_rm":      credit_rm,
            "balance_rm":     balance,
            "direction":      direction,
            "account_number": ACCOUNT_NUMBER,
            "surau_name":     SURAU_NAME,
            "branch":         BRANCH,
            "statement_month": STATEMENT_MONTH
        })
        prev_balance = balance

    return pd.DataFrame(transactions)

if __name__ == "__main__":
    df = extract_transactions(PDF_PATH)
    df.to_csv(OUTPUT_CSV, index=False)

    total_credit = df[df["direction"] == "CREDIT"]["credit_rm"].sum()
    total_debit  = df[df["direction"] == "DEBIT"]["debit_rm"].sum()

    print(f"✅ Extracted {len(df)} transactions → {OUTPUT_CSV}")
    print(f"   Credits : RM {total_credit:>12,.2f}  ({df[df['direction']=='CREDIT'].shape[0]} txns)")
    print(f"   Debits  : RM {total_debit:>12,.2f}  ({df[df['direction']=='DEBIT'].shape[0]} txns)")
    print(f"   Opening : RM {OPENING_BALANCE:>12,.2f}")
    print(f"   Closing : RM {df['balance_rm'].iloc[-1]:>12,.2f}")
