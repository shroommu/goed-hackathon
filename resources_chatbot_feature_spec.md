# Plan: Resource Navigator Conversational Chatbot

Implement a resource-guidance chatbot in the Founder Navigator so users can describe goals in plain text and receive ranked Utah resources with clear rationale and next actions. The chatbot should be grounded in the project resource dataset and existing personalization goals, not free-form general advice.

## Outcome

1. Users can ask natural-language questions (for example, "I am pre-seed in Ogden and need first funding options") and receive tailored resource recommendations.
2. Recommendations remain explainable, link-backed, and aligned to known resource records.
3. The conversation can gather missing context in under 2 minutes and improve recommendation relevance over follow-up turns.

## Scope

### In Scope

1. Chat UI in the Navigator route with guided follow-up questions.
2. Backend chat orchestration endpoint using retrieval from the resources table.
3. Deterministic ranking plus LLM-generated conversational framing.
4. Conversation state for one active session per user (anonymous or authenticated).
5. Safety and quality guardrails to avoid hallucinated programs or unsafe claims.
6. Analytics and persona-based evaluation.

### Out of Scope (MVP)

1. Voice interaction.
2. Multi-language translations.
3. Long-term cross-device memory.
4. Automated application submission to third-party programs.

## User Experience Requirements

### Primary User Stories

1. As a founder, I can describe my situation in plain text instead of filling only a static form.
2. As a founder, I can answer follow-up questions that narrow recommendations by stage, location, industry, objective, and founder attributes.
3. As a founder, I can see why each recommended resource matches me.
4. As a founder, I can open official links and save recommended items.

### UX Behavior

1. Chat opens from the Navigator as the primary intake mode.
2. First assistant message asks 1 to 2 concise questions to establish context.
3. Assistant asks at most one follow-up question per turn unless user requests a faster path.
4. Assistant returns a recommendation block after enough context is captured.
5. Every recommendation card includes:
   - Program name
   - Short description
   - Match rationale
   - Official link
   - Tags/category
6. Users can request: "show more like this", "broaden options", or "focus on grants/mentors/etc."

## System Architecture

### Frontend (Next.js)

1. Add a chat-first experience in `frontend/app/navigator/page.jsx`.
2. Create components:
   - `ChatPanel` for messages and input
   - `RecommendationCards` for structured results
   - `ContextChips` for active profile constraints (stage, location, objective)
3. Maintain conversation state client-side for current session, with backend session id.
4. Use backend APIs only for domain data; do not build parallel Next domain APIs.

### Backend (Flask)

1. Add conversation endpoints in `backend/app/routes.py`.
2. Add service layer modules for:
   - Context extraction from text
   - Resource retrieval and ranking
   - Prompt assembly and LLM call
   - Response normalization
3. Persist minimal conversation/session data for replay and analytics.

### Data Layer

1. Use existing `resources` dataset as source of truth.
2. Use normalized fields for ranking dimensions:
   - stage
   - location
   - objective
   - category/tags
3. Optionally add a denormalized search field or trigram index for keyword matching.

## Conversation and Ranking Design

### Hybrid Decision Flow

1. Parse user message into structured candidate context:
   - stage
   - industry
   - location
   - objective
   - optional founder attributes
2. Compute deterministic ranking from database records.
3. Pass top N records and context to LLM only for:
   - conversational explanation
   - tie-breaking rationale
   - follow-up question suggestion
4. Return structured output with source resource ids and links.

### Ranking Heuristic (Initial)

Use a weighted score per resource:

$$
score = 0.35(stage\_match) + 0.25(objective\_match) + 0.15(location\_match) + 0.15(category\_match) + 0.10(tag\_similarity)
$$

1. Exact matches score highest.
2. Related matches (for example, "capital" near "funding") get partial credit.
3. Archived resources are excluded.
4. Return top 5 by default, with pagination or "show more".

### Follow-up Question Logic

1. If stage is missing, ask stage first.
2. If objective is missing, ask objective second.
3. If location is missing and resource depends on geography, ask location third.
4. Stop asking questions once confidence threshold is met.

## API Contract (Proposed)

### 1) Create/Continue Chat Session

`POST /navigator/chat/message`

Request:

```json
{
  "session_id": "optional-uuid",
  "message": "I am building a health startup in Provo and need funding.",
  "user_context": {
    "stage": "pre-seed",
    "industry": "health",
    "location": "Provo",
    "objective": "capital"
  }
}
```

Response:

```json
{
  "session_id": "uuid",
  "assistant_message": "Based on your pre-seed health focus in Provo, here are strong starting points...",
  "follow_up_question": "Do you want grant-focused options, investor introductions, or both?",
  "recommendations": [
    {
      "resource_id": 12,
      "name": "SBA Utah District Office",
      "short_description": "Federal small business guidance, counseling, and funding education.",
      "why_match": "Matches your capital objective and early stage needs.",
      "official_url": "https://www.sba.gov/district/utah",
      "category": "Funding",
      "tags": ["funding", "mentorship"]
    }
  ],
  "derived_context": {
    "stage": "pre-seed",
    "location": "Provo",
    "objective": "capital"
  },
  "confidence": 0.82
}
```

### 2) Fetch Session Transcript

`GET /navigator/chat/session/<session_id>`

Returns ordered messages and recommendation snapshots for restore/debug.

### 3) Feedback on Recommendation Quality

`POST /navigator/chat/feedback`

Tracks thumbs up/down, selected resource, and optional free text.

## Database Additions (MVP)

Add lightweight chat tables:

1. `chat_sessions`
   - id (uuid)
   - created_at
   - updated_at
   - founder_profile_id (nullable)
   - status
2. `chat_messages`
   - id
   - session_id
   - role (`user`, `assistant`, `system`)
   - content
   - derived_context (jsonb)
   - created_at
3. `chat_recommendation_events`
   - id
   - session_id
   - message_id
   - resource_id
   - rank
   - score
   - created_at

## Prompting and Safety

### Prompt Rules

1. Only recommend resources present in retrieved dataset.
2. Never invent program names, eligibility rules, or deadlines.
3. If uncertain, ask a clarifying question instead of guessing.
4. Keep responses concise and action-oriented.

### Safety Controls

1. Retrieval-constrained generation: LLM sees only top-ranked candidate resources and context.
2. Post-generation validation: remove recommendations whose ids are not in candidate set.
3. URL validation: only show canonical official URLs from database.
4. PII handling: avoid requesting unnecessary personal data.

## Observability and Analytics

Track events:

1. `navigator_chat_started`
2. `navigator_chat_message_sent`
3. `navigator_chat_followup_asked`
4. `navigator_chat_recommendations_shown`
5. `navigator_chat_resource_clicked`
6. `navigator_chat_feedback_submitted`

Required dimensions:

1. session_id
2. detected_stage
3. detected_objective
4. detected_location
5. response_latency_ms
6. recommendation_count

## Performance Targets

1. P50 response time < 1.5s for cached context and local ranking.
2. P95 response time < 3.5s including LLM step.
3. Initial recommendation result returned within 2 turns for most users.

## Accessibility and UX Quality

1. Full keyboard operation for chat input, send action, and recommendation cards.
2. Screen-reader labels for message roles and card actions.
3. Clear loading and retry states for API/LLM failures.
4. Mobile layout keeps input visible and avoids scroll traps.

## Implementation Phases

### Phase 1: Backend Foundation

1. Add chat schema migration and SQLAlchemy models.
2. Add endpoint: `POST /navigator/chat/message`.
3. Build context extraction + deterministic ranking service.
4. Add response schema and validation tests.

### Phase 2: Frontend Chat UX

1. Replace Navigator placeholder with chat-first UI.
2. Render structured recommendation cards.
3. Add optimistic UI states, retries, and empty states.
4. Persist session id and restore transcript on refresh.

### Phase 3: Safety + Quality

1. Add retrieval-constrained prompt layer.
2. Add hallucination guard validation.
3. Add analytics instrumentation.
4. Add persona evaluation scripts and benchmark report.

### Phase 4: Hardening

1. Add recommendation feedback loop for ranking improvements.
2. Add admin observability dashboard slices.
3. Tune latency and caching strategy.

## Ticket Additions (Proposed)

### Backend

1. `BE-014 Conversational resource orchestration API`
2. `BE-015 Chat session persistence and telemetry`
3. `BE-016 Retrieval-constrained prompt and safety validator`

### Frontend

1. `FE-013 Navigator chatbot interface`
2. `FE-014 Conversational recommendation cards and feedback`
3. `FE-015 Chat accessibility and mobile hardening`

## Acceptance Criteria

1. User can start a chat and receive tailored resource recommendations within 2 minutes.
2. Recommendations include rationale and valid official links.
3. Distinct test personas produce meaningfully different top recommendations.
4. No recommendation is returned unless it maps to an existing resource id.
5. Chat interaction is functional on mobile and desktop with keyboard support.

## Risks and Mitigations

1. Risk: Hallucinated or low-precision recommendations.
   Mitigation: retrieval-constrained generation + post-validation.
2. Risk: Slow response times from LLM dependency.
   Mitigation: deterministic ranking first, small prompt context, timeout fallback.
3. Risk: Sparse resource metadata reduces match quality.
   Mitigation: expand ingestion normalization and tags in BE-003.

## Open Decisions

1. LLM provider/model and hosting policy.
2. Anonymous session retention period.
3. Whether to expose a "show scoring details" debug mode for admins.
4. Whether founder attributes (veteran, woman-owned, researcher) are optional fields in phase 1 or phase 2.