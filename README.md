# Retail Sales Intelligence Platform

## Overview
An end-to-end retail analytics project using Python, Amazon S3, Amazon Athena, SQL, and Power BI to clean retail transaction data, analyze sales performance, investigate returns, and visualize business trends.

## Dataset
- Source: UCI Online Retail II
- Source records: 1,067,371
- Period: December 2009 – December 2011

## Technology Stack
- Python and Pandas — data profiling and cleaning
- Amazon S3 — private raw and curated data storage
- Amazon Athena and SQL — serverless querying and analytics
- Power BI — interactive business dashboards

## Data Pipeline
1. Profile the source workbook.
2. Clean and classify transaction records using Python.
3. Export curated datasets to Parquet.
4. Store raw and curated datasets in Amazon S3.
5. Query curated tables with Athena.
6. Visualize sales, products, geography, returns, and data-quality findings in Power BI.

## Data Reconciliation
| Dataset | Records |
|---|---:|
| Sales | 1,044,415 |
| Returns and cancellations | 22,951 |
| Financial adjustments | 5 |
| Total | 1,067,371 |

The curated record counts reconcile with the source record count. Duplicate records were flagged for investigation rather than automatically deleted.

## Key Analyses
- Monthly gross sales and sales volume
- Top products by gross sales
- Country-level sales performance
- Monthly returns and cancellations
- Data-quality profiling and record reconciliation

## Dashboard
Three report pages:
1. Executive Overview
2. Product & Geography
3. Returns & Data Quality

## Limitations
Gross sales are not net revenue. Missing customer IDs limit customer-level analysis, and return/cancellation flags may overlap.

## Security
AWS credentials and raw dataset files are excluded from version control.

## Author
BSc CSIT student focused on data analytics and business intelligence.