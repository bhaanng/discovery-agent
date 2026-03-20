# GEPA Iteration Strategy: Getting the Most Value

## Understanding Iterations

Each GEPA iteration:
1. **Selects** a candidate from Pareto frontier
2. **Executes** it on test cases, capturing traces
3. **Reflects** on failures using LLM analysis
4. **Mutates** to create improved version
5. **Evaluates** and adds to population if better

**Key insight:** GEPA learns from *failures*, not successes. Rich failure traces → better improvements.

## Optimal Iteration Counts

### Phase 1: Discovery (10-20 iterations)
**Goal:** Explore the solution space quickly
**Cost:** ~$0.16-$0.32
**Time:** 5-10 minutes

```bash
python gepa_optimize.py --iterations 10
```

**What happens:**
- Initial random exploration
- Discovers major failure modes
- Identifies easy wins
- Builds first Pareto frontier

**Review checkpoint:**
- Check `gepa_results.json` for diversity
- Look for 3-5 different solutions on frontier
- Identify which objectives are hardest

**Decision:**
- ✅ If seeing clear improvements → Continue to Phase 2
- ❌ If all solutions similar → Need better test cases (see below)

### Phase 2: Refinement (50-100 iterations)
**Goal:** Converge on Pareto-optimal solutions
**Cost:** ~$0.79-$1.58
**Time:** 25-50 minutes

```bash
python gepa_optimize.py --iterations 100
```

**What happens:**
- Exploits promising directions from Phase 1
- Fine-tunes trade-offs
- Stabilizes Pareto frontier
- Accumulates lessons from edge cases

**Expected results:**
- 5-10 distinct solutions on frontier
- Clear trade-off patterns (fast vs. accurate, etc.)
- 2-3x improvement on primary metrics

### Phase 3: Deep Search (200-500 iterations)
**Goal:** Find rare optimal solutions
**Cost:** ~$3.16-$7.90
**Time:** 100-250 minutes

```bash
python gepa_optimize.py --iterations 500
```

**Only do this if:**
- Phase 2 results are promising but not good enough
- You have budget for deeper search
- Test cases cover diverse failure modes
- Metrics still improving after 100 iterations

**Diminishing returns:** GEPA paper shows most gains in first 100-200 iterations.

## Test Case Strategy (Most Important!)

**Quality > Quantity.** 5 great test cases beat 50 mediocre ones.

### Good Test Case Design

#### ❌ Bad: Homogeneous tests
```python
TEST_CASES = [
    {"query": "moisturizer", ...},
    {"query": "face cream", ...},
    {"query": "lotion", ...},
    # All basically the same!
]
```

#### ✅ Good: Diverse, edge cases
```python
TEST_CASES = [
    # 1. Broad query (tests clarification logic)
    {
        "query": "I need skincare",
        "difficulty": "hard",
        "tests": ["clarification_needed", "question_quality"]
    },

    # 2. Over-specific query (tests when NOT to ask)
    {
        "query": "CeraVe Moisturizing Cream for dry sensitive skin 19oz under $20",
        "difficulty": "easy",
        "tests": ["skip_clarification", "immediate_search"]
    },

    # 3. Ambiguous intent (tests understanding)
    {
        "query": "something that makes my face glow",
        "difficulty": "hard",
        "tests": ["disambiguate_makeup_vs_skincare", "clarify_goal"]
    },

    # 4. Edge case: contradictory requirements
    {
        "query": "luxury moisturizer under $10",
        "difficulty": "edge_case",
        "tests": ["handle_contradiction", "clarify_priority"]
    },

    # 5. Misspelled/informal (tests robustness)
    {
        "query": "moisterizer for acnee",
        "difficulty": "medium",
        "tests": ["spelling_tolerance", "intent_extraction"]
    },

    # 6. Multi-product query
    {
        "query": "cleanser and moisturizer for sensitive skin",
        "difficulty": "medium",
        "tests": ["handle_multiple_products", "prioritization"]
    },

    # 7. Negative constraint
    {
        "query": "face cream without fragrance or parabens",
        "difficulty": "medium",
        "tests": ["negative_filters", "ingredient_awareness"]
    },

    # 8. Context-dependent
    {
        "query": "something for after the gym",
        "difficulty": "hard",
        "tests": ["infer_use_case", "product_timing"]
    }
]
```

### Test Case Coverage Matrix

Ensure your test cases cover:

| Dimension | Coverage |
|-----------|----------|
| **Specificity** | Vague → Specific spectrum |
| **Intent clarity** | Clear → Ambiguous |
| **Complexity** | Single → Multiple requirements |
| **Domain knowledge** | Expert → Novice queries |
| **Edge cases** | Contradictions, misspellings, negations |
| **User types** | First-time, returning, power users |

## Progressive Optimization Strategy

### Strategy A: Breadth-First (Recommended)
```bash
# Round 1: Quick discovery with diverse tests (10 iter)
python gepa_optimize.py --iterations 10

# Review results, identify weakest area
# Add 2-3 test cases targeting that weakness

# Round 2: Deeper search (50 iter)
python gepa_optimize.py --iterations 50

# Review Pareto frontier
# Pick best solution for A/B test

# Round 3: Fine-tune winner (100 iter) - only if needed
python gepa_optimize.py --iterations 100
```

**Total cost:** $0.16 + $0.79 + $1.58 = $2.53
**Time:** ~1 hour across multiple sessions
**Benefit:** Learn between rounds, adapt test cases

### Strategy B: Depth-First
```bash
# Single deep run
python gepa_optimize.py --iterations 500
```

**Total cost:** $7.90
**Time:** 4+ hours
**Risk:** If test cases are poor, you waste iterations

## Monitoring Progress

### Live Progress Indicators

Add to your script to watch optimization:

```python
def on_iteration_complete(iteration, population, frontier):
    """Callback to monitor progress."""

    # Best score on each objective
    best_turns = min(p["metrics"]["turns_to_success"] for p in frontier)
    best_relevance = max(p["metrics"]["relevance_score"] for p in frontier)
    best_satisfaction = max(p["metrics"]["user_satisfied"] for p in frontier)

    print(f"Iter {iteration:3d} | Frontier: {len(frontier)} solutions")
    print(f"  Best turns: {best_turns:.1f}")
    print(f"  Best relevance: {best_relevance:.1f}/10")
    print(f"  Best satisfaction: {best_satisfaction*100:.0f}%")

    # Improvement rate
    if iteration > 10:
        print(f"  Improvement last 10 iters: ...")
```

### When to Stop Early

**Stop if (before max_iterations):**
- No improvement in 20+ consecutive iterations
- Pareto frontier hasn't changed in 30+ iterations
- Already hit your target metrics
- Solutions becoming too complex/overfitted

**Continue if:**
- Frontier still growing
- Metrics steadily improving
- Clear trajectory toward targets
- High variance in solution quality (still exploring)

## Maximize Information per Iteration

### 1. Add Evaluation Granularity

```python
def evaluate_agent_trace(query, trace):
    """Rich evaluation with sub-metrics."""

    return {
        # Primary objectives
        "turns_to_success": count_turns(trace),
        "relevance_score": rate_relevance(trace),
        "user_satisfied": check_satisfaction(trace),

        # Secondary metrics (help GEPA learn)
        "analysis_accuracy": did_analysis_match_expected(trace),
        "question_quality": measure_information_gain(trace),
        "search_precision": top_k_precision(trace, k=6),
        "unnecessary_questions": count_unnecessary_asks(trace),
        "time_to_first_result": measure_latency(trace),

        # Failure diagnostics
        "failure_reason": identify_failure_mode(trace),  # "wrong_category", "missed_intent", etc.
        "recovery_possible": could_have_recovered(trace),
        "user_confusion_points": where_user_got_lost(trace)
    }
```

More metrics → Better reflection → Faster convergence

### 2. Trace Enrichment

Capture everything that might help diagnosis:

```python
trace = {
    "query": query,
    "analysis": {
        "specificityScore": score,
        "detectedEntities": entities,  # brands, skin types, etc.
        "inferredIntent": intent,
        "confidence": confidence_score
    },
    "searchResults": {
        "query_sent": api_query,
        "results_count": count,
        "top_results": results[:10],
        "diversity_score": measure_diversity(results),
        "coverage": which_criteria_matched(results, user_filters)
    },
    "questions": [
        {
            "text": q,
            "options": opts,
            "reasoning": why_asked,
            "expected_gain": predicted_information_value,
            "actual_gain": measured_after_answer,
            "user_answer": answer,
            "answer_time": how_long_to_respond
        }
    ],
    "userBehavior": {
        "hesitationPoints": where_paused,
        "reworded_queries": follow_ups,
        "abandoned": did_give_up
    }
}
```

### 3. Objective Weighting Experiments

Try different weight combinations across runs:

```bash
# Run 1: Optimize for speed (10 iterations)
python gepa_optimize.py --iterations 10 --weights "0.6,0.2,0.2"

# Run 2: Optimize for accuracy (10 iterations)
python gepa_optimize.py --iterations 10 --weights "0.2,0.6,0.2"

# Run 3: Balanced (100 iterations with winning weights)
python gepa_optimize.py --iterations 100 --weights "0.3,0.4,0.3"
```

## Advanced: Curriculum Learning

Start with easy cases, progressively add harder ones:

```python
# Round 1: Easy cases only (20 iterations)
EASY_CASES = [specific_queries_only]
# Learn basic search and formatting

# Round 2: Add medium cases (30 iterations)
MEDIUM_CASES = EASY_CASES + [ambiguous_queries]
# Learn clarification

# Round 3: Add hard cases (50 iterations)
ALL_CASES = MEDIUM_CASES + [edge_cases, contradictions]
# Learn robustness
```

**Why it works:** GEPA builds on lessons learned. Start with foundation.

## Iteration Budget Allocation

### Scenario: $5 budget (~316 iterations)

**Option A: Depth**
- 316 iterations on one configuration
- Risk: Miss better configurations

**Option B: Breadth (Recommended)**
- 5 configs × 20 iterations = 100 iterations ($1.58)
- Pick best 2 configs
- 2 configs × 50 iterations = 100 iterations ($1.58)
- Pick winner
- 1 config × 116 iterations = 116 iterations ($1.83)
- **Total: $4.99**

**Option C: Ensemble**
- 10 configs × 10 iterations = 100 iterations ($1.58)
- Identify top 3 distinct approaches
- Combine insights manually
- 1 hybrid config × 200 iterations ($3.16)
- **Total: $4.74**

## Real-World Example

### Iteration 1-10: Discovery
```
Iter  1: Random init → turns=8.2, relevance=6.1 (baseline)
Iter  5: Found: asking fewer questions helps → turns=5.3
Iter  8: Found: better search query helps → relevance=7.2
Iter 10: Frontier has 3 solutions
```

### Iteration 11-50: Refinement
```
Iter 15: Combined fewer questions + better search → turns=4.1, relevance=7.8
Iter 25: Learned: skip questions for brand-specific queries → turns=3.2
Iter 40: Learned: data-driven options improve relevance → relevance=8.4
Iter 50: Frontier has 7 solutions, clear trade-offs visible
```

### Iteration 51-100: Convergence
```
Iter 60: Frontier stable, small improvements only
Iter 75: Edge case handling improved → satisfaction=87%
Iter 90: Overfitting detected, diversity injected
Iter 100: Final frontier: 6 solutions, 2-3x better than baseline
```

## Key Takeaways

1. **10 iterations:** Good for exploration, testing setup
2. **50 iterations:** Solid results for most use cases
3. **100 iterations:** Recommended for production deployment
4. **200+ iterations:** Only if you have specific constraints

5. **Test case quality matters 10x more than iteration count**

6. **Run multiple short rounds with learning > One long run**

7. **Monitor progress:** Stop early if converged, continue if improving

8. **Invest in evaluation:** Rich traces → Better reflection → Faster improvement

## Quick Start Recipe

```bash
# Day 1 Morning: Discovery (15 min, $0.16)
python gepa_optimize.py --iterations 10
# Review results over coffee

# Day 1 Afternoon: Add 2 test cases for weakest area (30 min, $0.79)
python gepa_optimize.py --iterations 50
# A/B test top 2 solutions

# Day 2: Deep optimization of winner (1 hour, $1.58)
python gepa_optimize.py --iterations 100
# Deploy

# Total: 2 days, $2.53, production-ready optimization
```
