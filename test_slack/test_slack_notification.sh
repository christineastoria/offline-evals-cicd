#!/bin/bash
# Local test script for Slack notification
# Usage: ./test_slack_notification.sh
# Make sure you have SLACK_WEBHOOK_URL in your .env file

set -e

echo "Testing Slack notification locally..."
echo "=========================================="

# Load .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "WARNING: .env file not found. Make sure SLACK_WEBHOOK_URL is set."
fi

# Check if SLACK_WEBHOOK_URL is set
if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo "ERROR: SLACK_WEBHOOK_URL is not set"
    echo "Please add it to your .env file:"
    echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    exit 1
fi

# Simulate workflow variables
REPO="christineastoria/offline-evals-cicd"
BRANCH="main"
ACTOR="local-test"
RUN_ID="12345"
RUN_URL="https://github.com/christineastoria/offline-evals-cicd/actions/runs/12345"

# Generate report from actual eval configs if they exist, otherwise create sample
if [ -f evaluation_config__*.json ]; then
    echo "Found evaluation configs, generating actual report..."
    python .github/scripts/report_eval.py evaluation_config__*.json 2>/dev/null || {
        echo "Failed to generate report from configs, using sample..."
        USE_SAMPLE=true
    }
else
    USE_SAMPLE=true
fi

if [ "$USE_SAMPLE" = "true" ] || [ ! -f eval_comment.md ]; then
    cat > eval_comment.md <<'REPORT'
# Financial Agents Evaluation Results

## financial-portfolio-eval

[View Experiment in LangSmith](https://smith.langchain.com/o/default/datasets/financial-portfolio-agent/compare?selectedSessions=financial-portfolio-eval)

**Dataset:** financial-portfolio-agent ([view](https://smith.langchain.com/o/default/datasets/financial-portfolio-agent))

**Examples:** 3

**Metrics:**

- **trajectory_unordered_match**: 0.95 — Measures if the agent called the correct tools regardless of order
- **response_correctness**: 0.92 — LLM judge evaluation of response accuracy compared to reference

---

## financial-market-eval

[View Experiment in LangSmith](https://smith.langchain.com/o/default/datasets/financial-market-agent/compare?selectedSessions=financial-market-eval)

**Dataset:** financial-market-agent ([view](https://smith.langchain.com/o/default/datasets/financial-market-agent))

**Examples:** 3

**Metrics:**

- **response_relevance**: 0.89 — LLM judge evaluation of response relevance to the question
- **tool_args_match_score**: 0.93 — Measures accuracy of tool names and arguments used

---
REPORT
    echo "Created sample eval_comment.md with new format for testing"
fi

# Read evaluation report (limit to 1200 chars for Slack, clean special chars)
if [ -f eval_comment.md ]; then
    # Take first 1200 chars and remove any null bytes or control chars that break JSON
    REPORT=$(head -c 1200 eval_comment.md | tr -d '\000-\010\013\014\016-\037')
else
    REPORT="Report not available"
fi

echo ""
echo "Building Slack message with jq..."
echo ""

# Use jq to properly create JSON with escaped strings
jq -n \
  --arg repo "$REPO" \
  --arg branch "$BRANCH" \
  --arg actor "$ACTOR" \
  --arg run_id "$RUN_ID" \
  --arg report "$REPORT" \
  --arg run_url "$RUN_URL" \
  '{
    text: "Financial Agents Evaluation Report",
    blocks: [
      {
        type: "header",
        text: {
          type: "plain_text",
          text: "Financial Agents Evaluation"
        }
      },
      {
        type: "section",
        fields: [
          {type: "mrkdwn", text: "*Branch:*\n\($branch)"},
          {type: "mrkdwn", text: "*Triggered by:*\n\($actor)"},
          {type: "mrkdwn", text: "*Repository:*\n\($repo)"}
        ]
      },
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: "*Evaluation Results:*\n```\n\($report)\n```"
        }
      },
      {
        type: "actions",
        elements: [
          {
            type: "button",
            text: {type: "plain_text", text: "View Full Results"},
            url: $run_url
          }
        ]
      }
    ]
  }' > slack_message.json

# Verify JSON is valid
echo "Validating JSON..."
if jq . slack_message.json > /dev/null; then
    echo "JSON is valid"
else
    echo "Invalid JSON generated"
    exit 1
fi

echo ""
echo "Generated Slack message (slack_message.json):"
echo "=========================================="
cat slack_message.json | jq .
echo "=========================================="
echo ""

# Send to Slack
echo "Sending to Slack webhook..."
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d @slack_message.json)

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS")

echo ""
if [ "$HTTP_STATUS" = "200" ]; then
    echo "Slack notification sent successfully"
    echo "Response: $BODY"
else
    echo "Failed to send Slack notification"
    echo "HTTP Status: $HTTP_STATUS"
    echo "Response: $BODY"
    exit 1
fi

echo ""
echo "Test complete!"

