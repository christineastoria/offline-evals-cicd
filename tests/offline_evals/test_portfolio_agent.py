import json
import pytest
from langchain_core.messages import HumanMessage, AIMessage
from langsmith import Client
from openevals.llm import create_llm_as_judge

from agents.portfolio_agent import agent

client = Client()

CORRECTNESS_PROMPT = """
You are a financial expert evaluating portfolio analysis responses.

Question: {inputs}
Expected Response: {reference_outputs}
Actual Response and Tool Usage: {outputs}

Evaluate if the actual response provides accurate, helpful portfolio analysis.
Consider both the tools called and the final answer quality.

Respond with CORRECT or INCORRECT.

CORRECT means: accurate financial data, relevant insights, actionable recommendations.
INCORRECT means: wrong data, irrelevant analysis, or poor recommendations.

Grade:
"""

QUALITY_PROMPT = """
Rate the quality of this portfolio analysis on a scale of 1-5:

Question: {inputs}
Expected Response: {reference_outputs}
Actual Response: {outputs}

Rating scale:
1. Completely incorrect or unhelpful
2. Partially correct but missing key insights
3. Mostly correct with minor issues
4. Correct and helpful analysis
5. Excellent, comprehensive financial analysis

Rating:
"""

correctness_evaluator = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,
    feedback_key="portfolio_correctness",
    model="openai:gpt-4o-mini",
)

quality_evaluator = create_llm_as_judge(
    prompt=QUALITY_PROMPT,
    feedback_key="portfolio_quality",
    model="openai:gpt-4o-mini",
)

def extract_tool_calls_with_args(messages: list) -> list:
    """Extract tool calls with their arguments from agent messages"""
    tool_calls_info = []
    
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_info = {
                    "name": tc.get('name', 'unknown'),
                    "args": tc.get('args', {})
                }
                tool_calls_info.append(tool_info)
    
    return tool_calls_info

def ls_target(inputs: dict) -> dict:
    """LangSmith target function for portfolio agent"""
    try:
        result = agent.invoke({"messages": [HumanMessage(content=inputs["question"])]})
        
        tool_calls = []
        if result and "messages" in result:
            tool_calls = extract_tool_calls_with_args(result["messages"])
            response = result["messages"][-1].content if result["messages"] else "No response"
            
            # Format tool calls for context
            tool_info = [f"{tc['name']}({tc['args']})" for tc in tool_calls]
            
            return {
                "response": response or "No response generated",
                "tool_calls": tool_calls,
                "tool_calls_summary": ", ".join(tool_info) if tool_info else "No tools used"
            }
        
        return {"response": "No response generated", "tool_calls": [], "tool_calls_summary": ""}
    except Exception as e:
        return {"response": f"Error: {str(e)}", "tool_calls": [], "tool_calls_summary": ""}

@pytest.mark.evaluator
def test_portfolio_evaluation():
    """Run portfolio agent evaluation using LangSmith"""
    
    experiment_results = client.evaluate(
        ls_target,
        data="financial-portfolio-agent",
        evaluators=[correctness_evaluator, quality_evaluator],
        max_concurrency=10,
        experiment_prefix="financial-portfolio-eval",
    )
    
    assert experiment_results is not None
    print(f"Evaluation completed: {experiment_results.experiment_name}")
    
    criteria = {
        "portfolio_correctness": ">=0.8",
        "portfolio_quality": ">=3.5"
    }
    
    output_metadata = {
        "experiment_name": experiment_results.experiment_name,
        "criteria": criteria,
    }
    
    safe_name = experiment_results.experiment_name.replace(":", "-").replace("/", "-")
    config_filename = f"evaluation_config__{safe_name}.json"
    with open(config_filename, "w") as f:
        json.dump(output_metadata, f)
    
    print(f"::set-output name=config_filename::{config_filename}")

