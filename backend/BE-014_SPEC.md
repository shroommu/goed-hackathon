# BE-014: Conversational Resource Orchestration API

**Status**: In Progress  
**Estimate**: 1.5 days  
**Dependencies**: BE-006 (Resource API endpoints)

---

## Overview

Build a conversational AI endpoint that helps entrepreneurs discover relevant resources through natural language interaction. The system extracts context from conversations, retrieves candidate resources using full-text search, and uses an LLM to generate personalized recommendations with rationales.

---

## Technical Architecture

### LLM Provider
- **Service**: OpenRouter (https://openrouter.ai)
- **Model**: `meta-llama/llama-3.1-8b-instruct` (budget tier, ~$0.10/M tokens)
- **Framework**: LangChain for conversation management and prompt orchestration
- **API Style**: OpenAI-compatible (easy migration path)

### Session Management
- **Strategy**: Stateless - client maintains and sends context with each request
- **Rationale**: Simplifies BE-014 implementation; full persistence will be added in BE-015

### Retrieval Strategy
- **Method**: Full-text search across resource fields (title, description, topics, industries, communities, locations)
- **Constraint**: Recommendations must come from actual Resource records (BE-016 requirement)
- **Ranking**: LLM selects and ranks top 5 from candidate set based on user context

---

## API Contract

### Endpoint
```
POST /api/navigator/chat/message
```

### Request Payload
```json
{
  "message": "string (required)",
  "context": {
    "stage": "string (optional)",
    "industry": "string (optional)",
    "location": "string (optional)",
    "objectives": ["string"] (optional),
    "topics": ["string"] (optional),
    "challenges": ["string"] (optional)
  }
}
```

**Field Descriptions**:
- `message`: User's conversational input
- `context`: Accumulated context from previous interactions (client-maintained)
  - `stage`: Business stage (e.g., "idea", "startup", "growth")
  - `industry`: Primary industry/sector
  - `location`: Geographic location
  - `objectives`: Goals (e.g., "funding", "hiring", "mentorship")
  - `topics`: Topics of interest
  - `challenges`: Current challenges or pain points

### Response Payload
```json
{
  "assistant_message": "string",
  "derived_context": {
    "stage": "string",
    "industry": "string",
    "location": "string",
    "objectives": ["string"],
    "topics": ["string"],
    "challenges": ["string"]
  },
  "recommendations": [
    {
      "id": 123,
      "title": "Resource Name",
      "description": "Brief description",
      "rationale": "LLM-generated explanation of why this resource matches",
      "url": "https://official.url",
      "topics": "Relevant Topics",
      "industries": "Relevant Industries",
      "communities": "Relevant Communities"
    }
  ],
  "follow_up_question": "string (optional)"
}
```

**Field Descriptions**:
- `assistant_message`: Natural language response to user's message
- `derived_context`: Updated context extracted from conversation (client should merge with existing)
- `recommendations`: Top 5 resources selected from candidate pool
  - `id`: Resource database ID
  - `title`: Resource title
  - `description`: Resource description
  - `rationale`: LLM-generated explanation specific to this user's context
  - `url`: Official resource link (from Resource.link field)
  - Additional metadata fields for transparency
- `follow_up_question`: Optional clarifying question if high-value context is missing

### Error Response
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

**Error Codes**:
- `invalid_request`: Malformed request payload
- `llm_timeout`: LLM request timed out
- `llm_error`: LLM service error
- `no_resources_found`: No candidate resources match query
- `internal_error`: Unexpected server error

---

## Conversation Flow

### Context Extraction
The system continuously extracts and updates:
1. **Stage**: Business/idea maturity (idea, pre-seed, startup, growth, established)
2. **Industry**: Primary sector (tech, healthcare, retail, etc.)
3. **Location**: Geographic focus (city, state, country, or "remote")
4. **Objectives**: What user wants to achieve (funding, hiring, mentorship, product-market fit, etc.)
5. **Topics**: Specific interests (AI/ML, sustainability, SaaS, etc.)
6. **Challenges**: Current blockers or pain points

### Follow-up Question Strategy
- **Natural Integration**: Ask clarifying questions naturally in conversation
- **Priority Order**: stage → objectives → industry → location → topics → challenges
- **Triggering Logic**: Ask when:
  - High-value field is missing AND
  - Would significantly improve recommendations AND
  - Not already asked in previous message
- **Example**: "To help me find the best resources, what stage is your business at—are you still at the idea stage, or have you launched?"

### Resource Retrieval Pipeline
1. **Parse User Message**: Extract keywords, intents, context updates
2. **Build Search Query**: 
   - Use extracted context fields (stage, industry, location, objectives, topics, challenges)
   - Construct full-text search across Resource fields
   - Prioritize fields: topics > industries > communities > title/description
3. **Retrieve Candidates**: Query database for matching resources (aim for 10-20 candidates)
4. **LLM Selection & Ranking**: 
   - Pass candidates to LLM with user context
   - LLM selects top 5 most relevant
   - LLM generates personalized rationale for each
5. **Fallback Logic**: If LLM fails, return deterministic top 5 by text match score

---

## Implementation Components

### 1. Dependencies (requirements.txt)
```
langchain==0.3.18
langchain-openai==0.2.14
openai==1.59.7
```

### 2. Configuration (app/config.py)
Add environment variables:
```python
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
```

### 3. Navigator Routes (app/routes_navigator.py)
New file containing:
- `POST /api/navigator/chat/message` handler
- Context extraction helper functions
- Resource retrieval logic (full-text search)
- LLM conversation orchestration with LangChain
- Response formatting
- Error handling with deterministic fallbacks

### 4. LangChain Integration
- **ChatOpenAI** client configured for OpenRouter
- **PromptTemplate** for system prompt:
  - Role: Entrepreneurship resource advisor
  - Task: Extract context, recommend resources, ask follow-up questions
  - Constraints: Only recommend resources from provided candidate list
  - Output format: JSON structure
- **Conversation chain** with context memory

### 5. Search Function
```python
def search_resources(context: dict, message: str) -> list[Resource]:
    """
    Full-text search across Resource fields using extracted context.
    Returns candidate resources for LLM ranking.
    """
```

### 6. LLM Orchestration
```python
def generate_response(message: str, context: dict, candidates: list[Resource]) -> dict:
    """
    Uses LangChain to:
    1. Update derived context from conversation
    2. Select top 5 resources from candidates
    3. Generate personalized rationales
    4. Create natural language response
    5. Optionally generate follow-up question
    """
```

---

## Acceptance Criteria

✅ **AC1**: `POST /api/navigator/chat/message` accepts user message plus optional context and returns assistant text, derived context, and recommendations.

✅ **AC2**: Recommendations are sourced only from existing Resource records and include id, rationale, and official URL.

✅ **AC3**: Follow-up question logic asks for missing high-value fields (stage, objective, location, industry, topics, challenges) naturally in conversation before broad fallback recommendations.

✅ **AC4**: Response schema and error handling are consistent with BE-006 contracts (using `_error_response` pattern).

---

## Error Handling & Fallbacks

### LLM Timeout or Failure
If OpenRouter/LLM fails:
1. Log error with context
2. Return deterministic recommendations using text match scoring
3. Include generic rationales based on field matches
4. Set error flag in response (optional telemetry field)

### No Resources Found
If search returns 0 candidates:
1. Return friendly message: "I couldn't find specific resources matching your needs yet. Let me ask a few questions to help narrow it down."
2. Generate follow-up question for missing high-value context
3. Empty recommendations array

### Invalid Request
- Missing `message` field → 400 error
- Malformed `context` object → 400 error with details
- Consistent with BE-006 error format

---

## Testing Scenarios

### Test Case 1: First Message (No Context)
**Request**:
```json
{
  "message": "I'm looking for funding for my AI startup"
}
```

**Expected**:
- Extract: industry="AI", objectives=["funding"], stage="startup" (implied)
- Retrieve candidates with AI + funding topics
- Return top 5 recommendations with rationales
- Possibly ask follow-up: "What stage is your startup at?"

### Test Case 2: Follow-up with Context
**Request**:
```json
{
  "message": "We're in San Francisco and just raised pre-seed",
  "context": {
    "industry": "AI",
    "objectives": ["funding"]
  }
}
```

**Expected**:
- Update context: location="San Francisco", stage="pre-seed"
- Narrow recommendations to SF-relevant resources
- No follow-up question needed (sufficient context)

### Test Case 3: LLM Failure
**Scenario**: OpenRouter returns 500 error

**Expected**:
- Return deterministic recommendations based on keyword matching
- Template rationales: "Matches your {industry} in {location}"
- Success response (not error) with valid recommendations

### Test Case 4: No Matching Resources
**Request**:
```json
{
  "message": "I need resources for underwater basket weaving"
}
```

**Expected**:
- Search returns 0 candidates
- Response includes assistant message explaining limited results
- Empty recommendations array
- Follow-up question to clarify needs

---

## Future Enhancements (Out of Scope for BE-014)

- **BE-015**: Session persistence, message history, telemetry
- **BE-016**: Enhanced safety validation, URL verification, fabrication prevention
- Semantic search with embeddings (vs. full-text)
- Multi-turn conversation memory (vs. stateless)
- Confidence scoring for recommendations
- A/B testing different prompts or models
- User feedback on recommendation quality

---

## Development Checklist

- [ ] Add OpenRouter dependencies to requirements.txt
- [ ] Create app/routes_navigator.py with endpoint handler
- [ ] Implement context extraction logic
- [ ] Implement full-text resource search function
- [ ] Configure LangChain with OpenRouter client
- [ ] Create system prompt template
- [ ] Implement LLM orchestration with error handling
- [ ] Add deterministic fallback logic
- [ ] Register navigator routes in app/routes.py
- [ ] Add OPENROUTER_API_KEY to environment config
- [ ] Test with sample conversations
- [ ] Verify error handling paths
- [ ] Validate response format consistency with BE-006

---

## Environment Variables

Add to `.env` or deployment config:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct
LLM_TIMEOUT_SECONDS=30
```
