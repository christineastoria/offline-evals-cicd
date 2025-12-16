# Financial Agents CI/CD Pipeline

A demonstration of **continuous evaluation** for LLM agents using LangSmith, with daily-refreshed datasets and automated reporting.

## Overview

This project showcases how to build a robust evaluation pipeline for financial agents that runs automatically via CI/CD. The key demonstration is **evaluating agents against fresh, real-world data every day** and distributing results to your team.

### What This Demonstrates

**Evaluation Types:**
- **LLM-as-Judge**: Evaluates response correctness and quality for the portfolio agent
- **Trajectory Evaluation**: Validates tool selection AND argument correctness for the market agent

**Automated Pipeline:**
- **Daily Dataset Refresh**: Batch recreates evaluation datasets with today's data from your APIs
- **Continuous Evaluation**: Runs evaluations automatically on push, PR, or daily schedule
- **Automated Reporting**: Generates markdown reports and sends to Slack/email

**Two Financial Agents across teams:**
1. **Portfolio Agent**: Analyzes portfolio performance (demonstrates LLM-as-judge evaluation)
2. **Market Data Agent**: Fetches market data with tool calls (demonstrates trajectory evaluation with argument validation)

### Key Features

- Daily batch dataset updates with latest financial data from your APIs
- LLM-as-judge evaluation with configurable pass/fail thresholds
- Trajectory evaluation that validates tool arguments from `AIMessage.tool_calls`
- GitHub Actions CI/CD pipeline (runs on push, PR, or cron schedule)
- Automated Slack notifications with evaluation reports (email alternative available)
- Versioned datasets with daily tags for reproducibility

## Architecture

```
Continuous Evaluation Pipeline:

┌─────────────────────────────────────────────────────────────┐
│  Trigger: Push to main/develop, PR, or Daily Cron (9 AM)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  1. Batch Dataset Refresh                                   │
│     - Delete old examples from LangSmith datasets           │
│     - Fetch today's data from your internal APIs            │
│     - Create new examples with fresh financial data         │
│     - Tag with daily version (e.g., "daily-2024-12-16")     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Run Evaluations (Parallel)                              │
│     - Portfolio: LLM-as-judge (correctness + quality)       │
│     - Market: Trajectory eval (tool args validation)        │
│     - Compare against expected outputs in datasets          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Generate Report                                         │
│     - Aggregate evaluation metrics                          │
│     - Apply pass/fail thresholds                            │
│     - Create markdown report                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Distribute Results                                      │
│     - Send Slack notification with summary                  │
│     - Post PR comment (if triggered by PR)                  │
│     - Store artifacts in GitHub Actions                     │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer
- OpenAI API key
- LangSmith API key
- Slack webhook URL (optional, for notifications)

## Quick Start

### 1. Install Dependencies

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 2. Environment Configuration

Create a `.env` file with your API keys:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# LangSmith Configuration
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=financial-agents-
```

### 3. Create Initial Datasets

Run the dataset creation script to set up your evaluation datasets:

```bash
uv run python helpers/create_financial_datasets.py
```

**Note**: Replace the mock data in this script with calls to your internal APIs to fetch real financial data.

### 4. Test the Agents Locally

```bash
# Test portfolio agent
uv run python -c "from agents.portfolio_agent import agent; print(agent.invoke({'messages': [{'role': 'user', 'content': 'What is my portfolio value?'}]}))"

# Test market agent
uv run python -c "from agents.market_data_agent import agent; print(agent.invoke({'messages': [{'role': 'user', 'content': 'What is AAPL stock price?'}]}))"
```

### 5. Run Evaluations

```bash
# Run both evaluations
uv run pytest tests/offline_evals/ -m evaluator
```

## Project Structure

```
financial-agents-cicd/
├── agents/
│   ├── __init__.py
│   ├── portfolio_agent.py      # Portfolio analysis agent
│   └── market_data_agent.py    # Market data agent with tools
├── tests/
│   └── offline_evals/
│       ├── test_portfolio_agent.py  # LLM-as-judge eval
│       └── test_market_agent.py     # Trajectory eval with args
├── helpers/
│   └── create_financial_datasets.py # Dataset creation/update
├── .github/
│   ├── workflows/
│   │   └── financial-agents-pipeline.yml  # CI/CD pipeline
│   └── scripts/
│       └── report_eval.py          # Evaluation report creator
├── pyproject.toml
├── langgraph.json
└── README.md
```

## Agents

### Portfolio Agent

Simple agent that analyzes portfolio data without external tool calls.

**Tools:**
- `get_portfolio_data()` - Fetch portfolio positions and values
- `calculate_portfolio_metrics()` - Calculate risk/performance metrics

**Evaluation:**
- LLM-as-judge for response correctness and quality
- Thresholds: correctness >= 0.8, quality >= 3.5

### Market Data Agent

Agent with tool calls for fetching market data and analysis.

**Tools:**
- `get_stock_price(symbol, include_change)` - Get current stock prices
- `get_market_sentiment(sector, timeframe)` - Get sector sentiment
- `calculate_moving_average(symbol, period)` - Calculate moving averages

**Evaluation:**
- Trajectory evaluation considering tool selection AND arguments
- Tool argument validation (symbols, timeframes, periods)
- Thresholds: trajectory >= 0.75, tool quality >= 3.5

## Dataset Management

This pipeline uses **batch dataset recreation** to ensure fresh data:

1. Deletes all old examples from existing datasets
2. Creates new examples with today's data from your APIs
3. Tags with daily timestamp and "latest" tag
4. Creates new version in LangSmith

**To integrate with your APIs:**

Edit `helpers/create_financial_datasets.py` and replace mock functions with internal API calls:
- Portfolio API for positions and risk metrics
- Market data API for prices and sentiment
- Technical analysis API for indicators

## CI/CD Pipeline

### Triggers

- Push to `main` or `develop` branches
- Pull requests
- Daily cron at 9 AM UTC

### Pipeline Jobs

1. **update-datasets**: Recreates datasets with today's data
2. **run-evaluations**: Runs both agent evaluations in parallel
3. **generate-report**: Creates markdown evaluation report
4. **notify-slack**: Sends Slack notification with results
5. **post-pr-comment**: Comments on PR with evaluation results

### Required GitHub Secrets

```bash
# Core secrets
OPENAI_API_KEY=your_openai_key
LANGSMITH_API_KEY=your_langsmith_key

# Slack notifications (recommended)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Notifications

### Slack Setup (Current Implementation)

This pipeline uses Slack to receive the report for simplicity. Setup:

1. Create Slack app at https://api.slack.com/apps
2. Enable "Incoming Webhooks"
3. Add webhook to desired channel (e.g., `#agent-evaluations`)
4. Copy webhook URL
5. Add `SLACK_WEBHOOK_URL` secret to GitHub

### Email Alternative

If you prefer email notifications, you can replace the `notify-slack` job with email configuration using `dawidd6/action-send-mail@v3`. This requires:
- SMTP server configuration
- Email credentials (username/password)
- Recipient email addresses

See comments in the workflow file for email setup details.

## Evaluation Criteria

### Portfolio Agent

- **Correctness**: Binary evaluation of response accuracy
- **Quality**: 1-5 rating of analysis comprehensiveness
- **Pass Criteria**: correctness >= 0.8, quality >= 3.5

## Development

### Running Tests Locally

```bash
# Run all tests
uv run pytest

# Run only evaluations
uv run pytest -m evaluator

# Run with verbose output
uv run pytest -v tests/offline_evals/
```

### Pre-commit Hooks

```bash
# Install pre-commit
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

## Resources
- [LangChain create_agent Documentation](https://docs.langchain.com/oss/python/langchain/overview)
- [LangSmith Dataset Management](https://docs.langchain.com/langsmith/manage-datasets)
- [OpenEvals Documentation](https://github.com/langchain-ai/openevals)

## License

MIT License - See LICENSE file for details
