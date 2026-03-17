import re

def parse_description(desc):
    """
    Input:  "9831 INW DuitNow QR POS FERHAD BIN ABDUL RAHMAN 08179283 CASAOffUs XRPP398"
    Output: txn_code, txn_type, sender_name, ref_code
    """
    # Transaction code (4-digit at start)
    txn_code_match = re.match(r"^(\d{4})\s+", desc)
    txn_code = txn_code_match.group(1) if txn_code_match else ""

    # Transaction type
    if "DuitNow QR POS" in desc:
        txn_type = "DuitNow QR"
    elif "DuitNow Transfer" in desc:
        txn_type = "DuitNow Transfer"
    elif "IBG TRANSFER" in desc:
        txn_type = "IBG Transfer"
    elif "CA CASH DEPOSIT" in desc:
        txn_type = "Cash Deposit"
    elif "MB SA TRF" in desc:
        txn_type = "Mobile Transfer"
    else:
        txn_type = "Other"

    # Reference code (XRPP*** or EFO***)
    ref_match = re.search(r"(XRPP\w+|EFO\w+)", desc)
    ref_code = ref_match.group(1) if ref_match else ""

    # Sender name — between txn type keyword and the number/ref
    name_patterns = [
        r"DuitNow QR POS\s+(.+?)\s+\d{8}",
        r"DuitNow Transfer\s+(.+?)\s+\w+\s+\1",  # name repeated
        r"DuitNow Transfer\s+(.+?)\s+(?:Infaq|Sedekah|Sumbangan|Fund Transfer)",
        r"IBG TRANSFER TO CA\s+(.+?)\s+(?:Sumbangan|Sedekah|\d)",
    ]
    sender_name = ""
    for pattern in name_patterns:
        m = re.search(pattern, desc, re.IGNORECASE)
        if m:
            sender_name = m.group(1).strip()
            break

    # Category keyword
    category_keywords = {
        "Infaq": "Infaq", "Sedekah": "Sedekah", "Sumbangan": "Sumbangan",
        "Fund Transfer": "Sumbangan", "QR Payment": "QR Payment",
        "CASH DEPOSIT": "Cash Deposit"
    }
    category = "Donation"
    for keyword, label in category_keywords.items():
        if keyword.lower() in desc.lower():
            category = label
            break

    return txn_code, txn_type, sender_name, ref_code, category
