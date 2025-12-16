# Financial Agents CI/CD Pipeline

Demo for continuous daily evaluation of LLM agents with refreshed datasets and automated offline eval reports sent to Slack.

## Overview
Demonstrates evaluating financial agents against fresh data daily using LangSmith evaluations in CI/CD using llm-as-judge, trajectory, and prebuilt evals. 

## Project Structure
```
financial-agents-cicd/
├── agents/
│   ├── __init__.py
│   ├── portfolio_agent.py      # Portfolio analysis agent
│   └── market_data_agent.py    # Market data agent with tools
├── evals/
│   ├── run_portfolio_eval.py   # Portfolio LLM-as-judge eval
│   ├── run_market_eval.py      # Market trajectory eval with args
│   └── run_all_evals.py        # Run all evals in sequence
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
### Key Features
- Daily dataset refresh with latest data from your APIs
- Trajectory evaluation using agentevals (unordered tool matching)
- LLM-as-judge with openevals and custom evaluators
- GitHub Actions CI/CD (push, PR, or cron schedule)
- Slack notifications with evaluation reports
- Versioned datasets with daily tags

### Agents to evaluate

**Portfolio Agent** 
Agent which analyzes a specific portfolio and provides recommendations
Tools: `get_portfolio_data()`, `calculate_portfolio_metrics()`
Evaluators:  Trajectory + Correctness
- Unordered trajectory matching (agentevals open source) - validates tool calls
- Response correctness (openevals open source) - validates answer quality
<img width="660" height="366" alt="Screenshot 2025-12-16 at 2 10 18 PM" src="https://github.com/user-attachments/assets/b5e7b3e1-31de-4978-bba0-2bc47f1800a8" />


**Market Data Agent**
Agent which analyzes market data and cites specific data points
Tools: `get_stock_price()`, `get_market_sentiment()`, `calculate_moving_average()`
Evaluators: Relevance + Tool Arguments  
- Custom LLM-as-judge - evaluates response relevance
- Custom code tool evaluator - validates tool names + arguments match
<img width="660" height="366" alt="Screenshot 2025-12-16 at 2 10 30 PM" src="https://github.com/user-attachments/assets/6d36f03b-180d-450d-809a-448eec27a81b" />


## Pipeline Flow
```
Trigger (Push/PR/Daily 9AM) → Batch Refresh Datasets → Run Evals → Report → Slack
```
1. **Refresh Datasets**: Delete old examples, fetch today's data, tag with `daily-YYYY-MM-DD`
2. **Run Evaluations**: Portfolio (trajectory + correctness), Market (relevance + tool args)
3. **Report**: Aggregate metrics, apply thresholds, create markdown
4. **Distribute**: Slack notification + PR comment


## Quick Start

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/), OpenAI + LangSmith API keys

```bash
# Install
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# Configure env
cp .env.example > .env

OPENAI_API_KEY=your_key
LANGSMITH_API_KEY=your_key
LANGSMITH_TRACING=true

# Create datasets (replace mock data with your API calls)
uv run python helpers/create_financial_datasets.py

# Run evaluations
uv run python evals/run_all_evals.py
```


## CI/CD Setup

**Triggers:** Push to main/develop, PRs, daily cron (9 AM UTC)

**GitHub Secrets:**
```bash
OPENAI_API_KEY=your_key
LANGSMITH_API_KEY=your_key
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Jobs:** update-datasets → run-evaluations → generate-report → notify-slack → post-pr-comment

## Slack Setup

1. Create Slack app at https://api.slack.com/apps
2. Enable "Incoming Webhooks" → Add to channel (e.g., `#agent-evals`)
3. Copy webhook URL → Add as `SLACK_WEBHOOK_URL` GitHub secret

**Email alternative:** Replace notify-slack job with SAML email setup

## Local Development

```bash
# Run all evals
uv run python evals/run_all_evals.py

# Individual evals
uv run python evals/run_portfolio_eval.py
uv run python evals/run_market_eval.py
```

## Resources
- [LangChain create_agent](https://docs.langchain.com/oss/python/langchain/overview)
- [LangSmith evals](https://docs.langchain.com/langsmith/evaluation)
- [LangSmith Datasets](https://docs.langchain.com/langsmith/manage-datasets)
- [AgentEvals](https://docs.langchain.com/langsmith/trajectory-evals)
- [OpenEvals](https://github.com/langchain-ai/openevals)
