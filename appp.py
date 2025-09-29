# Import necessary libraries
import streamlit as st
import pytesseract
import cv2
import yfinance as yf
import re
import numpy as np
import pandas as pd
from PIL import Image
import plotly.express as px

# Configure the Streamlit page
st.set_page_config(page_title="📈 Stock Prediction Dashboard", layout="wide")

# Display the app title and instructions
st.title("📈 Stock Portfolio Analyzer")
st.write("Upload a screenshot of your stock portfolio. This app will extract ticker symbols and prices, match them with real-world data, and predict stock performance with buy/sell recommendations.")

# Upload screenshot image
uploaded_file = st.file_uploader("Upload a screenshot (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Load and display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Screenshot", use_container_width=True)

    # Convert image to grayscale for better OCR accuracy
    image_np = np.array(image)
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

    # Extract text from image using Tesseract OCR
    text = pytesseract.image_to_string(gray)

    # Show the extracted raw text
    st.subheader("📝 Extracted Text")
    st.text(text)

    # Use regex to find ticker symbols and prices in the text
    pattern = r'\b([A-Z]{1,5})\b[^0-9]*([\d]+\.?\d{0,2})'
    matches = re.findall(pattern, text)

    # Store tickers and prices in a dictionary, grouping duplicates
    portfolio_data = {}
    for ticker, price in matches:
        price = float(price)
        if ticker in portfolio_data:
            portfolio_data[ticker].append(price)
        else:
            portfolio_data[ticker] = [price]

    # Prepare a list to hold prediction results
    result_rows = []

    # Analyze each ticker
    for ticker, prices in portfolio_data.items():
        screenshot_price = sum(prices) / len(prices)  # Average price from screenshot
        try:
            # Fetch 6-month historical data from Yahoo Finance
            data = yf.Ticker(ticker).history(period="6mo")
            if data.empty:
                continue

            # Get start and current prices
            start_price = data['Close'].iloc[0]
            current_price = data['Close'].iloc[-1]

            # Calculate percentage change
            change_percent = ((current_price - start_price) / start_price) * 100

            # Determine recommendation based on change
            if change_percent > 10:
                recommendation = "Buy"
            elif change_percent < -10:
                recommendation = "Sell"
            else:
                recommendation = "Hold"

            # Add result to list
            result_rows.append({
                "Ticker": ticker,
                "Screenshot Price": round(screenshot_price, 2),
                "Start Price": round(start_price, 2),
                "Current Price": round(current_price, 2),
                "Change (%)": round(change_percent, 2),
                "Recommendation": recommendation,
                "Confidence": round(abs(change_percent), 1)
            })
        except Exception:
            continue

    # Display results in an interactive chart
    if result_rows:
        result_df = pd.DataFrame(result_rows)

        st.subheader("📊 Interactive Prediction Map")
        fig = px.scatter(
            result_df,
            x="Ticker",
            y="Change (%)",
            color="Recommendation",
            size="Confidence",
            hover_data=["Screenshot Price", "Start Price", "Current Price", "Confidence"],
            title="📈 Stock Prediction Dashboard"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid stock data found in the screenshot.")
