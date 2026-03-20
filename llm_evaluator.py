#!/usr/bin/env python3
"""
LLM-as-a-Judge Evaluator for Product Discovery Agent

Uses Claude to evaluate agent performance across multiple dimensions:
- Goal Identification
- Cognitive Load
- Information Gain
- Question Redundancy
- Search Quality (Constraint Satisfaction, Precision@5, NDCG, Zero Results)
- Refinement Quality
- Drift Detection
"""

import os
import json
from typing import Dict, List, Any
from anthropic import Anthropic

# Initialize Claude client
client = Anthropic(
    api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"),
    base_url=os.getenv("ANTHROPIC_BEDROCK_BASE_URL")
)

# === LLM JUDGE PROMPTS ===

GOAL_IDENTIFICATION_PROMPT = """
You are evaluating a product discovery agent's ability to identify user intent.

## Trace
User Query: {query}
Agent Analysis: {analysis}
Questions Asked: {questions}

## Task
Did the agent correctly identify the user's goal/intent?

Score 0-10:
- 10: Perfectly understood intent, asked relevant clarifying questions
- 7-9: Good understanding, minor gaps
- 4-6: Partial understanding, missed key intent elements
- 1-3: Misunderstood intent, asked irrelevant questions
- 0: Completely missed the point

## Output Format (JSON)
{{
    "score": <0-10>,
    "reasoning": "<brief explanation>",
    "missed_intents": ["<list any missed elements>"]
}}
"""

COGNITIVE_LOAD_PROMPT = """
You are evaluating cognitive load - how difficult it was for the user to answer questions.

## Trace
Questions Asked:
{questions}

## Task
Rate the cognitive load (friction) for the user.

Evaluate:
1. Question complexity: Are questions simple and clear?
2. Number of options: Too many choices = higher cognitive load
3. Question sequencing: Logical flow or random?
4. Context provided: Does each question explain WHY it matters?

Score 0-10 (higher = LOWER cognitive load = better):
- 10: Effortless, clear questions with 3-5 options each
- 7-9: Mostly easy, some questions could be clearer
- 4-6: Medium effort, too many options or unclear questions
- 1-3: High effort, confusing or overwhelming
- 0: Extremely difficult to answer

## Output Format (JSON)
{{
    "score": <0-10>,
    "reasoning": "<brief explanation>",
    "friction_points": ["<list specific issues>"]
}}
"""

INFORMATION_GAIN_PROMPT = """
You are evaluating information gain per question - did the agent ask the most important questions first?

## Trace
Original Query: {query}
Initial Search Results: {initial_results} products found
Questions Asked (in order):
{questions}

After Answers:
Refined Results: {refined_results} products found

## Task
Evaluate if questions maximally narrowed the catalog.

For each question, assess:
1. Did it reduce result set significantly? (>30% reduction)
2. Was it the MOST important filter at that stage?
3. Could a better question have been asked?

Score 0-10:
- 10: Perfect prioritization, each question cut results by 50%+
- 7-9: Good questions, significant narrowing
- 4-6: Some useful questions, some trivial ones
- 1-3: Mostly trivial questions, minimal impact
- 0: Questions had no impact on results

## Output Format (JSON)
{{
    "score": <0-10>,
    "reasoning": "<brief explanation>",
    "question_impacts": [
        {{"question": "<text>", "reduction": "<percentage>", "priority": "<high|medium|low>"}}
    ]
}}
"""

REDUNDANCY_PROMPT = """
You are detecting redundant questions - did the agent avoid asking about information already gathered?

## Trace
Original Query: {query}
Context Gathered: {context}
Questions Asked:
{questions}

## Task
Identify redundant questions.

A question is redundant if:
1. Answer was in original query (e.g., user said "moisturizer", agent asks "what product type?")
2. Already answered earlier in conversation
3. Can be inferred from context (e.g., "dry skin" → don't need to ask if they need hydration)

Score 0-10 (higher = less redundancy = better):
- 10: Zero redundancy, all questions added new information
- 7-9: One minor redundancy
- 4-6: 2-3 redundant questions
- 1-3: Multiple redundancies
- 0: Mostly redundant questions

## Output Format (JSON)
{{
    "score": <0-10>,
    "reasoning": "<brief explanation>",
    "redundant_questions": ["<list redundant questions with explanation>"]
}}
"""

CONSTRAINT_SATISFACTION_PROMPT = """
You are evaluating constraint satisfaction - do search results match user requirements?

## Trace
User Requirements:
{constraints}

Top 5 Products Returned:
{top_products}

## Task
Check if each product satisfies ALL user constraints.

Constraints to check:
- Brand (if specified)
- Price range (if specified)
- Product type/category
- Skin type/concern
- Ingredients (include/exclude)
- Other specific requirements

Score 0-10:
- 10: All 5 products satisfy ALL constraints
- 8: 4/5 products satisfy all constraints
- 6: 3/5 products satisfy all constraints
- 4: 2/5 products satisfy all constraints
- 2: 1/5 products satisfy all constraints
- 0: 0/5 products satisfy all constraints

## Output Format (JSON)
{{
    "score": <0-10>,
    "reasoning": "<brief explanation>",
    "product_matches": [
        {{"product": "<name>", "satisfies": <true|false>, "violations": ["<constraints violated>"]}}
    ]
}}
"""

PRECISION_AT_5_PROMPT = """
You are evaluating Precision@5 - are the top 5 results relevant to user intent?

## Trace
User Intent: {intent}
User Query: {query}
User Constraints: {constraints}

Top 5 Products:
{top_products}

## Task
For each product, determine if it's RELEVANT to user's search intent.

Relevant = matches product type, addresses user needs, fits constraints
Not Relevant = wrong product type, doesn't match needs, violates constraints

Precision@5 = (# relevant products in top 5) / 5

## Output Format (JSON)
{{
    "precision_at_5": <0.0-1.0>,
    "relevant_count": <0-5>,
    "reasoning": "<brief explanation>",
    "product_relevance": [
        {{"product": "<name>", "relevant": <true|false>, "reason": "<why>"}}
    ]
}}
"""

NDCG_PROMPT = """
You are calculating NDCG (Normalized Discounted Cumulative Gain) - are the BEST results ranked first?

## Trace
User Intent: {intent}
User Query: {query}
Top 10 Products (in order):
{top_products}

## Task
1. Assign relevance score to each product (0-3):
   - 3: Perfect match (exactly what user wants)
   - 2: Good match (relevant, fits criteria)
   - 1: Acceptable (somewhat relevant)
   - 0: Not relevant

2. Calculate DCG = sum of (relevance / log2(position + 1))
3. Calculate IDCG (ideal DCG with perfect ranking)
4. NDCG = DCG / IDCG

## Output Format (JSON)
{{
    "ndcg": <0.0-1.0>,
    "dcg": <float>,
    "idcg": <float>,
    "reasoning": "<brief explanation>",
    "product_relevance_scores": [
        {{"product": "<name>", "position": <int>, "relevance": <0-3>, "reason": "<why>"}}
    ]
}}
"""

ZERO_RESULTS_PROMPT = """
You are detecting zero-result scenarios and evaluating how they were handled.

## Trace
Query: {query}
Filters Applied: {filters}
Results Count: {results_count}

Agent Response: {agent_response}

## Task
If results_count == 0, evaluate:
1. Was it avoidable? (filters too strict)
2. Did agent suggest loosening constraints?
3. Did agent provide helpful alternatives?

Score 0-10:
- 10: No zero results, or handled perfectly with smart suggestions
- 7-9: Zero results but good recovery (suggested alternatives)
- 4-6: Zero results, partial recovery
- 1-3: Zero results, poor recovery
- 0: Zero results, no recovery attempt

## Output Format (JSON)
{{
    "score": <0-10>,
    "had_zero_results": <true|false>,
    "avoidable": <true|false>,
    "reasoning": "<brief explanation>",
    "recovery_actions": ["<list what agent did to recover>"]
}}
"""

REFINEMENT_QUALITY_PROMPT = """
You are evaluating refinement quality - did the agent suggest logical next steps?

## Trace
Initial Results Shown: {results_count} products
Product Diversity:
- Brands: {brands}
- Price range: ${price_min}-${price_max}
- Attributes: {attributes}

Refinement Question Asked: {refinement_question}

## Task
Evaluate if the refinement question makes sense given the results.

Good refinement:
- Targets the dimension with most diversity (many brands → ask brand preference)
- Helps user narrow down without being overwhelmed
- Relevant to user's decision-making process

Score 0-10:
- 10: Perfect refinement, targets most valuable dimension
- 7-9: Good refinement, helpful narrowing
- 4-6: Okay refinement, not optimal
- 1-3: Poor refinement, not helpful
- 0: No refinement offered when needed, or irrelevant question

## Output Format (JSON)
{{
    "score": <0-10>,
    "reasoning": "<brief explanation>",
    "optimal_refinement": "<what would have been the best question>",
    "asked_refinement": "<what was actually asked>"
}}
"""

DRIFT_DETECTION_PROMPT = """
You are detecting intent drift - did the agent stay focused on the original goal?

## Trace
Original Query: {original_query}
Original Intent: {original_intent}

Conversation Flow:
{conversation}

Final Results: {final_results}

## Task
Check if the agent drifted from the original intent.

Drift indicators:
- Asking about unrelated product categories
- Suggesting products that don't match original need
- Getting sidetracked by tangential questions
- Final results don't address original query

Score 0-10 (higher = less drift = better):
- 10: Perfect focus, stayed on track throughout
- 7-9: Minor tangent but recovered
- 4-6: Moderate drift, partially off-track
- 1-3: Significant drift, mostly off-track
- 0: Complete drift, no relation to original query

## Output Format (JSON)
{{
    "score": <0-10>,
    "reasoning": "<brief explanation>",
    "drift_detected": <true|false>,
    "drift_points": ["<list where drift occurred>"]
}}
"""


# === LLM EVALUATION FUNCTIONS ===

def llm_judge(prompt: str, model: str = "claude-3-5-haiku-20241022") -> Dict[str, Any]:
    """Call Claude to evaluate with given prompt."""
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON from response
        content = response.content[0].text
        # Find JSON block
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "{" in content:
            # Try to extract JSON directly
            start = content.index("{")
            end = content.rindex("}") + 1
            json_str = content[start:end]
        else:
            raise ValueError("No JSON found in response")

        return json.loads(json_str)

    except Exception as e:
        print(f"LLM judge error: {e}")
        return {"score": 5.0, "reasoning": f"Error: {str(e)}"}


def evaluate_goal_identification(trace: Dict) -> float:
    """Evaluate if agent identified user's goal/intent."""
    prompt = GOAL_IDENTIFICATION_PROMPT.format(
        query=trace.get('query', ''),
        analysis=json.dumps(trace.get('analysis', {}), indent=2),
        questions=json.dumps(trace.get('questions_asked', []), indent=2)
    )
    result = llm_judge(prompt)
    return result.get('score', 5.0) / 10.0  # Normalize to 0-1


def evaluate_cognitive_load(trace: Dict) -> float:
    """Evaluate cognitive load (friction) for user."""
    prompt = COGNITIVE_LOAD_PROMPT.format(
        questions=json.dumps(trace.get('questions_asked', []), indent=2)
    )
    result = llm_judge(prompt)
    return result.get('score', 5.0) / 10.0  # Normalize to 0-1


def evaluate_information_gain(trace: Dict) -> float:
    """Evaluate information gain per question."""
    prompt = INFORMATION_GAIN_PROMPT.format(
        query=trace.get('query', ''),
        initial_results=trace.get('initial_results_count', 0),
        questions=json.dumps(trace.get('questions_asked', []), indent=2),
        refined_results=trace.get('refined_results_count', 0)
    )
    result = llm_judge(prompt)
    return result.get('score', 5.0) / 10.0  # Normalize to 0-1


def evaluate_redundancy(trace: Dict) -> float:
    """Evaluate if agent avoided redundant questions."""
    prompt = REDUNDANCY_PROMPT.format(
        query=trace.get('query', ''),
        context=json.dumps(trace.get('context_gathered', {}), indent=2),
        questions=json.dumps(trace.get('questions_asked', []), indent=2)
    )
    result = llm_judge(prompt)
    return result.get('score', 5.0) / 10.0  # Normalize to 0-1


def evaluate_constraint_satisfaction(trace: Dict) -> float:
    """Evaluate if results satisfy user constraints."""
    prompt = CONSTRAINT_SATISFACTION_PROMPT.format(
        constraints=json.dumps(trace.get('user_constraints', {}), indent=2),
        top_products=json.dumps(trace.get('top_products', [])[:5], indent=2)
    )
    result = llm_judge(prompt)
    return result.get('score', 5.0) / 10.0  # Normalize to 0-1


def evaluate_precision_at_5(trace: Dict) -> float:
    """Evaluate Precision@5."""
    prompt = PRECISION_AT_5_PROMPT.format(
        intent=trace.get('user_intent', ''),
        query=trace.get('query', ''),
        constraints=json.dumps(trace.get('user_constraints', {}), indent=2),
        top_products=json.dumps(trace.get('top_products', [])[:5], indent=2)
    )
    result = llm_judge(prompt)
    return result.get('precision_at_5', 0.5)


def evaluate_ndcg(trace: Dict) -> float:
    """Evaluate NDCG (Normalized Discounted Cumulative Gain)."""
    prompt = NDCG_PROMPT.format(
        intent=trace.get('user_intent', ''),
        query=trace.get('query', ''),
        top_products=json.dumps(trace.get('top_products', [])[:10], indent=2)
    )
    result = llm_judge(prompt)
    return result.get('ndcg', 0.5)


def evaluate_zero_results(trace: Dict) -> float:
    """Evaluate zero-result handling."""
    prompt = ZERO_RESULTS_PROMPT.format(
        query=trace.get('query', ''),
        filters=json.dumps(trace.get('filters_applied', {}), indent=2),
        results_count=trace.get('results_count', 0),
        agent_response=trace.get('agent_response', '')
    )
    result = llm_judge(prompt)
    return result.get('score', 5.0) / 10.0  # Normalize to 0-1


def evaluate_refinement_quality(trace: Dict) -> float:
    """Evaluate quality of post-search refinement."""
    prompt = REFINEMENT_QUALITY_PROMPT.format(
        results_count=trace.get('results_count', 0),
        brands=json.dumps(trace.get('result_brands', []), indent=2),
        price_min=trace.get('price_min', 0),
        price_max=trace.get('price_max', 0),
        attributes=json.dumps(trace.get('result_attributes', []), indent=2),
        refinement_question=trace.get('refinement_question', '')
    )
    result = llm_judge(prompt)
    return result.get('score', 5.0) / 10.0  # Normalize to 0-1


def evaluate_drift(trace: Dict) -> float:
    """Evaluate intent drift across conversation."""
    prompt = DRIFT_DETECTION_PROMPT.format(
        original_query=trace.get('original_query', ''),
        original_intent=trace.get('original_intent', ''),
        conversation=json.dumps(trace.get('conversation_flow', []), indent=2),
        final_results=json.dumps(trace.get('final_results', []), indent=2)
    )
    result = llm_judge(prompt)
    return result.get('score', 5.0) / 10.0  # Normalize to 0-1


# === COMPREHENSIVE EVALUATOR ===

def evaluate_trace_with_llm_judges(trace: Dict) -> Dict[str, float]:
    """
    Evaluate agent trace using LLM judges across all dimensions.

    Returns dictionary with normalized scores (0-1) for each metric.
    """

    print(f"📊 Evaluating trace: {trace.get('query', 'unknown')[:50]}...")

    metrics = {}

    # 1. Goal Identification
    print("  - Goal identification...")
    metrics['goal_identification'] = evaluate_goal_identification(trace)

    # 2. Cognitive Load
    print("  - Cognitive load...")
    metrics['cognitive_load'] = evaluate_cognitive_load(trace)

    # 3. Information Gain
    print("  - Information gain...")
    metrics['information_gain'] = evaluate_information_gain(trace)

    # 4. Redundancy Avoidance
    print("  - Redundancy check...")
    metrics['redundancy_avoidance'] = evaluate_redundancy(trace)

    # 5. Constraint Satisfaction
    print("  - Constraint satisfaction...")
    metrics['constraint_satisfaction'] = evaluate_constraint_satisfaction(trace)

    # 6. Precision@5
    print("  - Precision@5...")
    metrics['precision_at_5'] = evaluate_precision_at_5(trace)

    # 7. NDCG
    print("  - NDCG...")
    metrics['ndcg'] = evaluate_ndcg(trace)

    # 8. Zero Results Handling
    print("  - Zero results handling...")
    metrics['zero_results_handling'] = evaluate_zero_results(trace)

    # 9. Refinement Quality
    print("  - Refinement quality...")
    metrics['refinement_quality'] = evaluate_refinement_quality(trace)

    # 10. Drift Detection
    print("  - Drift detection...")
    metrics['drift_avoidance'] = evaluate_drift(trace)

    # Calculate overall score (weighted average)
    weights = {
        'goal_identification': 0.15,
        'cognitive_load': 0.10,
        'information_gain': 0.15,
        'redundancy_avoidance': 0.10,
        'constraint_satisfaction': 0.15,
        'precision_at_5': 0.10,
        'ndcg': 0.10,
        'zero_results_handling': 0.05,
        'refinement_quality': 0.05,
        'drift_avoidance': 0.05
    }

    overall_score = sum(metrics[k] * weights[k] for k in weights.keys())
    metrics['overall_score'] = overall_score

    print(f"✅ Overall score: {overall_score:.2f}")
    print()

    return metrics


# === USAGE EXAMPLE ===

if __name__ == "__main__":
    # Example trace
    example_trace = {
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
        "user_intent": "Find an affordable moisturizer for dry skin",
        "original_query": "I need a moisturizer",
        "original_intent": "Find a moisturizer",
        "conversation_flow": [
            {"role": "user", "content": "I need a moisturizer"},
            {"role": "agent", "content": "What's your skin type?"},
            {"role": "user", "content": "Dry"},
            {"role": "agent", "content": "What's your budget?"},
            {"role": "user", "content": "$25-$50"}
        ]
    }

    # Evaluate
    metrics = evaluate_trace_with_llm_judges(example_trace)

    print("=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    for metric, score in metrics.items():
        print(f"{metric:30s}: {score:.2f}")
