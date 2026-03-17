# 🕌 Masjid Finance Dashboard

> A serverless AWS pipeline that extracts mosque and surau bank statements (PDF/CSV), processes transactions, and visualises income, expenditure, and balance trends on an interactive dashboard.

Built for: **AWS Hackathon 2026**
Status: 🚧 In Development

---

## 📌 Problem Statement

Most mosques and suraus in Malaysia manage their finances manually — printing bank statements, calculating totals in spreadsheets, and presenting summaries verbally. There is no easy way for committees or the public to view a transparent, real-time financial summary.

This project solves that by letting any surau upload their bank statement PDF to a cloud folder, and automatically generating a clean finance dashboard.

---

## 🏗️ Architecture

```
🕌 Mosque Committee
        │
        │  Upload PDF/CSV
        ▼
┌──────────────────┐
│   Amazon S3      │  raw/bank-statements/
│   (Raw Bucket)   │
└────────┬─────────┘
         │ S3 Event Trigger
         ▼
┌──────────────────┐
│  AWS Lambda      │  ETL Function (Python)
│  + Textract      │  PDF → structured rows
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Amazon S3      │  curated/transactions/
│  (Curated)       │  year=YYYY/month=MM/
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌─────────────────┐
│  AWS Glue        │────▶│  Amazon Athena  │
│  Data Catalog    │     │  SQL Query Layer │
└──────────────────┘     └────────┬────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │   Amazon QuickSight    │
                     │   Finance Dashboard    │
                     └────────────────────────┘
```

---

## ✨ Features

- 📤 Upload bank statement PDF or CSV to S3 — processing is automatic
- 🔍 PDF parsing using `pdfplumber` (local) or AWS Textract (cloud)
- 📊 Dashboard showing:
  - Monthly inflow vs outflow
  - Running balance over time
  - Transaction breakdown by type (DuitNow QR, IBG Transfer, Cash Deposit)
  - Top donors / largest transactions
- 🔔 SNS notification when a new statement is processed
- 💰 Estimated cost: under USD 20/month for up to 5 surau

---

## 🛠️ Tech Stack

| Layer | Service |
|---|---|
| Storage | Amazon S3 |
| Extraction | AWS Lambda + pdfplumber / Textract |
| Catalog | AWS Glue Data Catalog |
| Query | Amazon Athena |
| Dashboard | Amazon QuickSight |
| Notification | Amazon SNS |
| IaC *(planned)* | Terraform |

---

## 🚀 Getting Started

### Prerequisites

```bash
pip install pdfplumber pandas boto3
```

### Run locally

```bash
# Clone the repo
git clone https://github.com/your-username/masjid-finance-dashboard.git
cd masjid-finance-dashboard

# Extract a bank statement PDF to CSV
python3 extract.py
```

Output: `surau_transactions.csv` — ready to upload to S3 or connect to QuickSight.

### File naming convention (S3)

```
raw/bank-statements/{surau-id}/{YYYY-MM}_statement.pdf

Example:
raw/bank-statements/surau-raudhatul-salam/2026-02_statement.pdf
```

---

## 📁 Project Structure

```
masjid-finance-dashboard/
│
├── extract.py              # Local PDF → CSV extractor
├── lambda_handler.py       # AWS Lambda ETL function
├── requirements.txt        # Python dependencies
├── sample/
│   └── sample_statement.pdf
├── output/
│   └── surau_transactions.csv
├── dashboard/
│   └── quicksight_setup.md # QuickSight setup guide
└── README.md
```

---

## 📊 Dashboard Preview

> *(Screenshot coming soon)*

Key visuals:
- **Total Inflow / Outflow / Balance** — KPI cards
- **Daily Transaction Timeline** — line chart
- **Transaction Type Breakdown** — pie chart (DuitNow QR, IBG, Cash)
- **Transaction Table** — filterable by date and amount

---

## 💡 Supported Banks

| Bank | Format | Status |
|---|---|---|
| Bank Islam | PDF (text-based) | ✅ Supported |
| Maybank | CSV export | 🔄 Planned |
| CIMB | CSV export | 🔄 Planned |

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first.

---

## 📄 License

MIT License — free to use for non-profit and community organisations.

---

## 👤 Author

**Afiq Kurshid**  
Cloud Security Architect | AWS | Hackathon 2026  
