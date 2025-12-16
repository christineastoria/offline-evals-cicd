# Financial Agents CI/CD Pipeline

Continuous evaluation for LLM agents with daily-refreshed datasets and automated reporting.

## Overview

Demonstrates evaluating financial agents against fresh data daily using LangSmith evaluations in CI/CD.

### Evaluation Approaches

**Portfolio Agent** - Trajectory + Correctness
- Unordered trajectory matching (agentevals open source) - validates tool calls
- Response correctness (openevals open source) - validates answer quality
<img width="660" height="366" alt="Screenshot 2025-12-16 at 2 10 18 PM" src="https://github.com/user-attachments/assets/b5e7b3e1-31de-4978-bba0-2bc47f1800a8" />

**Market Agent** - Relevance + Tool Arguments  
- Custom LLM-as-judge - evaluates response relevance
- Custom code tool evaluator - validates tool names + arguments match
<img width="660" height="366" alt="Screenshot 2025-12-16 at 2 10 30 PM" src="https://github.com/user-attachments/assets/6d36f03b-180d-450d-809a-448eec27a81b" />
### Key Features

- Daily dataset refresh with latest data from your APIs
- Trajectory evaluation using agentevals (unordered tool matching)
- LLM-as-judge with openevals and custom evaluators
- GitHub Actions CI/CD (push, PR, or cron schedule)
- Slack notifications with evaluation reports
- Versioned datasets with daily tags

## Pipeline Flow

```
Trigger (Push/PR/Daily 9AM) → Refresh Datasets → Run Evals → Report → Slack
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

# Configure .env
OPENAI_API_KEY=your_key
LANGSMITH_API_KEY=your_key
LANGSMITH_TRACING=true

# Create datasets (replace mock data with your API calls)
uv run python helpers/create_financial_datasets.py

# Run evaluations
uv run python evals/run_all_evals.py
```

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

## Agents & Evaluations

### Portfolio Agent
**Tools:** `get_portfolio_data()`, `calculate_portfolio_metrics()`

**Evaluators:**
1. **Trajectory Match** (agentevals, unordered) - Validates correct tools called
2. **Correctness** (openevals) - Validates response accuracy
   
**Thresholds:** trajectory_match >= 0.8, response_correctness >= 0.8

### Market Data Agent
**Tools:** `get_stock_price()`, `get_market_sentiment()`, `calculate_moving_average()`

**Evaluators:**
1. **Relevance** (custom LLM judge) - Evaluates if response addresses question
2. **Tool + Args Match** (custom code) - Validates exact tool names and arguments

**Thresholds:** response_relevance >= 0.8, tool_args_match_score >= 0.8

## Dataset Management

**Batch recreation daily:** Deletes old examples → Fetches fresh data from your APIs → Creates new examples → Tags with `daily-YYYY-MM-DD`

**Portfolio dataset:** Stores reference message trajectories (HumanMessage → AIMessage with tool_calls → ToolMessage → final AIMessage)

**Market dataset:** Stores expected response + expected_tools list

**To integrate:** Edit `helpers/create_financial_datasets.py` and replace mock functions with your API calls.

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

**Email alternative:** Replace notify-slack job with `dawidd6/action-send-mail@v3` (see workflow comments).

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
