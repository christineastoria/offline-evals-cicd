from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

load_dotenv(override=True)

PORTFOLIO_SYSTEM_PROMPT = """You are a portfolio analysis expert. 
Analyze portfolio performance, risk metrics, and provide recommendations 
based on the data provided. Be concise and data-driven.

When users ask about their portfolio, you should analyze:
- Total portfolio value and composition
- Individual position performance
- Risk metrics (volatility, Sharpe ratio, drawdown)
- Recommendations for rebalancing or optimization"""

def get_portfolio_data(question: str = "") -> dict:
    """Get current portfolio data including positions and risk metrics.
    
    Args:
        question: Optional context about what portfolio information is needed
    
    Returns:
        Dictionary containing portfolio positions, values, and risk metrics
    
    Note:
        Replace this mock implementation with calls to your internal portfolio API,
        database, or data warehouse to fetch real-time portfolio data.
    """
    # Mock data - replace with your internal API calls
    return {
        "total_value": 1000000,
        "positions": [
            {"symbol": "AAPL", "shares": 100, "value": 18500, "return": 0.15},
            {"symbol": "GOOGL", "shares": 50, "value": 7000, "return": 0.08},
            {"symbol": "MSFT", "shares": 150, "value": 52500, "return": 0.12}
        ],
        "risk_metrics": {
            "volatility": 0.18,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.15
        }
    }

def calculate_portfolio_metrics(metric_type: str) -> dict:
    """Calculate specific portfolio metrics.
    
    Args:
        metric_type: Type of metric to calculate (risk, performance, diversification)
    
    Returns:
        Dictionary containing calculated metrics
    
    Note:
        Replace this mock implementation with calls to your internal analytics API
        or calculation engine for real portfolio metrics.
    """
    metrics = {
        "risk": {"volatility": 0.18, "var_95": 0.12, "sharpe_ratio": 1.2},
        "performance": {"ytd_return": 0.125, "total_return": 0.45, "alpha": 0.03},
        "diversification": {"concentration": 0.52, "sector_count": 2, "correlation": 0.65}
    }
    return metrics.get(metric_type, {})

# Create agent with tools
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_agent(
    model=llm,
    tools=[get_portfolio_data, calculate_portfolio_metrics],
    system_prompt=PORTFOLIO_SYSTEM_PROMPT,
)

