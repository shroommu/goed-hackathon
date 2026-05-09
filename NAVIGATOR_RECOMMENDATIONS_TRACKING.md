# Navigator chatbot — recommendations improvement tracking

Tracks implementation of the recommendations pipeline improvements (retrieval ranking, UX for follow-ups, validation, conversation history, LLM robustness, tuning). Related context: `resources_chatbot_feature_spec.md`, `backend/BE-014_SPEC.md`, `backend/app/routes_navigator.py`.

## Status legend

| Status | Meaning |
|--------|---------|
| ⬜ | Not started |
| 🟡 | In progress |
| ✅ | Done |
| ⏸️ | Deferred / out of scope |

## Phase overview

| Phase | Description | Status | Notes |
|-------|-------------|--------|-------|
| 0 | Scope and success criteria agreed | ⬜ | |
| 1 | Frontend: surface `follow_up_question` | ✅ | |
| 2 | Backend: dedupe IDs; empty-after-validation fallback | ⬜ | Prefer after Phase 3 for ranked deterministic fallback |
| 3 | Backend: rank candidates (replace `id` ordering) | ⬜ | |
| 4 | API + UI: optional conversation `history` | ⬜ | |
| 5 | LLM: prompt alignment + structured JSON where supported | ⬜ | |
| 6 | Tuning: timeout, short keywords, telemetry | ⬜ | |

## Phase 0 — Scope

- [ ] Success criteria documented for the release (follow-up visible, ranked candidates, multi-turn, no dupes / graceful empty states).
- [ ] Explicit non-goals for this iteration (e.g. vector search deferred).

## Phase 1 — Frontend: `follow_up_question`

**Primary files:** `frontend/components/ChatInterface.jsx`, optionally `frontend/components/ChatMessage.jsx`

- [x] Use `followUpQuestion` from `sendChatMessage` response (`frontend/lib/navigatorApi.js` already maps it).
- [x] Append to assistant message content and/or render a distinct “Next question” block.
- [ ] Manual QA: sparse context shows clarifying question in the thread.

## Phase 2 — Backend: validation and fallbacks

**Primary files:** `backend/app/routes_navigator.py`, `backend/tests/test_be016_safety.py`

- [ ] `_validate_and_enrich_recommendations`: track `seen` resource IDs; skip duplicates; cap at `BE016_MAX_RECOMMENDATIONS`.
- [ ] When enriched list is empty but candidates exist: user-safe `assistant_message`, optional `follow_up_question`, optional ranked deterministic fallback (Phase 3).
- [ ] Tests: duplicate LLM IDs → single card; all-invalid IDs → graceful response.

## Phase 3 — Backend: candidate ranking

**Primary files:** `backend/app/routes_navigator.py`, new or extended tests under `backend/tests/`

- [ ] Replace or post-process `order_by(Resource.id.asc())` with relevance scoring (weighted field hits, location/industry boosts).
- [ ] Fetch window if needed (e.g. larger limit → score → slice to `BE016_CANDIDATE_LIMIT`).
- [ ] Pass candidates to the LLM in score order; use same order for deterministic fallback.
- [ ] Fix misleading comment for “no search conditions” behavior (document actual behavior or change to sampling).
- [ ] Unit tests for ranking determinism and tie-breakers.

## Phase 4 — Conversation history

**Primary files:** `backend/app/routes_navigator.py`, `frontend/lib/navigatorApi.js`, `frontend/components/ChatInterface.jsx`

- [ ] Request body: optional `history: [{ role, content }]`, capped (turns + chars).
- [ ] Include transcript in `ChatPromptTemplate` for `generate_llm_response`.
- [ ] Frontend sends recent messages (exclude welcome; normalize payload).
- [ ] Test: second turn without repeating full context improves relevance or derived context.

## Phase 5 — LLM robustness

**Primary files:** `backend/app/routes_navigator.py`

- [ ] Trim system prompt (remove redundant “insufficient context” branch; server already gates).
- [ ] Enable structured / JSON mode if supported by current OpenRouter + LangChain path.
- [ ] Optional: two-step id selection + rationales (only if parse failures remain high).

## Phase 6 — Tuning and observability

**Primary files:** `backend/app/routes_navigator.py`, config / `.env.example`

- [ ] Revisit `BE016_TIMEOUT_BUDGET_MS` vs measured LLM latency.
- [ ] Refine `_collect_search_terms` (allowlist for short tokens like `ai`, etc.).
- [ ] Structured logs or metrics: candidate count, validation failures, empty-enriched events.

## Rollout checklist

- [ ] Phase 1 can ship independently.
- [ ] Coordinate deploy if `history` is required server-side before frontend sends it (or feature-flag).
- [ ] After Phase 3: re-check fallback rate and manual relevance QA before widening timeout.

## References

- Implementation detail: review thread in Cursor (navigator recommendations).
- Core route: `backend/app/routes_navigator.py` (`POST /api/navigator/chat/message`).
