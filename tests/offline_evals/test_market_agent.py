import json
import pytest
from langchain_core.messages import HumanMessage, AIMessage
from langsmith import Client
from openevals.llm import create_llm_as_judge

from agents.market_data_agent import agent

client = Client()

TRAJECTORY_WITH_ARGS_PROMPT = """
You are evaluating an AI agent's tool usage for financial market analysis.

Question: {inputs}
Expected Tool Calls and Arguments: {reference_outputs}
Actual Agent Tool Calls with Arguments: {outputs}

Evaluate if the agent:
1. Called the appropriate tools for the question
2. Passed correct and relevant arguments to the tools
3. Used appropriate argument values (e.g., correct symbols, timeframes, periods)
4. Made good use of tool outputs in the final response

Respond with CORRECT or INCORRECT.

CORRECT means: right tools, correct arguments, logical flow, good integration.
INCORRECT means: wrong tools, incorrect/missing arguments, or poor use of outputs.

Grade:
"""

TOOL_ARGS_QUALITY_PROMPT = """
Rate the quality of tool usage AND argument selection on a scale of 1-5:

Question: {inputs}
Expected Tool Usage: {reference_outputs}
Actual Tool Calls with Arguments: {outputs}

Focus on:
- Tool selection appropriateness
- Argument correctness and completeness
- Argument value appropriateness (right symbols, timeframes, etc.)

Rating scale:
1. No tools or completely wrong tools/arguments
2. Some correct tools but poor or missing arguments
3. Mostly correct tools and arguments with minor issues
4. Correct tools with appropriate arguments
5. Excellent tool and argument selection

Rating:
"""

trajectory_evaluator = create_llm_as_judge(
    prompt=TRAJECTORY_WITH_ARGS_PROMPT,
    feedback_key="tool_trajectory_with_args",
    model="openai:gpt-4o-mini",
)

tool_quality_evaluator = create_llm_as_judge(
    prompt=TOOL_ARGS_QUALITY_PROMPT,
    feedback_key="tool_args_quality",
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
                    "args": tc.get('args', {}),
                    "id": tc.get('id', '')
                }
                tool_calls_info.append(tool_info)
    
    return tool_calls_info

def format_tool_calls_for_eval(tool_calls: list) -> str:
    """Format tool calls with arguments for evaluation"""
    if not tool_calls:
        return "No tool calls made"
    
    formatted = []
    for tc in tool_calls:
        args_str = ", ".join([f"{k}={v}" for k, v in tc['args'].items()])
        formatted.append(f"{tc['name']}({args_str})")
    
    return " -> ".join(formatted)

def ls_target(inputs: dict) -> dict:
    """LangSmith target function for market agent with trajectory and arguments"""
    try:
        result = agent.invoke({"messages": [HumanMessage(content=inputs["question"])]})
        
        # Extract tool calls with arguments
        tool_calls = []
        trajectory_parts = []
        
        if result and "messages" in result:
            tool_calls = extract_tool_calls_with_args(result["messages"])
            
            # Build detailed trajectory
            for msg in result["messages"]:
                if isinstance(msg, AIMessage):
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            args_str = ", ".join([f"{k}={v}" for k, v in tc.get('args', {}).items()])
                            trajectory_parts.append(f"Tool: {tc.get('name')}({args_str})")
                    if msg.content:
                        trajectory_parts.append(f"Response: {msg.content[:100]}...")
            
            final_response = result["messages"][-1].content if result["messages"] else "No response"
            tool_calls_formatted = format_tool_calls_for_eval(tool_calls)
            
            return {
                "response": final_response or "No response generated",
                "tool_calls_with_args": tool_calls,
                "tool_calls_formatted": tool_calls_formatted,
                "trajectory": " | ".join(trajectory_parts)
            }
        
        return {
            "response": "No response generated",
            "tool_calls_with_args": [],
            "tool_calls_formatted": "No tool calls",
            "trajectory": ""
        }
    except Exception as e:
        return {
            "response": f"Error: {str(e)}",
            "tool_calls_with_args": [],
            "tool_calls_formatted": "Error",
            "trajectory": ""
        }

@pytest.mark.evaluator
def test_market_agent_evaluation():
    """Run market agent evaluation with trajectory and argument analysis"""
    
    experiment_results = client.evaluate(
        ls_target,
        data="financial-market-agent",
        evaluators=[trajectory_evaluator, tool_quality_evaluator],
        max_concurrency=10,
        experiment_prefix="financial-market-eval",
    )
    
    assert experiment_results is not None
    print(f"Market agent evaluation completed: {experiment_results.experiment_name}")
    
    criteria = {
        "tool_trajectory_with_args": ">=0.75",
        "tool_args_quality": ">=3.5"
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

