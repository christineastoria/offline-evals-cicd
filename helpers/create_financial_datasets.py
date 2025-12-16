"""
Financial Dataset Creation and Update Script

This script creates or updates LangSmith datasets with the latest financial data.
It performs a BATCH recreation of datasets, deleting old examples and creating new ones
with today's updated information. This ensures your evaluation datasets always reflect
current market conditions and portfolio states.

The script is designed to run daily (via GitHub Actions cron) to keep datasets fresh.
Replace the mock data generation functions with calls to your internal APIs to fetch
real-time financial data for your evaluation datasets.
"""

from dotenv import load_dotenv
from langsmith import Client
from datetime import datetime

load_dotenv(override=True)
client = Client()

def generate_portfolio_examples():
    """
    Generate portfolio analysis examples with expected tool calls.
    
    This function creates a batch of examples with today's date for portfolio evaluation.
    
    Note:
        Replace this mock implementation with calls to your internal APIs to fetch:
        - Real portfolio positions and values
        - Actual risk metrics from your risk management system
        - Historical performance data from your data warehouse
        
    The examples should represent realistic queries your users would make and the
    expected responses from your portfolio analysis system.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Mock examples - replace with data from your internal portfolio API
    return [
        {
            "inputs": {
                "question": f"What is my portfolio's risk profile as of {today}?",
            },
            "outputs": {
                "response": f"As of {today}, your portfolio shows a volatility of 18% with a Sharpe ratio of 1.2, indicating moderate risk with good risk-adjusted returns.",
                "expected_tools": [
                    {"name": "get_portfolio_data", "args": {"question": "risk profile"}},
                    {"name": "calculate_portfolio_metrics", "args": {"metric_type": "risk"}}
                ]
            },
        },
        {
            "inputs": {
                "question": "What are my top performing positions?",
            },
            "outputs": {
                "response": "Your top performing positions are: AAPL (+15%), MSFT (+12%), and GOOGL (+8%).",
                "expected_tools": [
                    {"name": "get_portfolio_data", "args": {"question": "top performing positions"}}
                ]
            },
        },
        {
            "inputs": {
                "question": "Calculate my portfolio's performance metrics",
            },
            "outputs": {
                "response": "Your YTD return is 12.5%, total return is 45%, with an alpha of 3%.",
                "expected_tools": [
                    {"name": "calculate_portfolio_metrics", "args": {"metric_type": "performance"}}
                ]
            },
        },
    ]

def generate_market_data_examples():
    """
    Generate market data examples with expected tool calls and arguments.
    
    This function creates a batch of examples with today's market data for evaluation.
    
    Note:
        Replace this mock implementation with calls to your internal APIs to fetch:
        - Real-time stock prices from your market data API
        - Sentiment data from your market intelligence system
        - Technical indicators from your analytics platform
        
    The examples should reflect actual market queries and the expected tool usage patterns
    for your market data agent.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Mock examples - replace with data from your internal market data API
    return [
        {
            "inputs": {
                "question": f"What is Apple's stock price today ({today})?",
            },
            "outputs": {
                "response": f"As of {today}, Apple (AAPL) is trading at $185.50, up 2.3% from previous close.",
                "expected_tools": [
                    {"name": "get_stock_price", "args": {"symbol": "AAPL", "include_change": True}}
                ]
            },
        },
        {
            "inputs": {
                "question": "What's the weekly sentiment in the technology sector?",
            },
            "outputs": {
                "response": "The technology sector shows bullish sentiment (85% confidence) on a weekly basis, driven by strong earnings.",
                "expected_tools": [
                    {"name": "get_market_sentiment", "args": {"sector": "technology", "timeframe": "weekly"}}
                ]
            },
        },
        {
            "inputs": {
                "question": "Is GOOGL above its 200-day moving average?",
            },
            "outputs": {
                "response": "GOOGL at $140.20 is above its 200-day moving average of $138.50, showing bullish signal.",
                "expected_tools": [
                    {"name": "get_stock_price", "args": {"symbol": "GOOGL", "include_change": False}},
                    {"name": "calculate_moving_average", "args": {"symbol": "GOOGL", "period": 200}}
                ]
            },
        },
        {
            "inputs": {
                "question": "Compare AAPL and MSFT stock prices",
            },
            "outputs": {
                "response": "AAPL is at $185.50 (+2.3%) and MSFT is at $350.75 (+1.8%).",
                "expected_tools": [
                    {"name": "get_stock_price", "args": {"symbol": "AAPL", "include_change": True}},
                    {"name": "get_stock_price", "args": {"symbol": "MSFT", "include_change": True}}
                ]
            },
        },
    ]

def create_or_update_dataset(dataset_name: str, examples: list):
    """
    Create or update a LangSmith dataset with fresh examples.
    
    This function performs a BATCH recreation of the dataset:
    1. If the dataset exists, it deletes all old examples
    2. Creates new examples with today's updated data
    3. This creates a new version in LangSmith's dataset versioning system
    4. Tags the new version with today's date and "latest" tag
    
    This approach ensures your evaluation datasets always contain current data
    from your APIs, reflecting real-time market conditions and portfolio states.
    
    Args:
        dataset_name: Name of the dataset to create or update
        examples: List of example dictionaries with inputs and expected outputs
    
    Note:
        The examples list should be generated using your internal APIs to ensure
        the evaluation data reflects your current production data and use cases.
    """
    
    if client.has_dataset(dataset_name=dataset_name):
        print(f"Dataset '{dataset_name}' exists. Performing batch recreation with updated data...")
        dataset = client.read_dataset(dataset_name=dataset_name)
        
        # Delete all old examples (batch deletion)
        print(f"Deleting old examples from '{dataset_name}'...")
        for example in client.list_examples(dataset_id=dataset.id):
            client.delete_example(example.id)
        
        # Create new examples with today's data (batch creation)
        # This creates a new version in LangSmith's dataset versioning
        print(f"Creating {len(examples)} new examples with updated data...")
        client.create_examples(dataset_id=dataset.id, examples=examples)
        print(f"Updated dataset '{dataset_name}' with {len(examples)} fresh examples")
    else:
        print(f"Creating new dataset '{dataset_name}'...")
        dataset = client.create_dataset(dataset_name=dataset_name)
        client.create_examples(dataset_id=dataset.id, examples=examples)
        print(f"Created dataset '{dataset_name}' with {len(examples)} examples")
    
    # Tag this version with today's date for tracking
    # See: https://docs.langchain.com/langsmith/manage-datasets#tag-a-version
    today = datetime.now().strftime("%Y-%m-%d")
    client.update_dataset_tag(dataset_name=dataset_name, tag=f"daily-{today}")
    client.update_dataset_tag(dataset_name=dataset_name, tag="latest")
    print(f"Tagged dataset version as 'daily-{today}' and 'latest'")
    print(f"This version can be referenced in evaluations using the 'daily-{today}' tag")

if __name__ == "__main__":
    print("="*60)
    print("Financial Datasets Batch Update")
    print("="*60)
    print(f"Starting dataset recreation with data as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Note: Replace the mock data generation functions with calls to")
    print("your internal APIs to fetch real-time financial data for evaluations.")
    print()
    
    # Generate examples from your APIs and recreate datasets
    portfolio_examples = generate_portfolio_examples()
    create_or_update_dataset("financial-portfolio-agent", portfolio_examples)
    
    print()
    
    market_examples = generate_market_data_examples()
    create_or_update_dataset("financial-market-agent", market_examples)
    
    print()
    print("="*60)
    print("All datasets recreated successfully with updated daily data!")
    print("="*60)

