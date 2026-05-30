# Power BI Dashboard Guide
## Smart Retail Assistant – Analytics Dashboard
### Left Shift Program 2026 – Data & AI (T5)

---

## 1. Overview

The Power BI dashboard connects to the Smart Retail Assistant's SQLite/Azure SQL database and the curated Parquet files to visualise:

- Key business metrics (revenue, transactions, growth)
- ML model outputs (demand forecasts, anomaly alerts)
- Agent-driven insights
- Sales trends by product, category, store, and time

---

## 2. Data Sources

### 2.1 Direct Database Connection (Azure SQL / SQLite)

Connect Power BI to the database using the following tables:

| Table | Use |
|---|---|
| `sales_records` | Revenue, transactions, product/category/store breakdowns |
| `forecast_results` | Predicted demand vs actual |
| `anomaly_alerts` | Anomaly count, severity, product distribution |
| `agent_conversations` | Agent usage analytics |

**Connection string (Azure SQL):**
```
Server=your-server.database.windows.net
Database=smart-retail-db
Authentication=SQL Server Authentication
```

**Connection string (local SQLite via ODBC):**
Use the SQLite ODBC driver or export to CSV/Parquet first.

---

### 2.2 Parquet File Connection

Connect to the curated Parquet file for richer feature data:
- `data/curated/sales_curated.parquet`

In Power BI Desktop: **Get Data → Parquet → Browse to file**

---

## 3. Dashboard Pages

### Page 1 – Executive Summary

**Visuals:**

| Visual | Type | Data |
|---|---|---|
| Total Revenue (30d) | KPI Card | SUM(total_revenue) WHERE sale_date >= TODAY()-30 |
| Total Transactions (30d) | KPI Card | COUNT(id) WHERE sale_date >= TODAY()-30 |
| Revenue Growth % | KPI Card | (Current 30d / Previous 30d - 1) × 100 |
| Anomaly Alerts (7d) | KPI Card | COUNT(anomaly_alerts) WHERE is_anomaly=TRUE, last 7d |
| Revenue by Category | Donut Chart | SUM(total_revenue) GROUP BY category |
| Daily Revenue Trend | Line Chart | SUM(total_revenue) GROUP BY sale_date (last 30d) |
| Top 10 Products | Bar Chart | SUM(total_revenue) GROUP BY product_name, TOP 10 |
| Revenue by Store | Map / Bar | SUM(total_revenue) GROUP BY store_id |

---

### Page 2 – Demand Forecasting

**Visuals:**

| Visual | Type | Data |
|---|---|---|
| Actual vs Forecast | Line Chart | actual quantity + predicted_demand by date |
| Forecast Confidence Band | Area Chart | confidence_lower to confidence_upper |
| Product Selector | Slicer | product_id |
| Forecast Accuracy (MAE) | KPI Card | AVG(ABS(actual - predicted)) |
| 7-Day Forecast Table | Table | forecast_results for next 7 days |
| Demand Heatmap | Matrix | quantity by product × day_of_week |

**DAX Measures:**
```dax
Forecast MAE =
AVERAGEX(
    FILTER(forecast_results, forecast_results[forecast_date] <= TODAY()),
    ABS(
        RELATED(sales_records[quantity]) - forecast_results[predicted_demand]
    )
)

Revenue Growth % =
VAR CurrentPeriod = CALCULATE(SUM(sales_records[total_revenue]),
    DATESINPERIOD(sales_records[sale_date], TODAY(), -30, DAY))
VAR PreviousPeriod = CALCULATE(SUM(sales_records[total_revenue]),
    DATESINPERIOD(sales_records[sale_date], TODAY()-30, -30, DAY))
RETURN DIVIDE(CurrentPeriod - PreviousPeriod, PreviousPeriod, 0) * 100
```

---

### Page 3 – Anomaly Detection

**Visuals:**

| Visual | Type | Data |
|---|---|---|
| Anomaly Timeline | Scatter Chart | anomaly_score by sale_date, coloured by is_anomaly |
| Anomaly Count by Product | Bar Chart | COUNT(anomaly_alerts) WHERE is_anomaly=TRUE GROUP BY product_id |
| Anomaly Rate % | KPI Card | COUNT(anomalies) / COUNT(total) × 100 |
| Recent Alerts Table | Table | Latest 20 anomaly_alerts WHERE is_anomaly=TRUE |
| Anomaly Score Distribution | Histogram | anomaly_score distribution |
| Anomaly by Store | Bar Chart | COUNT(anomalies) GROUP BY store_id |

**Conditional Formatting:**
- Anomaly score < -2.0 → Red (High severity)
- Anomaly score -2.0 to -1.5 → Orange (Medium)
- Anomaly score > -1.5 → Yellow (Low)

---

### Page 4 – Product & Store Analytics

**Visuals:**

| Visual | Type | Data |
|---|---|---|
| Revenue by Product (Treemap) | Treemap | SUM(total_revenue) by product_name |
| Units Sold by Category | Stacked Bar | SUM(quantity) by category, by month |
| Store Performance | Table | revenue, transactions, avg_order_value by store |
| Weekend vs Weekday Sales | Clustered Bar | SUM(quantity) by is_weekend |
| Promotion Impact | Line Chart | revenue on promo days vs non-promo days |
| Category Growth | Line Chart | monthly revenue by category |

---

### Page 5 – Agent Insights

**Visuals:**

| Visual | Type | Data |
|---|---|---|
| Agent Usage | Donut Chart | COUNT(conversations) by agent_type |
| Query Volume Over Time | Line Chart | COUNT(conversations) by date |
| Top User Questions | Word Cloud | user_message text analysis |
| Response Time | KPI Card | AVG(response_time_ms) |
| Session Count | KPI Card | COUNT(DISTINCT session_id) |

---

## 4. Filters & Slicers

Add these slicers to all pages:

- **Date Range** — sale_date between [start] and [end]
- **Product** — product_id multi-select
- **Category** — category multi-select
- **Store** — store_id multi-select

---

## 5. Refresh Schedule

| Environment | Refresh Method | Frequency |
|---|---|---|
| Development | Manual refresh | On demand |
| Production (Azure SQL) | Scheduled refresh via Power BI Service | Every 4 hours |
| Production (Parquet) | Azure Data Factory trigger → Power BI API | After pipeline run |

---

## 6. Publishing

1. Open Power BI Desktop → **File → Publish → Publish to Power BI**
2. Select your workspace (e.g., `Smart Retail Assistant`)
3. In Power BI Service: **Settings → Scheduled Refresh → Configure**
4. Share the report: **Share → Enter email addresses**
5. Embed in the frontend (optional): **File → Embed Report → Website or portal**

---

## 7. Export for Submission

To export the dashboard as a PDF for submission:
1. Power BI Desktop → **File → Export → Export to PDF**
2. Select all pages
3. Save as `Smart_Retail_Dashboard.pdf`

---

## 8. Sample DAX Measures Reference

```dax
-- Total Revenue Last 30 Days
Revenue 30D =
CALCULATE(
    SUM(sales_records[total_revenue]),
    DATESINPERIOD(sales_records[sale_date], TODAY(), -30, DAY)
)

-- Anomaly Rate
Anomaly Rate % =
DIVIDE(
    COUNTROWS(FILTER(anomaly_alerts, anomaly_alerts[is_anomaly] = TRUE())),
    COUNTROWS(anomaly_alerts),
    0
) * 100

-- Week-over-Week Growth
WoW Growth =
VAR ThisWeek = CALCULATE(SUM(sales_records[total_revenue]),
    DATESINPERIOD(sales_records[sale_date], TODAY(), -7, DAY))
VAR LastWeek = CALCULATE(SUM(sales_records[total_revenue]),
    DATESINPERIOD(sales_records[sale_date], TODAY()-7, -7, DAY))
RETURN DIVIDE(ThisWeek - LastWeek, LastWeek, 0) * 100

-- Average Order Value
Avg Order Value =
DIVIDE(
    SUM(sales_records[total_revenue]),
    COUNTROWS(sales_records),
    0
)
```
