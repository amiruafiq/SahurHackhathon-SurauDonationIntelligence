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
│   HTML / JS         │  Auth via Amazon Cognito
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
  - Total donations received (RM)
  - Current balance (RM)
  - Daily donation trend (bar chart)
  - Donations by channel (DuitNow QR, IBG Transfer, Cash Deposit)
  - Running balance over time
  - Top 10 donors
- 🔒 Data isolation — each mosque only sees their own data (QuickSight Row-Level Security)
- 🔔 SNS notification when a new statement is processed

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

## 🌐 SaaS Web Portal (`portal/index.html`)

The web portal is a single HTML file — no framework needed. Host it on S3 + CloudFront.

### Login Screen
- Email + password form
- Demo credentials pre-filled for easy testing
- Enter key support
- Error feedback with colour-coded status badges

### Dashboard Screen (after login)
- Navbar with mosque name + Sign Out button
- **KPI cards** — Current Balance & Feb 2026 Donations
- **Drag & drop upload zone** — accepts PDF/CSV
- **Progress bar** with 3-stage feedback:
  `Requesting URL → Uploading to S3 → Lambda ETL Running → ✅ Done`
- Statement month selector
- **View Dashboard** button → opens QuickSight embedded dashboard
- **Upload history table** with ✅ Done / ⏳ Processing status badges

### To go live — replace 3 things in `<script>`:

| Code Block | Replace With |
|---|---|
| `DEMO_USERS` block | Cognito SDK `authenticateUser()` call |
| `setTimeout` upload demo | Real `fetch()` to API Gateway pre-signed URL endpoint |
| `viewDashboard()` demo | Real `fetch()` to get QuickSight embedded URL |

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

### Key Backend Lambda — Generate Pre-signed URL

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

## 💰 AWS Cost Estimate

Estimated monthly cost to run this platform for **up to 10 mosques**:

| Service | Usage Assumption | Est. Monthly Cost (USD) |
|---|---|---|
| S3 (Raw + Curated) | ~500 MB storage + uploads | ~$0.50 |
| Lambda | ~120 invocations/month (10 mosques × 12 statements/yr) | ~$0.00 (free tier) |
| Athena | ~50 queries/month × avg 1 MB scanned | ~$0.00 (free tier) |
| AWS Glue Catalog | < 1M objects | ~$0.00 (free tier) |
| Amazon Cognito | < 10,000 MAU | **FREE** (free tier) |
| CloudFront | Static portal hosting, < 1 GB/month | ~$0.10 |
| QuickSight Author | 1 author (dashboard builder) | ~$24.00 |
| QuickSight Reader | Up to 10 mosque admins × $3/user | ~$30.00 |
| SNS Notifications | < 1,000 emails/month | ~$0.00 (free tier) |
| **Total** | | **~$55/month** |

> 💡 QuickSight dominates the cost. For a hackathon demo, use 1 Author + Reader sessions to minimize cost.
> With capacity pricing (500 sessions/month), cost is ~$250/month — suitable when scaling to 50+ mosques.

---

## 📈 SaaS Pricing Model (How Much to Charge)

If commercialised as a SaaS product for Malaysian mosques/suraus:

| Tier | Target | Price (MYR/month) | Features |
|---|---|---|---|
| 🆓 Free | Small surau | RM 0 | 1 statement/month, basic dashboard |
| 🥈 Basic | Active surau | RM 49/month | 3 statements/month, all charts, email report |
| 🥇 Pro | Mosque (JAWI-registered) | RM 99/month | Unlimited uploads, multi-branch, custom branding |
| 🏢 Enterprise | JAWI / NGO (bulk) | RM 299/month | All mosques in 1 district, API access, audit log |

### Revenue Potential

| Scenario | Mosques | Price | Monthly Revenue |
|---|---|---|---|
| Conservative | 20 mosques × Basic | RM 49 | **RM 980/month** |
| Moderate | 50 mosques × Basic | RM 49 | **RM 2,450/month** |
| Growth | 100 mosques × Pro | RM 99 | **RM 9,900/month** |
| Scale | 500 mosques × Basic | RM 49 | **RM 24,500/month** |

> 🕌 There are **~6,000 mosques** and **~30,000 suraus** in Malaysia — addressable market is large.
> Even 1% penetration (300 mosques at RM 49/month) = **RM 14,700/month recurring revenue**.

---

## 🗺️ Build Roadmap

| Phase | Task | Status |
|---|---|---|
| 1 | PDF extraction + CSV output (local) | ✅ Done |
| 2 | S3 upload + Lambda ETL trigger | ✅ Done |
| 3 | Glue Catalog + Athena query | ✅ Done |
| 4 | QuickSight dashboard | ✅ Done |
| 5 | Web portal HTML (demo mode) | ✅ Done |
| 6 | Cognito auth + API Gateway | 🚧 In Progress |
| 7 | Pre-signed URL Lambda | 🚧 In Progress |
| 8 | QuickSight embedding in portal | 🔄 Planned |
| 9 | Row-Level Security (multi-mosque) | 🔄 Planned |
| 10 | Terraform IaC | 🔄 Planned |

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
├── extract.py                  # Local PDF → CSV extractor
├── lambda_handler.py           # AWS Lambda ETL function
├── lambda_presigned_url.py     # Lambda to generate S3 pre-signed upload URL
├── requirements.txt            # Python dependencies
├── portal/
│   └── index.html              # SaaS web portal (login + upload + dashboard)
├── sample/
│   └── sample_statement.pdf
├── output/
│   └── surau_transactions.csv
├── dashboard/
│   └── quicksight_setup.md     # QuickSight setup guide
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
