from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from datetime import datetime
import random

load_dotenv(override=True)

MARKET_SYSTEM_PROMPT = """You are a financial market data analyst.
Use the available tools to fetch current market data and provide insights.
Always cite specific numbers and data points in your analysis.
When analyzing stocks, consider both price action and technical indicators."""

def get_stock_price(symbol: str, include_change: bool = True) -> dict:
    """Get current stock price and daily change for a given symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT')
        include_change: Whether to include daily price change (default: True)
    
    Returns:
        Dictionary containing stock price, change, and timestamp
    
    Note:
        Replace this mock implementation with calls to your internal market data API
        to fetch real-time stock prices and market data.
    """
    # Mock data - replace with your internal market data API calls
    base_prices = {"AAPL": 185.50, "GOOGL": 140.20, "MSFT": 350.75, "TSLA": 245.30}
    price = base_prices.get(symbol.upper(), 100.0)
    change = round(random.uniform(-5, 5), 2)
    
    result = {
        "symbol": symbol.upper(),
        "price": round(price + change, 2),
        "timestamp": datetime.now().isoformat()
    }
    
    if include_change:
        result.update({
            "change": change,
            "change_percent": round((change / price) * 100, 2)
        })
    
    return result

def get_market_sentiment(sector: str, timeframe: str = "daily") -> dict:
    """Get market sentiment for a specific sector.
    
    Args:
        sector: Market sector (e.g., 'technology', 'finance', 'healthcare')
        timeframe: Analysis timeframe - 'daily', 'weekly', or 'monthly' (default: 'daily')
    
    Returns:
        Dictionary containing sentiment analysis and confidence scores
    
    Note:
        Replace this mock implementation with calls to your internal sentiment analysis API
        or market intelligence system.
    """
    sentiments = ["bullish", "bearish", "neutral"]
    confidence_base = 0.7 if timeframe == "daily" else 0.85
    
    return {
        "sector": sector,
        "sentiment": random.choice(sentiments),
        "confidence": round(random.uniform(confidence_base, 0.95), 2),
        "timeframe": timeframe,
        "key_factors": ["earnings reports", "interest rates", "global events"],
        "timestamp": datetime.now().isoformat()
    }

def calculate_moving_average(symbol: str, period: int = 50) -> dict:
    """Calculate simple moving average for a stock.
    
    Args:
        symbol: Stock ticker symbol
        period: Number of days for moving average (default: 50, common: 20, 50, 200)
    
    Returns:
        Dictionary containing moving average calculations and signals
    
    Note:
        Replace this mock implementation with calls to your internal technical analysis API
        or calculation service for real moving averages and indicators.
    """
    # Mock data - replace with your internal API for technical indicators
    current_price = 185.50
    ma = round(current_price * random.uniform(0.95, 1.05), 2)
    
    return {
        "symbol": symbol.upper(),
        "period": period,
        "moving_average": ma,
        "current_price": current_price,
        "position": "above" if current_price > ma else "below",
        "signal": "bullish" if current_price > ma else "bearish",
        "timestamp": datetime.now().isoformat()
    }

# Create agent with tools
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_agent(
    model=llm,
    tools=[get_stock_price, get_market_sentiment, calculate_moving_average],
    system_prompt=MARKET_SYSTEM_PROMPT,
)

