# Backend Implementation Tickets

## P0 Core

### BE-001 Project bootstrap and environment setup [COMPLETED]
Estimate: 0.5 day
Dependencies: None
Acceptance Criteria:
1. API boots locally and in production mode.
2. Health endpoint returns status and build version.
3. Environment config supports local and deployed environments.

### BE-002 Core schema design for resources, companies, and profiles [COMPLETED]
Estimate: 1 day
Dependencies: BE-001
Acceptance Criteria:
1. Migrations exist for all core entities.
2. Required company fields are represented.
3. Seed script can load starter data packs.

### BE-003 Resource data ingestion pipeline [COMPLETED]
Estimate: 1 day
Dependencies: BE-002
Acceptance Criteria:
1. Import command ingests spreadsheet export reliably.
2. Validation reports row-level errors without failing whole import.
3. Imported resources are queryable by Communities, Industries, Locations, and Topics.

### BE-004 Company data ingestion pipeline [SKIPPED]
Estimate: 1 day
Dependencies: BE-002
Acceptance Criteria:
1. Company ingest supports create and update semantics.
2. Geocoding fallback strategy exists for missing coordinates.
3. Ingestion summary reports new, updated, and skipped rows.

### BE-005 Guided onboarding and personalization engine [SKIPPED]
Estimate: 2 days
Dependencies: BE-003
Acceptance Criteria:
1. Onboarding payload supports stage, industry, location, and objective.
2. Ranked recommendations include explanation for each match.
3. Distinct personas return meaningfully different top results.

### BE-006 Resource API endpoints [COMPLETED]
Estimate: 1 day
Dependencies: BE-005
Acceptance Criteria:
1. Endpoint latency remains responsive for typical datasets.
2. Pagination and filtering are supported.
3. Error responses are consistent and documented.

### BE-007 Company map and filtered mindmap API endpoints [COMPLETED]
Estimate: 2 days
Dependencies: BE-004
Acceptance Criteria:
1. Filters support sector, size, stage, hiring status, and location.
2. Listing endpoint returns deterministic paginated data suitable for both clustered map rendering and Sector -> Stage -> Company mindmap rendering.
3. Filter validation and error responses are consistent for invalid values, invalid paging, and empty results.
4. Company details include all required profile fields.

### BE-008 Self-service listing and claim workflow [COMPLETED]
Estimate: 2 days
Dependencies: BE-007
Acceptance Criteria:
1. User can submit new company listing.
2. User can claim an existing company.
3. Ownership status gates edit permissions.

### BE-009 Lightweight verification flow [COMPLETED]
Estimate: 1.5 days
Dependencies: BE-008
Acceptance Criteria:
1. Verification state is visible and auditable.
2. Unverified claims cannot publish protected changes.
3. Admin can approve or reject claims.

### BE-010 Admin content update endpoints [COMPLETED]
Estimate: 1 day
Dependencies: BE-006, BE-007
Acceptance Criteria:
1. Admin can create, edit, archive resources.
2. Admin can edit company metadata and status.
3. Changes are reflected immediately in public queries.

### BE-014 Conversational resource orchestration API [COMPLETED]
Estimate: 1.5 days
Dependencies: BE-006
Acceptance Criteria:
1. `POST /navigator/chat/message` accepts user message plus optional session/context and returns assistant text, derived context, and recommendations.
2. Recommendations are sourced only from existing resource records and include id, rationale, and official URL.
3. Follow-up question logic asks for missing high-value fields (stage, objective, location) before broad fallback recommendations.
4. Response schema and error handling are consistent with BE-006 contracts.

### BE-015 Chat session persistence and telemetry
Estimate: 1 day
Dependencies: BE-014
Acceptance Criteria:
1. Conversation sessions and message history are persisted with retrievable transcript snapshots.
2. Recommendation events are stored with rank and score for auditing/evaluation.
3. Session restore endpoint supports frontend refresh and resume use cases.
4. Structured telemetry includes session id, latency, and recommendation count.

### BE-016 Retrieval-constrained prompt and safety validator
Estimate: 1 day
Dependencies: BE-014
Acceptance Criteria:
1. LLM prompt context is restricted to candidate resources returned by deterministic retrieval.
2. Post-generation validation blocks resources not present in the candidate set.
3. URL and resource id validation prevent fabricated links or unknown programs in responses.
4. Timeout/fallback path returns deterministic recommendations if LLM step fails.

Implementation Defaults (Interviewed):
1. Primary risk to prevent: fabricated recommendations (resource not in DB).
2. Candidate set policy: deterministic retrieval plus light expansion (synonyms/tags), capped at top 20.
3. Validation strictness: drop invalid items only (do not fail entire response if some items are valid).
4. Identity policy: resource id is source of truth; title/url are display fields.
5. URL policy: response URL must exactly match stored official URL.
6. Timeout budget: 3000 ms total for LLM generation and safety validation.
7. Fallback policy: return deterministic top-N with canned rationale text on LLM timeout/error.
8. Sparse-context behavior: ask follow-up first, then provide recommendations.
9. Debug transparency: include filtered-item reasons only in admin/debug mode.
10. Rollout: enabled by default (no feature flag for initial release).

Required Telemetry:
1. candidate_count
2. blocked_count
3. llm_timeout
4. fallback_used
5. validation_fail_reasons

Minimum Test Bar (Current Decision):
1. Adversarial hallucination tests that verify out-of-candidate resources and fabricated URLs are filtered.

Definition of Done (Current Decision):
1. BE-016 acceptance criteria pass.

## P1 Hardening

### BE-011 Auth and authorization
Estimate: 1.5 days
Dependencies: BE-008
Acceptance Criteria:
1. Public endpoints remain accessible without sign-in where appropriate.
2. Claim and admin actions require authenticated roles.
3. Unauthorized actions return correct status codes.

Implementation Defaults (Interviewed):
1. Public endpoints (no auth required): resource read APIs, company read APIs, health/version endpoints.
2. All write endpoints are protected — no public writes.
3. Role model: anonymous | user | admin.
4. Admin role source: JWT `app_metadata.role = "admin"` (Supabase token).
5. Ownership resolution: via approved claim record whose `user_id` matches the authenticated user's JWT subject.
6. Ownership edit rule: owner or admin only; other authenticated users are forbidden.
7. Auth failure status codes: 401 when no valid JWT is present; 403 when authenticated but not authorized.
8. Error body contract: use existing BE-006 error envelope for all auth failure responses.
9. Auth source: verify Supabase JWT on the backend for every protected request.
10. Rollout: enabled immediately in all environments — no feature flag.

Audit Events to Log:
1. 401 responses — include endpoint and action.
2. 403 responses — include endpoint, action, and user id.
3. Token verification failures — include failure reason.
4. Successful admin mutations — include actor user id and target record.
5. Successful owner edits — include actor user id and company id.

Implementation Checklist:
- [x] `auth.py` decorator/helper: verify Supabase JWT and extract `sub`, `app_metadata.role`.
- [x] `require_auth` decorator: returns 401 with BE-006 envelope if no valid token.
- [x] `require_role("admin")` via `require_admin` decorator: returns 403 if authenticated user lacks admin role.
- [x] `owner_or_admin_for_company` helper: verified claim by `user_id = sub` or admin role; returns 403 otherwise.
- [x] Apply `require_admin` to all admin routes (`routes_admin.py`).
- [x] Apply `require_auth` to submit-listing and claim routes (`routes_companies.py`).
- [x] Apply `owner_or_admin_for_company` to company protected-field edit route.
- [x] Apply `require_admin` to verification approval/rejection endpoints.
- [x] Structured auth event logging for all five audit events above.
- [x] Route-level / JWT tests: public vs protected, expired token, non-admin vs admin, claim decision audit (see `tests/test_be011_auth.py`, `tests/test_be008_workflow.py`).

Minimum Test Bar (Current Decision):
1. Route-level test matrix: public, user, owner, admin — one happy-path and one rejection case per route group.
2. Auth decorator unit tests: missing token → 401, expired token → 401, valid non-admin → 403 on admin route, valid owner → 200 on own company, non-owner user → 403.

Definition of Done (Current Decision):
1. BE-011 acceptance criteria pass.
2. All five audit event types appear in structured logs under integration test.
3. Route matrix tests green for public, user, owner, and admin paths.

### BE-012 Link checker and content quality job
Estimate: 0.5 day
Dependencies: BE-010
Acceptance Criteria:
1. Broken links are marked for admin review.
2. Job can run on schedule and on demand.
3. Report output is visible to admins.

### BE-013 Observability and audit trail
Estimate: 1 day
Dependencies: BE-001
Acceptance Criteria:
1. Critical flows emit structured logs.
2. Claim and verification actions are auditable.
3. Basic error-rate and latency metrics are exposed.
4. Company listing flow logs include filter dimensions and response-shape telemetry for map and mindmap usage.

## Backend Build Order

1. BE-001 to BE-007, with BE-007 providing a shared contract for map and filtered mindmap views.
2. BE-008 and BE-009.
3. BE-010.
4. BE-014 to BE-016.
5. BE-011 to BE-013.