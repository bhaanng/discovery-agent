# User Feedback Collection & Optimization Guide

## Overview

Real user feedback is **10x more valuable** than synthetic test cases for GEPA optimization. This guide shows how to collect, analyze, and use feedback to continuously improve your agent.

## Types of User Feedback

### 1. Explicit Feedback (Direct User Input)
User deliberately rates or comments on their experience

### 2. Implicit Feedback (Behavioral Signals)
Inferred from user actions and engagement patterns

### 3. Outcome Feedback (Task Completion)
Whether the user achieved their goal

---

## Implementation Strategy

### Phase 1: Basic Feedback Collection (Quick Start)

Add simple thumbs up/down after showing products:

```javascript
// Add to your index.html after product results

const addFeedbackWidget = () => {
    return {
        role: 'agent',
        content: "Did you find what you were looking for?",
        feedbackWidget: true,
        timestamp: new Date()
    };
};

// In your message rendering
{msg.feedbackWidget && (
    <div className="flex gap-3 mt-4">
        <button
            onClick={() => handleFeedback(sessionId, 'positive')}
            className="flex-1 py-2 bg-green-50 hover:bg-green-100 rounded-lg text-green-700 font-medium transition-colors flex items-center justify-center gap-2"
        >
            <Icon name="thumbs-up" size={18} />
            Yes, helpful!
        </button>
        <button
            onClick={() => handleFeedback(sessionId, 'negative')}
            className="flex-1 py-2 bg-red-50 hover:bg-red-100 rounded-lg text-red-700 font-medium transition-colors flex items-center justify-center gap-2"
        >
            <Icon name="thumbs-down" size={18} />
            Not quite
        </button>
    </div>
)}
```

### Phase 2: Rich Feedback Collection

**A. Post-Search Survey (Conditional)**
Only show if user gives negative feedback:

```javascript
const handleNegativeFeedback = (sessionId) => {
    setMessages(prev => [...prev, {
        role: 'agent',
        content: "Sorry about that! What would have made this search better?",
        feedbackOptions: [
            "Wrong product type",
            "Products too expensive",
            "Results not relevant",
            "Asked too many questions",
            "Didn't understand my need",
            "Other"
        ],
        timestamp: new Date()
    }]);
};
```

**B. Implicit Behavioral Tracking**

Track these signals automatically:

```javascript
const sessionMetrics = {
    // Engagement
    timeOnPage: Date.now() - sessionStart,
    messagesExchanged: messageCount,
    questionsAnswered: answeredQuestions.length,
    productsViewed: viewedProducts.length,
    productsClicked: clickedProducts.length,

    // Search quality
    searchRefinements: refinementCount,
    backButtonClicks: backCount,
    repeatedQueries: queryRepeatCount,

    // Outcomes
    taskCompleted: didFindProduct,
    sessionAbandoned: leftWithoutResult,
    returnVisitor: hasSeenBefore
};
```

### Phase 3: Trace Collection for GEPA

Capture full execution traces with user feedback:

```javascript
const captureSessionTrace = () => {
    return {
        // Session metadata
        sessionId: generateSessionId(),
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,

        // Query & Analysis
        originalQuery: sessionContext.originalQuery,
        queryAnalysis: {
            specificityScore: analysis.specificityScore,
            hasCategory: analysis.hasCategory,
            needsClarification: analysis.needsClarification,
            detectedIntent: analysis.intent
        },

        // Conversation flow
        messagesExchanged: messages.map(m => ({
            role: m.role,
            content: m.content,
            timestamp: m.timestamp
        })),

        // Questions asked
        questionsAsked: messages
            .filter(m => m.clarifyingQuestions)
            .map(m => ({
                questions: m.clarifyingQuestions,
                userAnswers: getUserAnswers(m)
            })),

        // Search & Results
        apiCalls: [
            {
                query: searchQuery,
                filters: appliedFilters,
                resultsCount: results.length,
                topProducts: results.slice(0, 10).map(p => ({
                    name: p.product_name,
                    brand: p.brand_name,
                    price: p.price_numeric,
                    relevanceScore: p.score
                }))
            }
        ],

        // User behavior
        behavior: {
            productsClicked: clickedProducts,
            timeToFirstClick: firstClickTime,
            scrollDepth: maxScrollDepth,
            refinements: refinementCount
        },

        // Explicit feedback
        feedback: {
            rating: userRating, // thumbs up/down
            category: feedbackCategory, // what went wrong
            comment: feedbackComment, // free text
            wouldRecommend: npsScore
        },

        // Outcome metrics
        outcome: {
            taskCompleted: didFindProduct,
            turnsToSuccess: messageCount,
            timeToSuccess: sessionDuration,
            abandonedEarly: leftBeforeResults
        }
    };
};
```

---

## Feedback Storage Options

### Option 1: Local Storage (Development)
```javascript
// Store traces in browser
const saveTrace = (trace) => {
    const traces = JSON.parse(localStorage.getItem('agentTraces') || '[]');
    traces.push(trace);
    localStorage.setItem('agentTraces', JSON.stringify(traces));
};

// Export for GEPA
const exportTraces = () => {
    const traces = JSON.parse(localStorage.getItem('agentTraces') || '[]');
    const blob = new Blob([JSON.stringify(traces, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-traces-${Date.now()}.json`;
    a.click();
};
```

### Option 2: Simple Backend (Production)
```javascript
// Send to your backend
const saveTrace = async (trace) => {
    await fetch('/api/agent-trace', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trace)
    });
};
```

### Option 3: Google Analytics / Mixpanel
```javascript
// Track with analytics
const trackAgentEvent = (eventName, properties) => {
    // Google Analytics
    gtag('event', eventName, properties);

    // Or Mixpanel
    mixpanel.track(eventName, properties);
};

// Usage
trackAgentEvent('agent_query_analyzed', {
    query: userQuery,
    specificityScore: score,
    needsClarification: needs
});

trackAgentEvent('agent_feedback', {
    rating: 'positive',
    turnsToSuccess: 3,
    relevanceScore: 9.5
});
```

---

## Feedback-Driven GEPA Optimization

### Step 1: Collect Real User Data (1-2 weeks)

Aim for minimum:
- **50 sessions** (more is better)
- Mix of positive and negative outcomes
- Diverse query types

### Step 2: Analyze Feedback Patterns

```python
# analyze_feedback.py

import json
from collections import Counter

def analyze_traces(traces_file):
    with open(traces_file) as f:
        traces = json.load(f)

    # Satisfaction analysis
    positive_feedback = [t for t in traces if t['feedback']['rating'] == 'positive']
    negative_feedback = [t for t in traces if t['feedback']['rating'] == 'negative']

    print(f"Overall satisfaction: {len(positive_feedback)/len(traces)*100:.1f}%")

    # What's working
    print("\n✅ Successful patterns:")
    positive_queries = [t['originalQuery'] for t in positive_feedback]
    print(f"   Sample queries: {positive_queries[:5]}")

    # What's failing
    print("\n❌ Failure patterns:")
    failure_reasons = Counter([
        t['feedback'].get('category', 'unknown')
        for t in negative_feedback
    ])
    for reason, count in failure_reasons.most_common(5):
        print(f"   {reason}: {count} times")

    # Identify problem areas
    print("\n🔍 Problem areas:")

    # 1. Unnecessary questions
    over_questioned = [t for t in traces if len(t['questionsAsked']) > 3]
    print(f"   Over-questioning: {len(over_questioned)} sessions")

    # 2. Poor relevance
    low_relevance = [t for t in traces if t['outcome']['turnsToSuccess'] > 5]
    print(f"   Low relevance (>5 turns): {len(low_relevance)} sessions")

    # 3. Abandoned sessions
    abandoned = [t for t in traces if t['outcome']['abandonedEarly']]
    print(f"   Abandoned early: {len(abandoned)} sessions")

    return traces
```

### Step 3: Create Test Cases from Real Failures

```python
# Convert real failures to GEPA test cases

def create_test_cases_from_failures(traces):
    test_cases = []

    for trace in traces:
        if trace['feedback']['rating'] == 'negative':
            test_case = {
                "query": trace['originalQuery'],
                "difficulty": "real_world",
                "user_feedback": trace['feedback'],
                "expected": {
                    # What SHOULD have happened
                    "should_clarify": should_have_clarified(trace),
                    "ideal_questions": ideal_questions(trace),
                    "expected_results": trace['behavior']['productsClicked']
                },
                "ideal_outcome": {
                    "turns": trace['outcome']['turnsToSuccess'] - 2,  # Target: 2 fewer turns
                    "relevance": 9.0,  # Target: high relevance
                    "satisfaction": True
                },
                "failure_mode": trace['feedback']['category']
            }
            test_cases.append(test_case)

    return test_cases
```

### Step 4: Run GEPA with Real Data

```python
# gepa_optimize_with_real_data.py

from gepa import optimize_anything
import json

# Load real user traces
with open('user_traces.json') as f:
    real_traces = json.load(f)

# Convert to test cases
test_cases = create_test_cases_from_failures(real_traces)

# Mix with original synthetic cases (important!)
all_test_cases = SYNTHETIC_TEST_CASES + test_cases

print(f"Optimizing with {len(all_test_cases)} test cases")
print(f"  - {len(SYNTHETIC_TEST_CASES)} synthetic")
print(f"  - {len(test_cases)} real user failures")

# Run GEPA
result = optimize_anything(
    seed_artifacts=artifacts,
    train_examples=all_test_cases,
    evaluator=evaluate_with_real_feedback,
    objectives=[
        {"name": "turns_to_success", "direction": "minimize", "weight": 0.3},
        {"name": "user_satisfaction", "direction": "maximize", "weight": 0.4},
        {"name": "relevance_score", "direction": "maximize", "weight": 0.3}
    ],
    max_iterations=150,  # More iterations for real data
    task_model="claude-3-5-sonnet-20241022",
    reflection_model="claude-3-5-haiku-20241022"
)
```

---

## Continuous Optimization Loop

### Monthly Optimization Cycle

**Week 1: Data Collection**
- Deploy current agent
- Collect user traces
- Monitor feedback dashboard

**Week 2: Analysis**
- Analyze failure patterns
- Identify top 3 problem areas
- Create targeted test cases

**Week 3: Optimization**
- Run GEPA with real + synthetic data
- A/B test top 2 solutions
- Measure improvement

**Week 4: Deployment**
- Deploy winning solution
- Document improvements
- Update test suite

### Automated Dashboard

```javascript
// Real-time metrics dashboard
const AgentMetrics = () => {
    const [metrics, setMetrics] = useState({
        totalSessions: 0,
        satisfactionRate: 0,
        avgTurns: 0,
        avgRelevance: 0,
        topFailures: []
    });

    return (
        <div className="p-6 bg-white rounded-lg shadow">
            <h2 className="text-xl font-bold mb-4">Agent Performance</h2>

            <div className="grid grid-cols-4 gap-4 mb-6">
                <MetricCard
                    label="Satisfaction"
                    value={`${metrics.satisfactionRate}%`}
                    trend={+5}
                />
                <MetricCard
                    label="Avg Turns"
                    value={metrics.avgTurns.toFixed(1)}
                    trend={-0.8}
                />
                <MetricCard
                    label="Relevance"
                    value={`${metrics.avgRelevance}/10`}
                    trend={+0.5}
                />
                <MetricCard
                    label="Sessions"
                    value={metrics.totalSessions}
                />
            </div>

            <div>
                <h3 className="font-semibold mb-2">Top Failure Modes</h3>
                {metrics.topFailures.map((failure, i) => (
                    <div key={i} className="flex justify-between py-2 border-b">
                        <span>{failure.reason}</span>
                        <span className="text-red-600">{failure.count} sessions</span>
                    </div>
                ))}
            </div>
        </div>
    );
};
```

---

## Quick Implementation Checklist

### Phase 1: Basic (1 hour)
- [ ] Add thumbs up/down widget
- [ ] Track in localStorage
- [ ] Export traces manually

### Phase 2: Behavioral (2 hours)
- [ ] Track time metrics
- [ ] Track click events
- [ ] Track abandonment

### Phase 3: Rich Feedback (3 hours)
- [ ] Add follow-up questions for negative feedback
- [ ] Capture full session traces
- [ ] Build export functionality

### Phase 4: Backend Integration (1 day)
- [ ] Set up /api/agent-trace endpoint
- [ ] Store in database
- [ ] Build admin dashboard

### Phase 5: GEPA Integration (2 hours)
- [ ] Download traces
- [ ] Convert to test cases
- [ ] Re-run optimization
- [ ] A/B test improvements

---

## Example: Complete Feedback Flow

```javascript
// 1. User completes search
setMessages(prev => [...prev, {
    role: 'agent',
    content: formatted.message,
    products: formatted.products,
    requestFeedback: true
}]);

// 2. Show feedback widget
if (msg.requestFeedback) {
    <FeedbackWidget
        onFeedback={(rating, details) => {
            // Capture full trace
            const trace = captureSessionTrace();
            trace.feedback = { rating, ...details };

            // Save locally
            saveTrace(trace);

            // Send to backend
            sendToBackend(trace);

            // Show thank you
            setMessages(prev => [...prev, {
                role: 'agent',
                content: rating === 'positive'
                    ? "Thank you! Happy shopping! 🎉"
                    : "Thanks for the feedback. We'll use it to improve! 💪"
            }]);
        }}
    />
}

// 3. Weekly: Export and analyze
const exportForGEPA = () => {
    const traces = getAllTraces();
    const failures = traces.filter(t => t.feedback.rating === 'negative');

    console.log(`Collected ${traces.length} traces`);
    console.log(`${failures.length} failures to learn from`);

    downloadJSON(traces, 'agent-traces-for-gepa.json');
};

// 4. Run GEPA with real data
// python gepa_optimize.py --train-data agent-traces-for-gepa.json --iterations 150

// 5. Deploy improved agent
// Update index.html with optimized logic
```

---

## Key Metrics to Track

### Primary Metrics
1. **User Satisfaction Rate** - % thumbs up
2. **Task Completion Rate** - % found what they need
3. **Avg Turns to Success** - Conversation efficiency
4. **Product Relevance Score** - Quality of results

### Secondary Metrics
5. **Question Efficiency** - % questions that helped
6. **Search Precision** - Click-through rate
7. **Abandonment Rate** - % who leave early
8. **Return Rate** - % who come back

### Diagnostic Metrics
9. **Top Failure Modes** - Why users are unhappy
10. **Query Type Distribution** - What people ask for
11. **Time Metrics** - Speed to first result
12. **Refinement Patterns** - How users narrow down

---

## Expected ROI

### Before Feedback-Driven Optimization
- Satisfaction: 68%
- Avg turns: 5.2
- Based on synthetic test cases

### After 1 Month of Real Feedback
- Satisfaction: 87% (+19 points)
- Avg turns: 3.1 (-40%)
- Based on 500+ real sessions

### Continuous Improvement
- Monthly: +2-5% satisfaction
- Quarterly: +10-15% satisfaction
- Compounds over time

---

## Resources

### Starter Code
- `feedback-widget.js` - Copy-paste feedback UI
- `trace-capture.js` - Session trace collection
- `analyze_feedback.py` - Python analysis script
- `export_for_gepa.py` - Convert traces to test cases

### Tools
- Google Analytics - Free, easy to integrate
- Mixpanel - More detailed behavioral tracking
- Hotjar - Heatmaps and session recordings
- PostHog - Open source, self-hosted

### Reading
- "Measuring AI Agent Performance" - Anthropic blog
- "Human-in-the-Loop ML" - Manning book
- "Continuous Optimization" - GEPA docs
