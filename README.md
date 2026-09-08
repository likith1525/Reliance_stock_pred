# Reliance Industries Stock Analysis & Price Forecasting 📈

An end-to-end time-series analysis and price trend exploration of stock price data using Python in Google Colab. This project processes historical market data, identifies technical trends via moving averages, examines daily volatility spikes, and evaluates correlation across key market metrics.

---

## 📌 Project Overview
* **Dataset Scope:** 753 trading days (October 19, 2020 – October 16, 2023)
* **Data Fields:** Date, Open, High, Low, Close, Adjusted Close, Volume
* **Environment:** Google Colab

---

## 🛠️ Tech Stack
* **Language:** Python
* **Data Processing:** Pandas, NumPy
* **Data Visualization:** Matplotlib, Seaborn
* **Data Source Format:** Excel (`Company stock prices.xlsx`)

---

## 📊 Key Findings & Technical Analysis

### 1. Feature Correlations
* Strong positive correlation (**1.0**) exists among `Open`, `High`, `Low`, and `Close` prices.
* Volume exhibits a moderate inverse correlation (**~ -0.38 to -0.40**) relative to price points.

### 2. Trend Identification (Moving Averages)
* Smooths short-term price fluctuations using **20-Day MA** and **50-Day MA**.
* Highlights momentum shifts and cross-over points across the multi-year dataset.

### 3. Outlier Analysis & Extreme Volatility
* **Biggest Single-Day Drop:** `2022-04-20` | **Daily Return:** `-35.11%`
* **Biggest Single-Day Gain:** `2021-01-20` | **Close Price:** `586.34`

---

## 📈 Visualizations Included in Repository
* **Correlation Matrix Heatmap:** Heatmap of price columns against daily trading volume.
* **Moving Average Overlay Plot:** Time-series line plot mapping `Close Price`, `20-Day MA`, and `50-Day MA`.

---

## 🚀 How to Run

1. Clone this repository:
   ```bash
   git clone [https://github.com/likith1525/Reliance_stock_pred.git]
   
2.Download all the required files and save them in a single folder & run them in the command prompt and enjoy your website.
