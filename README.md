# Product Discovery Agent - Cimulate Integration

An intelligent product discovery agent that uses natural language to help users find products through Cimulate's search API.

## 🎯 Three-Phase System Architecture

### Phase 1: Initial Query Analysis
**Purpose**: Evaluate user intent and gather necessary context before searching

**Logic**:
- Analyzes if query is specific enough for immediate search
- Identifies if user intent is for exact match or supplementary products
- If query is too broad → triggers clarifying questions
- Maximum 2-3 questions to avoid cognitive overload
- Each question includes:
  - Restatement of understood portion (for user validation)
  - Brief "Why" explanation
  - Clear showcase of how answering helps solve the problem
- Context is remembered across session to avoid repeat questions

**Example Flow**:
```
User: "I need a moisturizer"
Agent: "I understand you're looking for a moisturizer. To find the perfect match, I have a few quick questions:"

1. What's your skin type?
   💡 This helps me recommend products formulated specifically for your skin's needs
   [Dry] [Oily] [Combination] [Normal] [Sensitive]

2. What's your primary skin concern?
   💡 I can match you with products that target your specific goals
   [Hydration] [Anti-aging] [Acne] [Brightening] [Sensitivity]
```

### Phase 2: Search Results Integration & Formatting
**Purpose**: Execute search and present results in PSA format

**Logic**:
- Only shows results when enough context is gathered
- Transforms Cimulate API response to PSA format
- Includes customer-specific refinements in search query
- Highlights why top results match the identified filters
- Results presented in brand voice/tone

**API Integration**:
```javascript
// Cimulate API Call
POST https://search-api.demo.search.cimulate.ai/api/v1/search
Headers:
  - x-cimulate-customer-id: cephora
  - x-cimulate-api-key: 6827c3f6-2c53-4ed1-16d8-c7546de99c82
Body:
  {
    "query": "moisturizer for dry skin hydration",
    "page_size": 300,
    "include_facets": true
  }
```

**Response Transformation**:
- Extracts top 6 results
- Formats product cards with: name, brand, price, image, description
- Adds contextual explanation: "Based on your preferences for dry skin and hydration, here are the top matches:"

### Phase 3: Post-Search Refinement
**Purpose**: Help users refine search results further

**Logic**:
- After displaying results, asks ONE follow-up question
- Question is relevant to:
  - Context gathered in session
  - Original user intent
  - Search results characteristics
- Examples: formula preference (cream/gel/oil), ingredient preferences, specific features

**Example Flow**:
```
Agent: [Shows 6 product results]
Agent: "Would you like to refine your search?"

Would you prefer a cream, gel, or oil formula?
💡 Different textures work better for different skin types and preferences
[Cream] [Gel] [Oil] [No preference]
```

## 🚀 Quick Start

Simply open `index.html` in a browser. No build process required!

```bash
open index.html
```

## 📋 Features

✅ **Natural Language Understanding**
- Analyzes user queries for intent and specificity
- Contextual understanding across conversation

✅ **Smart Clarification**
- Max 2-3 upfront questions
- Each question explains "why" it matters
- Restates understanding before asking
- Never repeats questions in same session

✅ **Cimulate API Integration**
- Real-time product search
- Faceted search with refinements
- 300 product results per query

✅ **PSA Format Results**
- Clean product cards
- Contextual match explanations
- Responsive grid layout

✅ **Intelligent Refinement**
- Post-search follow-up questions
- Session-aware suggestions
- Optional user refinements

## 🔧 Configuration

### Cimulate API Credentials
Located in `index.html` around line 43:

```javascript
const CIMULATE_CONFIG = {
    endpoint: 'https://search-api.demo.search.cimulate.ai/api/v1/search',
    customerId: 'cephora',
    apiKey: '6827c3f6-2c53-4ed1-16d8-c7546de99c82'
};
```

### Customizing Query Analysis
Modify the `analyzeQuery()` function to adjust what makes a query "specific enough":

```javascript
const analyzeQuery = (query) => {
    // Add your custom logic here
    // Return { isSpecific, hasCategory, needsClarification }
};
```

### Adding More Clarifying Questions
Edit `generateClarifyingQuestions()` function to add domain-specific questions:

```javascript
if (!context.gatheredInfo.yourNewField) {
    questions.push({
        question: "Your question?",
        why: "Why this matters",
        options: ["Option1", "Option2", "Option3"]
    });
}
```

## 📱 UI Features

- **Clean Chat Interface**: Focused conversation flow
- **Quick Reply Buttons**: One-tap answers to questions
- **Product Grid**: Visual product cards with images
- **Loading States**: Clear feedback during API calls
- **Responsive Design**: Works on desktop and mobile

## 🧠 Session Context Memory

The agent maintains context throughout the session:

```javascript
sessionContext = {
    originalQuery: "moisturizer",
    gatheredInfo: {
        skinType: "Dry",
        concern: "Hydration",
        priceRange: "$25-$50"
    },
    clarificationCount: 2,
    searchPerformed: true
}
```

This prevents:
- Asking the same question twice
- Losing user preferences between messages
- Redundant clarifications

## 🎨 Customization Ideas

1. **Brand Voice**: Update agent responses to match brand personality
2. **Product Categories**: Add support for other product types (makeup, fragrance, etc.)
3. **Advanced Filters**: Integrate Cimulate facets for ingredient filtering
4. **User Preferences**: Save preferences across sessions with localStorage
5. **Product Details**: Add product detail view with full descriptions

## 📊 How It Works

### Query Analysis Logic
```
User Query → Analyze specificity →
  ├─ Specific enough? → Call API → Show results
  └─ Too broad? → Ask 2-3 questions → Gather info → Call API → Show results
```

### Context Building
```
Q1: Skin type (Dry) →
Q2: Concern (Hydration) →
Q3: Price ($25-$50) →
Build query: "moisturizer for dry skin hydration $25-$50" →
Call Cimulate API
```

### Result Refinement
```
Show 6 products →
Ask refinement (formula type) →
User selects "Gel" →
Re-search with added filter →
Show refined results
```

## 🔍 Testing the Agent

### Test Query 1: Broad Query (Triggers Clarification)
```
Input: "I need skincare"
Expected: Agent asks 2-3 clarifying questions
```

### Test Query 2: Specific Query (Immediate Search)
```
Input: "I'm looking for a hydrating moisturizer for dry sensitive skin"
Expected: Agent searches immediately and shows results
```

### Test Query 3: Follow-up Refinement
```
Input: "I need a moisturizer"
[Answer clarifying questions]
[See results]
Input: "Show me only gel formulas"
Expected: Agent refines search with new filter
```

## 🚀 Future Enhancements

- [ ] Integration with Gemini/Claude for more nuanced query understanding
- [ ] Multi-turn clarification (if user provides partial answers)
- [ ] Comparison view (side-by-side product comparison)
- [ ] Favorites/wishlist functionality
- [ ] Purchase intent detection
- [ ] Review summarization from Cimulate data

## 📄 License

Prototype for demonstration purposes.

---

**Built with**: React, Tailwind CSS, Cimulate Search API
