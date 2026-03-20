#!/usr/bin/env python3
"""
GEPA Optimization for Product Discovery Agent

This script optimizes the agent's decision logic and prompts using GEPA framework.
"""

import json
from typing import Dict, List, Any
from gepa import optimize_anything

# Test cases with expected behaviors - COMPREHENSIVE for better GEPA learning
# 25 test cases covering intent, ingredients, context, safety, and edge cases
TEST_CASES = [
    # --- 1. BROAD QUERY ---
    {
        "query": "I need skincare",
        "difficulty": "hard",
        "expected": {
            "should_clarify": True,
            "max_questions": 3,
            "should_search_immediately": False,
            "expected_question_topics": ["product_category", "skin_type", "concern"]
        },
        "ideal_outcome": {"turns": 4, "relevance": 8.5, "satisfaction": True}
    },

    # --- 2. OVER-SPECIFIC ---
    {
        "query": "hydrating moisturizer for dry sensitive skin under $50",
        "difficulty": "easy",
        "expected": {
            "should_clarify": False,
            "should_search_immediately": True,
            "expected_filters": {
                "category": "moisturizer",
                "benefits": ["hydrating"],
                "skin_type": "dry sensitive",
                "price_max": 50
            }
        },
        "ideal_outcome": {"turns": 2, "relevance": 9.5, "satisfaction": True}
    },

    # --- 3. AMBIGUOUS INTENT ---
    {
        "query": "something for my face that glows",
        "difficulty": "hard",
        "expected": {
            "should_clarify": True,
            "clarify_first": "intent",  # makeup vs skincare
            "max_questions": 2
        },
        "ideal_outcome": {"turns": 3, "relevance": 8.0, "satisfaction": True}
    },

    # --- 4. BRAND-SPECIFIC ---
    {
        "query": "Clinique moisturizer",
        "difficulty": "medium",
        "expected": {
            "should_search_immediately": True,
            "expected_filters": {"brand": "Clinique", "category": "moisturizer"},
            "post_search_refinement": True
        },
        "ideal_outcome": {"turns": 3, "relevance": 9.0, "satisfaction": True}
    },

    # --- 5. PRICE-FOCUSED ---
    {
        "query": "affordable face cream",
        "difficulty": "medium",
        "expected": {
            "should_clarify": True,
            "expected_question_topics": ["price_range", "skin_type", "concern"]
        },
        "ideal_outcome": {"turns": 4, "relevance": 8.0, "satisfaction": True}
    },

    # --- 6. CONTRADICTORY REQUIREMENTS ---
    {
        "query": "luxury anti-aging serum under $15",
        "difficulty": "edge_case",
        "expected": {
            "should_clarify": True,
            "clarify_first": "priority",  # luxury OR budget?
            "handle_contradiction": True
        },
        "ideal_outcome": {"turns": 3, "relevance": 7.0, "satisfaction": True}
    },

    # --- 7. INFORMAL/MISSPELLED ---
    {
        "query": "moisterizer for acnee prone skin",
        "difficulty": "medium",
        "expected": {
            "should_search_immediately": True,
            "infer_intent": "moisturizer for acne prone skin"
        },
        "ideal_outcome": {"turns": 2, "relevance": 8.5, "satisfaction": True}
    },

    # --- 8. NEGATIVE CONSTRAINTS ---
    {
        "query": "face cream without fragrance or parabens",
        "difficulty": "medium",
        "expected": {
            "should_search_immediately": True,
            "expected_filters": {"category": "face cream", "exclude": ["fragrance", "parabens"]}
        },
        "ideal_outcome": {"turns": 2, "relevance": 8.0, "satisfaction": True}
    },

    # --- 9. MULTI-PRODUCT ---
    {
        "query": "cleanser and moisturizer for sensitive skin",
        "difficulty": "medium",
        "expected": {
            "should_clarify": True,
            "clarify_first": "prioritization",
            "handle_multiple_products": True
        },
        "ideal_outcome": {"turns": 4, "relevance": 8.5, "satisfaction": True}
    },

    # --- 10. CONTEXT-DEPENDENT ---
    {
        "query": "something for after the gym",
        "difficulty": "hard",
        "expected": {
            "should_clarify": True,
            "infer_use_case": "post-workout",
            "expected_question_topics": ["product_type", "skin_concerns"]
        },
        "ideal_outcome": {"turns": 4, "relevance": 7.5, "satisfaction": True}
    },

    # --- 11. TECHNICAL COMPARISON ---
    {
        "query": "Should I use 2% BHA or a 10% AHA peel for closed comedones?",
        "difficulty": "medium",
        "expected": {
            "should_clarify": True,
            "clarify_first": "skin_sensitivity",
            "expected_topics": ["current_routine", "skin_type"]
        },
        "ideal_outcome": {"turns": 3, "relevance": 9.0, "satisfaction": True}
    },

    # --- 12. SAFETY/INTERACTION ---
    {
        "query": "Can I use Tretinoin and then put on a high-strength Vitamin C serum?",
        "difficulty": "edge_case",
        "expected": {
            "should_clarify": False,
            "must_include_warning": True,
            "safety_logic": "contraindication_check"
        },
        "ideal_outcome": {"turns": 1, "relevance": 10.0, "satisfaction": True}
    },

    # --- 13. BRAND DUPE ---
    {
        "query": "Glossier Milky Jelly dupe but drugstore price",
        "difficulty": "medium",
        "expected": {
            "should_search_immediately": True,
            "expected_filters": {"texture": "jelly", "price_max": 15}
        },
        "ideal_outcome": {"turns": 2, "relevance": 9.5, "satisfaction": True}
    },

    # --- 14. CLIMATE INFERENCE ---
    {
        "query": "I'm going to Iceland in December, what do I need for my face?",
        "difficulty": "hard",
        "expected": {
            "should_clarify": True,
            "infer_climate": "cold_dry",
            "expected_question_topics": ["skin_type"]
        },
        "ideal_outcome": {"turns": 3, "relevance": 8.5, "satisfaction": True}
    },

    # --- 15. SENSORY CONSTRAINTS ---
    {
        "query": "skincare for someone with 30 seconds who hates the feeling of lotion",
        "difficulty": "hard",
        "expected": {
            "should_search_immediately": True,
            "exclude_textures": ["heavy_cream"],
            "prefer_formats": ["mist", "gel", "stick"]
        },
        "ideal_outcome": {"turns": 2, "relevance": 9.0, "satisfaction": True}
    },

    # --- 16. MEDICAL CONDITION ---
    {
        "query": "What can I use for my cystic hormonal acne on my jawline?",
        "difficulty": "hard",
        "expected": {
            "should_clarify": False,
            "must_include_disclaimer": True,
            "suggest_targeted_ingredients": ["benzoyl_peroxide", "adapalene"]
        },
        "ideal_outcome": {"turns": 2, "relevance": 8.0, "satisfaction": True}
    },

    # --- 17. PREGNANCY SAFETY ---
    {
        "query": "Is my anti-aging routine safe now that I'm pregnant?",
        "difficulty": "hard",
        "expected": {
            "should_clarify": True,
            "clarify_first": "product_list",
            "must_flag_retinoids": True
        },
        "ideal_outcome": {"turns": 3, "relevance": 10.0, "satisfaction": True}
    },

    # --- 18. AGE-SPECIFIC ---
    {
        "query": "Skincare for a 13-year-old just starting out",
        "difficulty": "medium",
        "expected": {
            "should_clarify": True,
            "limit_to_basics": True,
            "exclude_harsh_actives": True
        },
        "ideal_outcome": {"turns": 2, "relevance": 9.0, "satisfaction": True}
    },

    # --- 19. SEASONAL TRANSITION ---
    {
        "query": "It's getting humid and my winter cream is starting to feel greasy",
        "difficulty": "medium",
        "expected": {
            "should_search_immediately": True,
            "logic": "texture_pivot",
            "suggest_formats": ["gel_cream"]
        },
        "ideal_outcome": {"turns": 2, "relevance": 9.0, "satisfaction": True}
    },

    # --- 20. HYPER-TECHNICAL ---
    {
        "query": "Vitamin C serum with at least 15% L-Ascorbic Acid and Vitamin E",
        "difficulty": "medium",
        "expected": {
            "should_search_immediately": True,
            "expected_filters": {"min_concentration": 15, "ingredients": ["Vitamin E"]}
        },
        "ideal_outcome": {"turns": 1, "relevance": 10.0, "satisfaction": True}
    },

    # --- 21. EMERGENCY ---
    {
        "query": "I have a huge red pimple and a wedding tomorrow, help!!",
        "difficulty": "hard",
        "expected": {
            "should_clarify": False,
            "priority": "fast_acting",
            "suggest_products": ["pimple_patch"]
        },
        "ideal_outcome": {"turns": 1, "relevance": 9.5, "satisfaction": True}
    },

    # --- 22. OUT-OF-DOMAIN ---
    {
        "query": "how to fix a cracked screen on my phone",
        "difficulty": "easy",
        "expected": {
            "should_clarify": False,
            "handle_out_of_domain": True,
            "should_search_immediately": False
        },
        "ideal_outcome": {"turns": 1, "relevance": 10.0, "satisfaction": True}
    },

    # --- 23. INCLUSIVITY ---
    {
        "query": "sunscreen that won't leave a white cast on darker skin tones",
        "difficulty": "medium",
        "expected": {
            "should_search_immediately": True,
            "filter_logic": "no_white_cast",
            "prefer_formats": ["chemical", "tinted"]
        },
        "ideal_outcome": {"turns": 2, "relevance": 9.5, "satisfaction": True}
    },

    # --- 24. PROCEDURAL ---
    {
        "query": "I have an oil cleanser, a toner, and a moisturizer. What order?",
        "difficulty": "easy",
        "expected": {
            "should_clarify": False,
            "provide_sequence": True,
            "expected_order": ["oil cleanser", "toner", "moisturizer"]
        },
        "ideal_outcome": {"turns": 1, "relevance": 10.0, "satisfaction": True}
    },

    # --- 25. HYBRID NEEDS ---
    {
        "query": "I want a moisturizer that also has high SPF",
        "difficulty": "easy",
        "expected": {
            "should_search_immediately": True,
            "expected_filters": {"category": "moisturizer", "min_spf": 30}
        },
        "ideal_outcome": {"turns": 1, "relevance": 10.0, "satisfaction": True}
    }
]

# Current agent logic as text artifacts
QUERY_ANALYSIS_LOGIC = """
Analyze query specificity by scoring:
1. Check for product category (moisturizer, serum, cleanser, etc.)
2. Count specific details:
   - Brand names: +2 points (clinique, cerave, etc.)
   - Skin type: +1 point (dry, oily, combination, sensitive, normal)
   - Concerns/benefits: +1 point (hydration, anti-aging, acne, brightening, etc.)
   - Price indicators: +1 point ($, cheap, affordable, luxury, budget)
   - Formulation: +1 point (gel, cream, oil-free, lightweight, rich, thick)
   - Ingredients: +1 point (hyaluronic, retinol, vitamin, peptide, niacinamide, etc.)

Decision rules:
- Query is SPECIFIC if score >= 2
- Query NEEDS CLARIFICATION if has category AND score < 2
- Query is TOO VAGUE if no category AND score < 2

Return: {isSpecific: bool, hasCategory: bool, needsClarification: bool, specificityScore: int}
"""

QUESTION_GENERATION_LOGIC = """
Generate 2-3 clarifying questions based on:

Priority 1: Category identification (if missing)
- "What type of product are you looking for?"
- Options: based on common categories

Priority 2: Data-driven questions from search results
- Extract unique brands from results (top 5)
- Calculate price range from results
- Identify common attributes/highlights

Priority 3: User profile
- Skin type (if skincare)
- Primary concern
- Budget/price preference

Question format:
{
  question: "Clear question text",
  why: "Explanation of why this matters (information value)",
  options: ["Option1", "Option2", ..., "No preference"]
}

Rules:
- Maximum 3 questions at once
- Each question should reduce result set by >30%
- Provide "No preference" or "Show all" option
- Never repeat questions in same session
"""

RESULT_FORMATTING_LOGIC = """
Format search results with context:

1. Build explanation based on gathered filters:
   - If brand selected: mention brand
   - If price range selected: mention price
   - If concern selected: mention concern

2. Template: "Based on your preferences for {criteria}, here are the top matches"

3. Show top 6 products with:
   - Product name
   - Brand name
   - Price
   - Image
   - Short description
   - Rating (if available)

4. Add result count: "({N} products found)"
"""

REFINEMENT_LOGIC = """
After showing results, generate ONE data-driven follow-up question:

Analyze current results to find the most valuable refinement axis:

1. Brand diversity check:
   - If 3+ brands present AND not yet filtered: ask brand preference
   - Show actual brands from results

2. Price spread check:
   - If price range > $30 AND not yet filtered: ask budget
   - Show actual price ranges from results

3. Attribute diversity check:
   - If multiple common highlights: ask about priorities
   - Show actual attributes from results

4. Formulation diversity:
   - If multiple texture types: ask preference
   - Options: Cream, Gel, Lotion, Oil, Serum, No preference

Priority order: brand > price > attributes > formulation

Don't ask if:
- Already filtered on that dimension
- Results count < 10 (already narrow enough)
- All products very similar
"""


def evaluate_agent_trace(query: str, trace: Dict[str, Any]) -> Dict[str, float]:
    """
    Evaluate agent performance on a single query.

    Returns multiple objectives for Pareto optimization:
    - turns_to_success: Number of conversation turns (minimize)
    - relevance_score: Product match quality 0-10 (maximize)
    - question_efficiency: Quality of questions asked 0-1 (maximize)
    - user_satisfied: Binary outcome (maximize)
    """

    # Extract metrics from trace
    turns = trace.get("turns_to_success", 10)  # default penalty

    # Calculate relevance (would need actual product evaluation)
    relevance = trace.get("relevance_score", 5.0)

    # Calculate question efficiency
    questions_asked = trace.get("questions_asked", [])
    if questions_asked:
        # Measure if questions reduced result set effectively
        efficiency = sum(q.get("information_gain", 0.5) for q in questions_asked) / len(questions_asked)
    else:
        efficiency = 1.0 if turns <= 2 else 0.5

    # User satisfaction (simulated or actual)
    satisfied = trace.get("user_satisfied", False)

    return {
        "turns_to_success": turns,  # minimize
        "relevance_score": relevance,  # maximize (0-10)
        "question_efficiency": efficiency,  # maximize (0-1)
        "user_satisfied": 1.0 if satisfied else 0.0  # maximize
    }


def run_optimization(
    max_iterations: int = 100,
    task_model: str = "claude-3-5-sonnet-20241022",
    reflection_model: str = "claude-3-5-haiku-20241022"
):
    """
    Run GEPA optimization on agent logic.
    """

    print("🚀 Starting GEPA optimization with Claude models...")
    print(f"   Task model: {task_model}")
    print(f"   Reflection model: {reflection_model}")
    print(f"   Max iterations: {max_iterations}")
    print(f"   Test cases: {len(TEST_CASES)}")
    print(f"   Estimated cost: ${max_iterations * 0.0158:.2f}")
    print()

    # Define artifacts to optimize
    artifacts = [
        {
            "name": "query_analysis",
            "content": QUERY_ANALYSIS_LOGIC,
            "type": "decision_logic"
        },
        {
            "name": "question_generation",
            "content": QUESTION_GENERATION_LOGIC,
            "type": "prompt"
        },
        {
            "name": "result_formatting",
            "content": RESULT_FORMATTING_LOGIC,
            "type": "prompt"
        },
        {
            "name": "refinement_logic",
            "content": REFINEMENT_LOGIC,
            "type": "decision_logic"
        }
    ]

    # Run optimization
    result = optimize_anything(
        seed_artifacts=artifacts,
        train_examples=TEST_CASES,
        evaluator=evaluate_agent_trace,
        objectives=[
            {"name": "turns_to_success", "direction": "minimize", "weight": 0.3},
            {"name": "relevance_score", "direction": "maximize", "weight": 0.4},
            {"name": "user_satisfied", "direction": "maximize", "weight": 0.3}
        ],
        max_iterations=max_iterations,
        task_model=task_model,
        reflection_model=reflection_model,
        population_size=10,
        verbose=True
    )

    print("\n✨ Optimization complete!")
    print(f"   Iterations: {result['iterations_used']}")
    print(f"   Best solutions: {len(result['pareto_frontier'])}")
    print()

    # Save results
    with open("gepa_results.json", "w") as f:
        json.dump(result, f, indent=2)

    print("📊 Results saved to gepa_results.json")

    # Extract best solution
    best = result.get_best_by_weights({
        "turns_to_success": 0.3,
        "relevance_score": 0.4,
        "user_satisfied": 0.3
    })

    print("\n🏆 Best solution (weighted):")
    print(f"   Turns: {best['metrics']['turns_to_success']:.1f}")
    print(f"   Relevance: {best['metrics']['relevance_score']:.1f}/10")
    print(f"   Satisfaction: {best['metrics']['user_satisfied']*100:.1f}%")
    print()

    # Save optimized artifacts
    for artifact in best['artifacts']:
        filename = f"optimized_{artifact['name']}.txt"
        with open(filename, "w") as f:
            f.write(artifact['content'])
        print(f"   Saved: {filename}")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Optimize product discovery agent with GEPA")
    parser.add_argument("--iterations", type=int, default=100, help="Max optimization iterations")
    parser.add_argument("--task-model", default="claude-3-5-sonnet-20241022", help="Model for agent execution")
    parser.add_argument("--reflection-model", default="claude-3-5-haiku-20241022", help="Model for trace analysis")

    args = parser.parse_args()

    run_optimization(
        max_iterations=args.iterations,
        task_model=args.task_model,
        reflection_model=args.reflection_model
    )
