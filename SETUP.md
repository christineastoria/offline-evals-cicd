# Quick Setup Guide

This guide will help you get the Financial Agents CI/CD pipeline up and running.

## Step 1: Install Dependencies

```bash
cd financial-agents-cicd

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync project dependencies
uv sync
```

## Step 2: Configure Environment Variables

Create a `.env` file:

```bash
# Copy from example (create manually)
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-key-here
LANGSMITH_API_KEY=lsv2_pt_your-key-here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=financial-agents
EOF
```

## Step 3: Create Datasets in LangSmith

```bash
# Run dataset creation script
uv run python helpers/create_financial_datasets.py
```

This creates two datasets:
- `financial-portfolio-agent`
- `financial-market-agent`

## Step 4: Test Agents Locally

```bash
# Test portfolio agent
uv run python -c "
from agents.portfolio_agent import agent
from langchain_core.messages import HumanMessage
result = agent.invoke({'messages': [HumanMessage(content='What is my portfolio value?')]})
print(result)
"

# Test market agent
uv run python -c "
from agents.market_data_agent import agent
from langchain_core.messages import HumanMessage
result = agent.invoke({'messages': [HumanMessage(content='What is AAPL stock price?')]})
print(result)
"
```

## Step 5: Run Evaluations

```bash
# Run both evaluations
uv run pytest tests/offline_evals/ -m evaluator -v
```

This will:
1. Run portfolio agent evaluation (LLM-as-judge)
2. Run market agent evaluation (trajectory with tool args)
3. Generate evaluation config JSON files
4. Display results

## Step 6: Setup GitHub Actions (Optional)

### Required GitHub Secrets

Go to GitHub repo → Settings → Secrets → Actions → New repository secret:

1. `OPENAI_API_KEY` - Your OpenAI API key
2. `LANGSMITH_API_KEY` - Your LangSmith API key
3. `SLACK_WEBHOOK_URL` - Your Slack webhook URL (for notifications)

### Slack Webhook Setup

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "Financial Agents CI/CD"
4. Select your workspace
5. Go to "Incoming Webhooks" → Toggle ON
6. Click "Add New Webhook to Workspace"
7. Select channel (e.g., `#agent-evaluations`)
8. Copy webhook URL → Add to GitHub secrets as `SLACK_WEBHOOK_URL`

### Verify Pipeline

Push to `main` or `develop` branch, or create a PR to trigger the pipeline.

## Step 7: Integrate with Your APIs

Replace mock data with real API calls:

### Portfolio Agent

Edit `agents/portfolio_agent.py`:
- Replace `get_portfolio_data()` with your portfolio API
- Replace `calculate_portfolio_metrics()` with your analytics API

### Market Agent

Edit `agents/market_data_agent.py`:
- Replace `get_stock_price()` with your market data API
- Replace `get_market_sentiment()` with your sentiment API
- Replace `calculate_moving_average()` with your technical analysis API

### Dataset Generation

Edit `helpers/create_financial_datasets.py`:
- Update `generate_portfolio_examples()` with real data
- Update `generate_market_data_examples()` with real data

## Verification Checklist

- [ ] Dependencies installed with `uv sync`
- [ ] `.env` file created with API keys
- [ ] Datasets created in LangSmith
- [ ] Agents tested locally
- [ ] Evaluations run successfully
- [ ] GitHub secrets configured (if using CI/CD)
- [ ] Slack webhook set up (if using notifications)
- [ ] Mock data replaced with real APIs (production)

## Common Issues

### "No module named 'agents'"

Run from project root: `cd financial-agents-cicd`

### "Dataset not found"

Run: `uv run python helpers/create_financial_datasets.py`

### Evaluation fails

Check:
1. LangSmith API key is valid
2. Datasets exist in LangSmith
3. OpenAI API key has credits

### GitHub Actions fails

Verify:
1. All secrets are configured
2. Secret names match exactly
3. Workflow file syntax is correct

## Next Steps

1. **Customize evaluations**: Edit evaluation prompts in test files
2. **Add more agents**: Create new agent files following the pattern
3. **Adjust thresholds**: Modify pass/fail criteria in tests
4. **Add deployment**: Extend pipeline to deploy to LangGraph Platform
5. **Monitor production**: Set up alerts for evaluation failures

## Resources

- README.md - Full project documentation
- [LangChain Docs](https://docs.langchain.com/oss/python/langchain/overview)
- [LangSmith Docs](https://docs.langchain.com/langsmith/manage-datasets)
- [OpenEvals](https://github.com/langchain-ai/openevals)

