"""Portfolio agent evaluation with 2 evaluators:
1. Unordered trajectory match (agentevals)
2. Response correctness (openevals)
"""
import json
from langchain_core.messages import HumanMessage, AIMessage
from langsmith import Client
from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT
from agentevals.trajectory.match import create_trajectory_match_evaluator

from agents.portfolio_agent import agent

client = Client()


def ls_target(inputs: dict) -> dict:
    """Run portfolio agent and return results for evaluation."""
    result = agent.invoke({"messages": [HumanMessage(content=inputs["question"])]})
    
    return {
        "Response": result["messages"][-1].content if result.get("messages") else "No response",
        "messages": result.get("messages", [])
    }


# 1. Unordered trajectory match evaluator from agentevals
_trajectory_evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="unordered"
)

def trajectory_evaluator(outputs: dict, reference_outputs: dict) -> dict:
    """Compare actual message trajectory with reference trajectory."""
    actual_messages = outputs.get("messages", [])
    reference_messages = reference_outputs.get("messages", [])
    
    return _trajectory_evaluator(
        outputs=actual_messages,
        reference_outputs=reference_messages
    )


# 2. Correctness evaluator from openevals
correctness_evaluator = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,
    feedback_key="response_correctness",
    model="openai:gpt-4o-mini",
)


if __name__ == "__main__":
    # Run evaluation with 2 evaluators
    experiment_results = client.evaluate(
        ls_target,
        data="financial-portfolio-agent",
        evaluators=[
            trajectory_evaluator,
            correctness_evaluator
        ],
        max_concurrency=10,
        experiment_prefix="financial-portfolio-eval",
    )
    
    # Save config for reporting
    criteria = {
        "trajectory_unordered_match": ">=0.8",
        "response_correctness": ">=0.8"
    }
    
    output_metadata = {
        "experiment_name": experiment_results.experiment_name,
        "dataset_name": "financial-portfolio-agent",
        "criteria": criteria,
    }
    
    safe_name = experiment_results.experiment_name.replace(":", "-").replace("/", "-")
    config_filename = f"evaluation_config__{safe_name}.json"
    with open(config_filename, "w") as f:
        json.dump(output_metadata, f)

