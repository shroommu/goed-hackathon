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

### BE-008 Self-service listing and claim workflow
Estimate: 2 days
Dependencies: BE-007
Acceptance Criteria:
1. User can submit new company listing.
2. User can claim an existing company.
3. Ownership status gates edit permissions.

### BE-009 Lightweight verification flow
Estimate: 1.5 days
Dependencies: BE-008
Acceptance Criteria:
1. Verification state is visible and auditable.
2. Unverified claims cannot publish protected changes.
3. Admin can approve or reject claims.

### BE-010 Admin content update endpoints
Estimate: 1 day
Dependencies: BE-006, BE-007
Acceptance Criteria:
1. Admin can create, edit, archive resources.
2. Admin can edit company metadata and status.
3. Changes are reflected immediately in public queries.

### BE-014 Conversational resource orchestration API
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

## P1 Hardening

### BE-011 Auth and authorization
Estimate: 1.5 days
Dependencies: BE-008
Acceptance Criteria:
1. Public endpoints remain accessible without sign-in where appropriate.
2. Claim and admin actions require authenticated roles.
3. Unauthorized actions return correct status codes.

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