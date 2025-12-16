"""Market agent evaluation with 2 evaluators:
1. Custom LLM-as-judge for relevance
2. Tool + argument match score (custom code)
"""
import json
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langsmith import Client

from agents.market_data_agent import agent

client = Client()


def ls_target(inputs: dict) -> dict:
    """Run market agent and return results for evaluation."""
    result = agent.invoke({"messages": [HumanMessage(content=inputs["question"])]})
    
    # Extract tool calls from messages
    actual_tools = []
    for msg in result.get("messages", []):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                actual_tools.append({
                    "name": tc.get('name'),
                    "args": tc.get('args', {})
                })
    
    return {
        "Response": result["messages"][-1].content if result.get("messages") else "No response",
        "Actual Tools": actual_tools
    }


# 1. Custom LLM-as-judge for relevance
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def relevance_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """Evaluate if response is relevant to the question."""
    instructions = """You are evaluating whether an AI agent's response is relevant to the user's question about market data.

When grading, a relevant response will:
- Address the specific question asked
- Provide appropriate market data or analysis
- Be on-topic and useful

Grade as True if the response is relevant, False otherwise."""
    
    user_context = f"""Please grade the following:

Question: {inputs.get('question', 'N/A')}
Response: {outputs.get('Response', 'N/A')}
Expected: {reference_outputs.get('response', 'N/A')}

Is the response relevant? Reply with just "True" or "False" followed by a brief explanation."""
    
    result = llm.invoke([
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_context}
    ])
    
    # Parse True/False from response
    response_text = result.content.strip()
    is_relevant = response_text.lower().startswith("true")
    
    return {
        "key": "response_relevance",
        "score": is_relevant,
        "comment": response_text
    }


# 2. Simple custom code evaluator for tool + argument comparison
def tool_and_args_evaluator(outputs: dict, reference_outputs: dict) -> dict:
    """
    Simple comparison of actual tools with expected tools.
    Counts how many tools match (name + args).
    """
    actual_tools = outputs.get("Actual Tools", [])
    expected_tools = reference_outputs.get("expected_tools", [])
    
    if not expected_tools:
        return {"key": "tool_args_match_score", "score": 1.0, "comment": "No expected tools"}
    
    # Count matches
    matches = 0
    for expected in expected_tools:
        for actual in actual_tools:
            if actual["name"] == expected["name"] and actual["args"] == expected["args"]:
                matches += 1
                break
    
    score = matches / len(expected_tools)
    comment = f"{matches}/{len(expected_tools)} tools match"
    
    return {
        "key": "tool_args_match_score",
        "score": score,
        "comment": comment
    }


if __name__ == "__main__":
    # Run evaluation with both evaluators
    experiment_results = client.evaluate(
        ls_target,
        data="financial-market-agent",
        evaluators=[
            relevance_evaluator,
            tool_and_args_evaluator
        ],
        max_concurrency=10,
        experiment_prefix="financial-market-eval",
    )
    
    # Save config for reporting
    criteria = {
        "response_relevance": ">=0.8",
        "tool_args_match_score": ">=0.8"
    }
    
    output_metadata = {
        "experiment_name": experiment_results.experiment_name,
        "dataset_name": "financial-market-agent",
        "criteria": criteria,
    }
    
    safe_name = experiment_results.experiment_name.replace(":", "-").replace("/", "-")
    config_filename = f"evaluation_config__{safe_name}.json"
    with open(config_filename, "w") as f:
        json.dump(output_metadata, f)

