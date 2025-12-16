from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from datetime import datetime

load_dotenv(override=True)

MARKET_SYSTEM_PROMPT = """You are a financial market data analyst.
Use the available tools to fetch current market data and provide insights.
Always cite specific numbers and data points in your analysis.
When analyzing stocks, consider both price action and technical indicators. 
Summarize result in 1-2 sentences concisely."""

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
    # Static mock data matching dataset expectations - replace with your internal API
    stock_data = {
        "AAPL": {"price": 185.50, "change": 2.3},
        "MSFT": {"price": 350.75, "change": 1.8},
        "GOOGL": {"price": 140.20, "change": 0.0},
        "TSLA": {"price": 245.30, "change": 1.5}
    }
    
    data = stock_data.get(symbol.upper(), {"price": 100.0, "change": 0.0})
    
    result = {
        "symbol": symbol.upper(),
        "price": data["price"],
        "timestamp": datetime.now().isoformat()
    }
    
    if include_change:
        # Calculate change_percent from change and price
        prev_price = data["price"] - data["change"]
        result.update({
            "change": data["change"],
            "change_percent": round((data["change"] / prev_price) * 100, 2) if prev_price != 0 else 0.0
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
    # Static mock data matching dataset expectations - replace with your internal API
    sector_sentiments = {
        "technology": {"sentiment": "bullish", "confidence": 0.85}
    }
    
    sentiment_data = sector_sentiments.get(sector.lower(), {
        "sentiment": "neutral",
        "confidence": 0.75
    })
    
    return {
        "sector": sector,
        "sentiment": sentiment_data["sentiment"],
        "confidence": sentiment_data["confidence"],
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
    # Static mock data matching dataset expectations - replace with your internal API
    ma_data = {
        "GOOGL": {
            200: {"current": 140.20, "ma": 138.50}
        },
        "AAPL": {
            50: {"current": 185.50, "ma": 180.00},
            200: {"current": 185.50, "ma": 175.00}
        }
    }
    
    # Default values if symbol/period not in lookup
    default_current = 185.50
    default_ma = 180.00
    
    symbol_data = ma_data.get(symbol.upper(), {})
    period_data = symbol_data.get(period, {
        "current": default_current,
        "ma": default_ma
    })
    
    current_price = period_data["current"]
    ma = period_data["ma"]
    
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

