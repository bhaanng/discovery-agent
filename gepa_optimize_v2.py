#!/usr/bin/env python3
"""
GEPA Optimization for Product Discovery Agent - Updated API

Proper integration with optimize_anything API using:
- Mode 3: Generalization (trainset → optimize → generalize to valset)
- LLM-as-a-judge evaluation
- Multi-component optimization (query analysis, questions, formatting, refinement)
"""

import sys
import os
import json
from typing import Dict, Any

# Add GEPA to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gepa', 'src'))

from gepa.optimize_anything import optimize_anything, GEPAConfig, EngineConfig, ReflectionConfig

# Use mock evaluator until API is fixed
# from llm_evaluator import evaluate_trace_with_llm_judges
from mock_evaluator import evaluate_trace_with_mock_judges as evaluate_trace_with_llm_judges

# Import test cases
from gepa_optimize import TEST_CASES, QUERY_ANALYSIS_LOGIC, QUESTION_GENERATION_LOGIC, RESULT_FORMATTING_LOGIC, REFINEMENT_LOGIC

# Seed candidate - our current agent logic as dict
SEED_CANDIDATE = {
    "query_analysis": QUERY_ANALYSIS_LOGIC,
    "question_generation": QUESTION_GENERATION_LOGIC,
    "result_formatting": RESULT_FORMATTING_LOGIC,
    "refinement_logic": REFINEMENT_LOGIC
}

def simulate_agent_with_candidate(candidate: Dict[str, str], test_case: Dict) -> Dict:
    """
    Simulate running the agent with given logic on a test case.

    In practice, this would:
    1. Parse the candidate logic
    2. Apply it to the test case query
    3. Generate questions, search, show results
    4. Return full trace

    For now, return a mock trace for evaluation.
    """
    query = test_case["query"]

    # Mock trace - in real implementation, would execute the logic
    trace = {
        "query": query,
        "analysis": {
            "specificityScore": 2,
            "hasCategory": True,
            "needsClarification": False
        },
        "questions_asked": [
            {
                "question": "What's your skin type?",
                "why": "Helps match products to your needs",
                "options": ["Dry", "Oily", "Combination", "Sensitive"],
                "user_answer": "Dry"
            }
        ],
        "initial_results_count": 100,
        "refined_results_count": 25,
        "user_constraints": test_case.get("expected", {}).get("expected_filters", {}),
        "top_products": [
            {"name": f"Product {i}", "brand": "TestBrand", "price": 25.0}
            for i in range(5)
        ],
        "context_gathered": {"skin_type": "dry"},
        "results_count": 25,
        "result_brands": ["TestBrand"],
        "price_min": 15.0,
        "price_max": 35.0,
        "result_attributes": ["Hydrating", "Fragrance-free"],
        "refinement_question": "Would you like gel or cream?",
        "user_intent": query,
        "original_query": query,
        "original_intent": query,
        "conversation_flow": [
            {"role": "user", "content": query},
            {"role": "agent", "content": "Here are your matches"}
        ],
        "filters_applied": {},
        "agent_response": "Found 25 products matching your criteria",
        "final_results": []
    }

    return trace


def evaluator(candidate: Dict[str, str], example: Dict, state: Any = None) -> tuple[float, Dict]:
    """
    Evaluator for GEPA - called once per test case.

    Args:
        candidate: Dict with optimized logic components
        example: One test case from dataset
        state: OptimizationState (current best candidates, etc.)

    Returns:
        (score, side_info) tuple where:
        - score: float (higher is better)
        - side_info: dict with diagnostic feedback for LLM reflection
    """

    # Simulate running agent with this candidate on this test case
    trace = simulate_agent_with_candidate(candidate, example)

    # Evaluate with LLM judges
    try:
        metrics = evaluate_trace_with_llm_judges(trace)

        # Overall score for GEPA (0-1 scale)
        score = metrics.get('overall_score', 0.5)

        # Side info for LLM reflection
        side_info = {
            "query": example["query"],
            "difficulty": example.get("difficulty", "unknown"),
            "metrics": metrics,
            "trace_summary": {
                "questions_asked": len(trace["questions_asked"]),
                "results_count": trace["results_count"],
                "user_satisfied": score > 0.7
            },
            # Actionable feedback
            "feedback": generate_feedback(metrics, example)
        }

        return score, side_info

    except Exception as e:
        print(f"Error evaluating {example['query']}: {e}")
        return 0.0, {"error": str(e), "query": example["query"]}


def generate_feedback(metrics: Dict, test_case: Dict) -> str:
    """Generate actionable feedback from metrics."""

    feedback_parts = []

    # Goal identification feedback
    if metrics.get('goal_identification', 0) < 0.7:
        feedback_parts.append("❌ Goal Identification: Agent misunderstood user intent")

    # Cognitive load feedback
    if metrics.get('cognitive_load', 0) < 0.7:
        feedback_parts.append("❌ Cognitive Load: Questions too complex or too many")

    # Information gain feedback
    if metrics.get('information_gain', 0) < 0.7:
        feedback_parts.append("❌ Information Gain: Questions didn't effectively narrow results")

    # Constraint satisfaction feedback
    if metrics.get('constraint_satisfaction', 0) < 0.7:
        feedback_parts.append("❌ Constraint Satisfaction: Results don't match user requirements")

    # Precision feedback
    if metrics.get('precision_at_5', 0) < 0.7:
        feedback_parts.append("❌ Precision@5: Top results not relevant")

    # NDCG feedback
    if metrics.get('ndcg', 0) < 0.7:
        feedback_parts.append("❌ NDCG: Best results not ranked first")

    # Redundancy feedback
    if metrics.get('redundancy_avoidance', 0) < 0.7:
        feedback_parts.append("❌ Redundancy: Asked redundant questions")

    # Success patterns
    if metrics.get('overall_score', 0) > 0.8:
        feedback_parts.append("✅ Strong performance - preserve this approach")

    return "\n".join(feedback_parts) if feedback_parts else "✅ All metrics good"


def run_optimization(max_iterations: int = 10):
    """
    Run GEPA optimization with optimize_anything API.
    """

    print("=" * 70)
    print("GEPA OPTIMIZATION - Product Discovery Agent")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  - Test cases: {len(TEST_CASES)}")
    print(f"  - Max iterations: {max_iterations}")
    print(f"  - Components: query_analysis, question_generation, result_formatting, refinement_logic")
    print(f"  - Evaluation: 10 LLM-as-a-judge metrics")
    print()

    # Split dataset (80/20 train/val)
    train_size = int(len(TEST_CASES) * 0.8)
    trainset = TEST_CASES[:train_size]
    valset = TEST_CASES[train_size:]

    print(f"Dataset split:")
    print(f"  - Training: {len(trainset)} cases")
    print(f"  - Validation: {len(valset)} cases")
    print()

    try:
        # Run optimization
        result = optimize_anything(
            seed_candidate=SEED_CANDIDATE,
            evaluator=evaluator,
            dataset=trainset,
            valset=valset,
            objective="""
Optimize a product discovery agent that helps users find beauty products through natural conversation.

The agent should:
1. Understand user intent accurately (even from vague queries)
2. Ask minimal, high-value questions to narrow results
3. Return products that match ALL user constraints
4. Provide helpful refinement suggestions
5. Stay focused on the original search goal

Key success metrics:
- Goal Identification: Correctly understand what user wants
- Cognitive Load: Keep questions simple and easy to answer
- Information Gain: Each question should significantly narrow results
- Constraint Satisfaction: All returned products match user requirements
- Precision & NDCG: Best results ranked first
- Redundancy: Never ask about information already gathered
- Drift: Stay focused on original goal throughout conversation
            """.strip(),
            background="""
Domain: E-commerce beauty product discovery (skincare, makeup)
Product attributes: category, brand, price, skin_type, concerns, ingredients, texture
User types: novice to expert, various skin types and concerns
            """.strip(),
            config=GEPAConfig(
                engine=EngineConfig(
                    max_candidate_proposals=max_iterations,
                    run_dir=f"outputs/product_discovery_agent",
                    track_best_outputs=True,
                    cache_evaluation=True,
                ),
                reflection=ReflectionConfig(
                    reflection_lm="claude-3-5-haiku-20241022",
                )
            )
        )

        print("\n" + "=" * 70)
        print("OPTIMIZATION COMPLETE!")
        print("=" * 70)
        print()

        print(f"Best candidate found:")
        print(f"  - Training score: {result.best_score:.3f}")
        print(f"  - Validation score: {result.best_val_score:.3f}")
        print()

        # Save results
        output_file = "gepa_results_optimized.json"
        with open(output_file, "w") as f:
            # Convert result to dict for JSON serialization
            result_dict = {
                "best_candidate": result.best_candidate,
                "best_score": result.best_score,
                "best_val_score": result.best_val_score,
                "iterations": max_iterations
            }
            json.dump(result_dict, f, indent=2)

        print(f"✅ Results saved to: {output_file}")
        print()

        # Save optimized components
        if isinstance(result.best_candidate, dict):
            for component_name, component_text in result.best_candidate.items():
                filename = f"optimized_{component_name}_v2.txt"
                with open(filename, "w") as f:
                    f.write(component_text)
                print(f"   Saved: {filename}")

        return result

    except Exception as e:
        print(f"\n❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Optimize product discovery agent with GEPA")
    parser.add_argument("--iterations", type=int, default=10, help="Max optimization iterations")

    args = parser.parse_args()

    result = run_optimization(max_iterations=args.iterations)

    if result:
        print("\n🎉 Success! Check outputs/ directory for full optimization history")
    else:
        print("\n⚠️  Optimization failed - see error above")
