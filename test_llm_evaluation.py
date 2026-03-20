#!/usr/bin/env python3
"""
Test LLM-as-a-Judge Evaluation System

Run this to see your 10 new metrics in action on sample test cases.
"""

import json
from llm_evaluator import evaluate_trace_with_llm_judges

# Sample trace for testing
sample_traces = [
    {
        "query": "I need a moisturizer",
        "analysis": {
            "specificityScore": 1,
            "hasCategory": True,
            "needsClarification": True
        },
        "questions_asked": [
            {
                "question": "What's your skin type?",
                "why": "This helps me recommend products formulated specifically for your skin's needs",
                "options": ["Dry", "Oily", "Combination", "Normal", "Sensitive"],
                "user_answer": "Dry"
            },
            {
                "question": "What's your budget?",
                "why": "Prices range from $8 to $125",
                "options": ["Under $25", "$25-$50", "$50-$100", "Luxury ($100+)"],
                "user_answer": "$25-$50"
            }
        ],
        "initial_results_count": 287,
        "refined_results_count": 23,
        "user_constraints": {
            "category": "moisturizer",
            "skin_type": "dry",
            "price_range": "$25-$50"
        },
        "top_products": [
            {"name": "CeraVe Moisturizing Cream", "brand": "CeraVe", "price": 19.99},
            {"name": "Cetaphil Daily Hydrating Lotion", "brand": "Cetaphil", "price": 15.99},
            {"name": "Neutrogena Hydro Boost", "brand": "Neutrogena", "price": 21.99},
            {"name": "La Roche-Posay Toleriane", "brand": "La Roche-Posay", "price": 24.99},
            {"name": "Aveeno Daily Moisturizing Lotion", "brand": "Aveeno", "price": 12.99}
        ],
        "context_gathered": {"skin_type": "Dry", "price_range": "$25-$50"},
        "results_count": 23,
        "result_brands": ["CeraVe", "Cetaphil", "Neutrogena", "La Roche-Posay", "Aveeno"],
        "price_min": 12.99,
        "price_max": 24.99,
        "result_attributes": ["Hydrating", "Fragrance-free", "Non-comedogenic"],
        "refinement_question": "Would you prefer a cream or lotion texture?",
        "user_intent": "Find an affordable moisturizer for dry skin",
        "original_query": "I need a moisturizer",
        "original_intent": "Find a moisturizer",
        "conversation_flow": [
            {"role": "user", "content": "I need a moisturizer"},
            {"role": "agent", "content": "What's your skin type?"},
            {"role": "user", "content": "Dry"},
            {"role": "agent", "content": "What's your budget?"},
            {"role": "user", "content": "$25-$50"}
        ],
        "filters_applied": {"skin_type": "dry", "price_max": 50},
        "agent_response": "Here are 23 moisturizers for dry skin in your budget",
        "final_results": [
            {"name": "CeraVe Moisturizing Cream", "brand": "CeraVe", "price": 19.99}
        ]
    },
    {
        "query": "hydrating moisturizer for dry sensitive skin under $50",
        "analysis": {
            "specificityScore": 4,
            "hasCategory": True,
            "needsClarification": False
        },
        "questions_asked": [],
        "initial_results_count": 45,
        "refined_results_count": 45,
        "user_constraints": {
            "category": "moisturizer",
            "benefits": ["hydrating"],
            "skin_type": "dry sensitive",
            "price_max": 50
        },
        "top_products": [
            {"name": "CeraVe Moisturizing Cream", "brand": "CeraVe", "price": 19.99},
            {"name": "La Roche-Posay Toleriane Double Repair", "brand": "La Roche-Posay", "price": 21.99},
            {"name": "Vanicream Moisturizing Cream", "brand": "Vanicream", "price": 15.99},
            {"name": "Cetaphil Moisturizing Cream", "brand": "Cetaphil", "price": 17.99},
            {"name": "Eucerin Advanced Repair", "brand": "Eucerin", "price": 12.99}
        ],
        "context_gathered": {},
        "results_count": 45,
        "result_brands": ["CeraVe", "La Roche-Posay", "Vanicream", "Cetaphil", "Eucerin"],
        "price_min": 12.99,
        "price_max": 49.99,
        "result_attributes": ["Fragrance-free", "Hypoallergenic", "Dermatologist-tested"],
        "refinement_question": "Would you like fragrance-free options only?",
        "user_intent": "Find hydrating moisturizer for dry sensitive skin under $50",
        "original_query": "hydrating moisturizer for dry sensitive skin under $50",
        "original_intent": "Find specific moisturizer",
        "conversation_flow": [
            {"role": "user", "content": "hydrating moisturizer for dry sensitive skin under $50"},
            {"role": "agent", "content": "Here are the top matches for your search"}
        ],
        "filters_applied": {"category": "moisturizer", "skin_type": "dry sensitive", "price_max": 50},
        "agent_response": "Here are 45 hydrating moisturizers for dry sensitive skin under $50",
        "final_results": [
            {"name": "CeraVe Moisturizing Cream", "brand": "CeraVe", "price": 19.99}
        ]
    }
]

def main():
    print("=" * 70)
    print("LLM-AS-A-JUDGE EVALUATION TEST")
    print("=" * 70)
    print()
    print("Testing your 10 new metrics on sample traces...")
    print()

    all_results = []

    for i, trace in enumerate(sample_traces, 1):
        print(f"\n{'=' * 70}")
        print(f"TEST CASE {i}: {trace['query']}")
        print(f"{'=' * 70}\n")

        # Evaluate with LLM judges
        metrics = evaluate_trace_with_llm_judges(trace)

        # Store results
        result = {
            "query": trace["query"],
            "metrics": metrics
        }
        all_results.append(result)

        # Print summary
        print(f"\n{'─' * 70}")
        print(f"RESULTS FOR: {trace['query'][:50]}...")
        print(f"{'─' * 70}")
        print(f"  Overall Score:           {metrics.get('overall_score', 0):.2f}")
        print(f"  Goal Identification:     {metrics.get('goal_identification', 0):.2f}")
        print(f"  Cognitive Load:          {metrics.get('cognitive_load', 0):.2f}")
        print(f"  Information Gain:        {metrics.get('information_gain', 0):.2f}")
        print(f"  Redundancy Avoidance:    {metrics.get('redundancy_avoidance', 0):.2f}")
        print(f"  Constraint Satisfaction: {metrics.get('constraint_satisfaction', 0):.2f}")
        print(f"  Precision@5:             {metrics.get('precision_at_5', 0):.2f}")
        print(f"  NDCG:                    {metrics.get('ndcg', 0):.2f}")
        print(f"  Zero Results Handling:   {metrics.get('zero_results_handling', 0):.2f}")
        print(f"  Refinement Quality:      {metrics.get('refinement_quality', 0):.2f}")
        print(f"  Drift Avoidance:         {metrics.get('drift_avoidance', 0):.2f}")
        print()

    # Save results
    with open("llm_evaluation_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE!")
    print("=" * 70)
    print(f"\n✅ Evaluated {len(sample_traces)} test cases")
    print(f"📊 Results saved to: llm_evaluation_results.json")
    print()

    # Calculate averages
    avg_metrics = {}
    for metric_name in all_results[0]["metrics"].keys():
        avg_metrics[metric_name] = sum(r["metrics"][metric_name] for r in all_results) / len(all_results)

    print("📈 AVERAGE SCORES ACROSS ALL TEST CASES:")
    print("─" * 70)
    for metric, score in sorted(avg_metrics.items()):
        print(f"  {metric:30s}: {score:.2f}")

    print("\n" + "=" * 70)
    print("\nNext steps:")
    print("  1. Review llm_evaluation_results.json for detailed scores")
    print("  2. Add more test cases to sample_traces")
    print("  3. Use these metrics to manually iterate on agent logic")
    print("  4. Once GEPA is available, integrate for automatic optimization")
    print()

if __name__ == "__main__":
    main()
