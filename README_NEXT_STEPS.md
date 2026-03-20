# Next Steps for LLM-as-a-Judge Implementation

## Current Status

✅ **Completed:**
- Created comprehensive LLM-as-a-judge evaluation framework
- Defined 10 detailed metrics with evaluation prompts
- Built test infrastructure
- Updated GEPA optimizer to use new metrics
- Created 25 diverse test cases

❌ **Blocked:**
- GEPA package not publicly available yet
- Salesforce Bedrock proxy API incompatibility with Anthropic SDK
  - Returns `UnknownOperationException`
  - Content is None in responses

## Two Paths Forward

### Path 1: Fix API Access (Recommended)

**Option A: Use Standard Anthropic API**
```bash
# Set standard Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-your-key"
unset ANTHROPIC_AUTH_TOKEN
unset ANTHROPIC_BEDROCK_BASE_URL

# Use standard Claude
# Cost: ~$21 for 100 iterations
```

**Option B: Contact Salesforce DevX Team**
- The Bedrock proxy at `eng-ai-model-gateway.sfproxy.devx-preprod` might need:
  - Different authentication method
  - AWS Bedrock SDK instead of Anthropic SDK
  - Different model ID format
  - Special permissions/configuration

**Option C: Use AWS Bedrock Directly**
```python
import boto3

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
response = bedrock.invoke_model(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    })
)
```

### Path 2: Manual Optimization (Works Now)

Since LLM-as-a-judge isn't working yet, use your metrics conceptually:

**1. Manual Evaluation**
```bash
# Look at your 25 test cases
# For each one, manually assess:
# - Does agent understand intent?
# - Are questions easy to answer?
# - Do results match constraints?
# - etc.
```

**2. Iterative Improvement**
```javascript
// In index.html, improve based on failures:
// - Add brand name detection
// - Improve question ordering
// - Better constraint matching
// - etc.
```

**3. User Feedback**
```javascript
// Add feedback widget (from USER_FEEDBACK_GUIDE.md)
// Collect real user traces
// Use those to identify problems
```

## Quick Win: Simplified Test Without API

I can create a version that:
- ✅ Uses rule-based heuristics (not LLM judges)
- ✅ Still evaluates all 10 dimensions
- ✅ Works immediately
- ✅ Good enough for initial optimization

Example:
```python
def evaluate_goal_identification_heuristic(trace):
    # Rule-based evaluation
    query = trace['query'].lower()
    analysis = trace['analysis']

    score = 0.5  # baseline

    # Good signals
    if analysis['hasCategory']: score += 0.2
    if analysis['specificityScore'] >= 2: score += 0.2
    if not analysis['needsClarification']: score += 0.1

    return min(score, 1.0)
```

Would you like me to:
1. **Create rule-based version** (works now, ~80% as good)
2. **Help debug Bedrock API** (need DevX team help)
3. **Set up standard Anthropic API** (costs money but works)
4. **Something else**

## Files Ready to Use

Even without live API:

1. **llm_evaluator.py** - All 10 judge prompts ready
2. **gepa_optimize.py** - Integration code ready
3. **LLM_JUDGE_README.md** - Complete documentation
4. **25 test cases** - Comprehensive coverage
5. **Iteration strategy** - How to use iterations effectively

Once API works, everything else is ready to go!

## Alternative: OpenAI Models

If Bedrock is too complex, can use OpenAI:

```python
# In llm_evaluator.py
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def llm_judge(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Cheaper than Claude
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)
```

Cost: ~$10 for 100 iterations (vs $21 for Claude)

## Recommendation

**For right now:**
1. I'll create a rule-based evaluator that works immediately
2. You can start optimizing your agent today
3. When API access is sorted, swap to LLM judges

**For production:**
1. Get standard Anthropic API key OR
2. Work with DevX to fix Bedrock proxy OR
3. Use OpenAI GPT-4o-mini

Sound good?
