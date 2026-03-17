# 🕌 Masjid Finance Dashboard

> A serverless AWS SaaS platform that enables mosques and suraus to upload bank statements, auto-process transactions, and visualise finance data on an interactive dashboard — with a multi-tenant web portal for self-service access.

Built for: **AWS Hackathon 2026**
Status: 🚧 In Development

---

## 📌 Problem Statement

Most mosques and suraus in Malaysia manage their finances manually — printing bank statements, calculating totals in spreadsheets, and presenting summaries verbally. There is no easy way for committees or the public to view a transparent, real-time financial summary.

This project solves that by providing a **SaaS portal** where any surau admin can log in, upload their bank statement PDF, and automatically get a clean finance dashboard — with full data isolation between mosques.

---

## 🏗️ Architecture

```
🕌 Mosque Admin (Browser)
        │
        │  Login + Upload PDF
        ▼
┌─────────────────────┐
│   Web Portal        │  Static site (S3 + CloudFront)
│   React / HTML      │  Auth via Amazon Cognito
└────────┬────────────┘
         │ Upload via Pre-signed S3 URL
         ▼
┌─────────────────────┐
│  S3 Raw Bucket      │  raw/{mosque_id}/YYYY-MM_statement.pdf
└────────┬────────────┘
         │ S3 Event Trigger
         ▼
┌─────────────────────┐
│  AWS Lambda         │  ETL Function (Python)
│  + pdfplumber       │  PDF → structured CSV rows
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  S3 Curated Bucket  │  curated/{mosque_id}/transactions.csv
└────────┬────────────┘
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
                     │ (Embedded per mosque)  │
                     └────────────────────────┘
```

---

## ✨ Features

- 🔐 Multi-tenant login — each mosque admin has their own account via Amazon Cognito
- 📤 Self-service upload — mosque admin uploads PDF via web portal (no AWS console access needed)
- 🔍 Auto PDF parsing using `pdfplumber` (local) or AWS Textract (cloud)
- 📊 Per-mosque dashboard showing:
  - Monthly inflow vs outflow
  - Running balance over time
  - Daily donation trend (bar chart)
  - Donations by channel (DuitNow QR, IBG Transfer, Cash Deposit)
  - Top donors / largest transactions
- 🔒 Data isolation — each mosque only sees their own data (QuickSight Row-Level Security)
- 🔔 SNS notification when a new statement is processed
- 💰 Estimated cost: under USD 20/month for up to 5 surau

---

## 🛠️ Tech Stack

| Layer | Service |
|---|---|
| Auth | Amazon Cognito |
| Web Portal | S3 + CloudFront (static HTML/JS) |
| File Upload | S3 Pre-signed URL via API Gateway + Lambda |
| Storage | Amazon S3 (Raw + Curated buckets) |
| Extraction | AWS Lambda + pdfplumber / Textract |
| Catalog | AWS Glue Data Catalog |
| Query | Amazon Athena |
| Dashboard | Amazon QuickSight (Embedded) |
| Notification | Amazon SNS |
| IaC *(planned)* | Terraform |

---

## 🌐 SaaS Portal

The web portal allows mosque admins to:
1. **Login** with their Cognito credentials
2. **Upload** their monthly bank statement PDF
3. **View** their auto-generated QuickSight dashboard — embedded directly in the portal

### Portal Flow

```
Admin logs in (Cognito)
        │
        ▼
Portal requests pre-signed S3 URL (API Gateway → Lambda)
        │
        ▼
Admin uploads PDF directly to S3 (raw/{mosque_id}/)
        │
        ▼
S3 trigger fires Lambda ETL → CSV written to curated/{mosque_id}/
        │
        ▼
QuickSight refreshes → Dashboard live within ~2 minutes
```

### Key Portal Code

**Frontend — Upload via Pre-signed URL**
```javascript
// Get pre-signed URL from API Gateway
fetch(`${CONFIG.apiEndpoint}/upload-url`, {
  method: 'POST',
  headers: { 'Authorization': token },
  body: JSON.stringify({ mosque_id, filename })
})
.then(r => r.json())
.then(data => fetch(data.upload_url, {
  method: 'PUT',
  body: file,
  headers: { 'Content-Type': 'application/pdf' }
}));
```

**Backend Lambda — Generate Pre-signed URL**
```python
import boto3, json

s3 = boto3.client('s3', region_name='ap-southeast-1')

def lambda_handler(event, context):
    body      = json.loads(event['body'])
    mosque_id = body['mosque_id']
    filename  = body['filename']
    key       = f"raw/{mosque_id}/{filename}"

    url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket':      'masjid-raw-ACCOUNT_ID-ap-southeast-1',
            'Key':         key,
            'ContentType': 'application/pdf'
        },
        ExpiresIn=600  # 10 minutes
    )

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'upload_url': url})
    }
```

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
raw/{mosque_id}/{YYYY-MM}_statement.pdf

Example:
raw/surau-raudhatul-salam/2026-02_statement.pdf
```

---

## 📁 Project Structure

```
masjid-finance-dashboard/
│
├── extract.py              # Local PDF → CSV extractor
├── lambda_handler.py       # AWS Lambda ETL function
├── lambda_presigned_url.py # Lambda to generate S3 pre-signed upload URL
├── requirements.txt        # Python dependencies
├── portal/
│   └── index.html          # SaaS web portal (upload + dashboard)
├── sample/
│   └── sample_statement.pdf
├── output/
│   └── surau_transactions.csv
├── dashboard/
│   └── quicksight_setup.md # QuickSight setup guide
└── README.md
```

---

## 📊 Dashboard Visuals

Key visuals per mosque:
- **Total Donations (RM)** — KPI card (Sum of credit_rm)
- **Current Balance (RM)** — KPI card (Max of balance_rm)
- **Daily Donations Trend** — bar chart (credit_rm Sum by day)
- **Donations by Channel** — pie chart (txn_type breakdown)
- **Running Balance** — line chart (balance over time)
- **Top 10 Donors** — horizontal bar chart (sender_name by credit_rm)

---

## 🔐 Multi-Tenant Data Isolation

Each mosque's data is isolated using:
- **S3 folder structure**: `raw/{mosque_id}/` and `curated/{mosque_id}/`
- **Cognito User Pool**: each admin belongs to a group matching their `mosque_id`
- **QuickSight Row-Level Security**: dataset rules filter rows by `mosque_id` per user

---

## 🗺️ Build Roadmap

| Phase | Task | Status |
|---|---|---|
| 1 | PDF extraction + CSV output (local) | ✅ Done |
| 2 | S3 upload + Lambda ETL trigger | ✅ Done |
| 3 | Glue Catalog + Athena query | ✅ Done |
| 4 | QuickSight dashboard | ✅ Done |
| 5 | Cognito auth + web portal | 🚧 In Progress |
| 6 | API Gateway + pre-signed URL Lambda | 🚧 In Progress |
| 7 | QuickSight embedding in portal | 🔄 Planned |
| 8 | Row-Level Security (multi-mosque) | 🔄 Planned |
| 9 | Terraform IaC | 🔄 Planned |

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
