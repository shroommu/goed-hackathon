# GOED Webapp Implementation Tickets

## Sprint Strategy

1. Sprint 1: Foundation + core data model + basic UX shell.
2. Sprint 2: Founder Navigator personalization + map exploration.
3. Sprint 3: Self-service profiles + verification + polish + demo hardening.

## Backend Tickets

### BE-001 Project bootstrap and environment setup
Priority: P0
Estimate: 0.5 day
Dependencies: None
Description: Initialize backend service, config management, environment variables, logging, and health endpoint.
Acceptance Criteria:
1. API boots locally and in production mode.
2. Health endpoint returns status and build version.
3. Environment config supports local and deployed environments.

### BE-002 Core schema design for resources, companies, and profiles
Priority: P0
Estimate: 1 day
Dependencies: BE-001
Description: Create database schema for resource catalog, founder intake, recommendations, companies, claims, verification events, and media references.
Acceptance Criteria:
1. Migrations exist for all core entities.
2. Required company fields are represented.
3. Seed script can load starter data packs.

### BE-003 Resource data ingestion pipeline
Priority: P0
Estimate: 1 day
Dependencies: BE-002
Description: Import and normalize resource spreadsheet data into searchable entities.
Acceptance Criteria:
1. Import command ingests spreadsheet export reliably.
2. Validation reports row-level errors without failing whole import.
3. Imported resources are queryable by tags, stage, and location.

### BE-004 Company data ingestion pipeline
Priority: P0
Estimate: 1 day
Dependencies: BE-002
Description: Import and normalize map company data.
Acceptance Criteria:
1. Company ingest supports create and update semantics.
2. Geocoding fallback strategy exists for missing coordinates.
3. Ingestion summary reports new, updated, and skipped rows.

### BE-005 Founder intake and personalization engine
Priority: P0
Estimate: 2 days
Dependencies: BE-003
Description: Build scoring/matching service that maps founder context to ranked resources.
Acceptance Criteria:
1. Intake payload supports stage, industry, location, and objective.
2. Ranked recommendations include explanation for each match.
3. Distinct personas return meaningfully different top results.

### BE-006 Resource API endpoints
Priority: P0
Estimate: 1 day
Dependencies: BE-005
Description: Expose endpoints for intake submission, recommendations, resource list, and resource detail.
Acceptance Criteria:
1. Endpoint latency remains responsive for typical datasets.
2. Pagination and filtering are supported.
3. Error responses are consistent and documented.

### BE-007 Company map API endpoints
Priority: P0
Estimate: 1.5 days
Dependencies: BE-004
Description: Expose map listing, geospatial query, filters, and company detail endpoints.
Acceptance Criteria:
1. Filters support sector, size, stage, hiring status, and location.
2. Map listing endpoint returns data suitable for clustered rendering.
3. Company details include all required profile fields.

### BE-008 Self-service listing and claim workflow
Priority: P0
Estimate: 2 days
Dependencies: BE-007
Description: Implement company create, claim request, owner update, and moderation states.
Acceptance Criteria:
1. User can submit new company listing.
2. User can claim an existing company.
3. Ownership status gates edit permissions.

### BE-009 Lightweight verification flow
Priority: P0
Estimate: 1.5 days
Dependencies: BE-008
Description: Add verification options such as domain email or admin review queue.
Acceptance Criteria:
1. Verification state is visible and auditable.
2. Unverified claims cannot publish protected changes.
3. Admin can approve or reject claims.

### BE-010 Admin content update endpoints
Priority: P0
Estimate: 1 day
Dependencies: BE-006, BE-007
Description: Add non-technical update path for resources and companies through admin-safe endpoints.
Acceptance Criteria:
1. Admin can create, edit, archive resources.
2. Admin can edit company metadata and status.
3. Changes are reflected immediately in public queries.

### BE-011 Auth and authorization
Priority: P1
Estimate: 1.5 days
Dependencies: BE-008
Description: Implement role model for visitor, founder, company-owner, and admin.
Acceptance Criteria:
1. Public endpoints remain accessible without sign-in where appropriate.
2. Claim and admin actions require authenticated roles.
3. Unauthorized actions return correct status codes.

### BE-012 Link checker and content quality job
Priority: P1
Estimate: 0.5 day
Dependencies: BE-010
Description: Background task to detect broken resource links and flag stale records.
Acceptance Criteria:
1. Broken links are marked for admin review.
2. Job can run on schedule and on demand.
3. Report output is visible to admins.

### BE-013 Observability and audit trail
Priority: P1
Estimate: 1 day
Dependencies: BE-001
Description: Add request logs, structured events for claims/verification, and dashboard-friendly metrics.
Acceptance Criteria:
1. Critical flows emit structured logs.
2. Claim and verification actions are auditable.
3. Basic error-rate and latency metrics are exposed.

## Frontend Tickets

### FE-001 Frontend app bootstrap and design system foundation
Priority: P0
Estimate: 0.5 day
Dependencies: None
Description: Initialize app, routing, theme tokens, typography, and layout primitives.
Acceptance Criteria:
1. Responsive shell with desktop and mobile nav.
2. Shared color, type, spacing tokens are implemented.
3. Accessibility baseline is configured.

### FE-002 Landing page and mode selection
Priority: P0
Estimate: 0.5 day
Dependencies: FE-001
Description: Build first-touch experience for founders and investors with clear entry points.
Acceptance Criteria:
1. User can choose navigator or map flow quickly.
2. Value proposition is clear in under one screen.
3. CTA paths are measurable and trackable.

### FE-003 Founder intake experience
Priority: P0
Estimate: 1 day
Dependencies: FE-001, BE-006
Description: Build guided intake form with adaptive questions.
Acceptance Criteria:
1. Intake completes in under 2 minutes for typical users.
2. Validation errors are clear and recoverable.
3. Progress state is preserved during navigation.

### FE-004 Personalized recommendations UI
Priority: P0
Estimate: 1 day
Dependencies: FE-003, BE-006
Description: Render ranked recommendations with rationale and next actions.
Acceptance Criteria:
1. Each recommendation shows why it matches.
2. Resource cards include direct links and tags.
3. Users can compare or save items for later.

### FE-005 Interactive Utah startup map
Priority: P0
Estimate: 2 days
Dependencies: FE-001, BE-007
Description: Build fast, filterable map with clustering and discoverable interactions.
Acceptance Criteria:
1. Map supports zoom, pan, marker select, and clustered points.
2. Filter changes update map and list view quickly.
3. Empty-state and no-result handling are clear.

### FE-006 Company profile page
Priority: P0
Estimate: 1 day
Dependencies: FE-005, BE-007
Description: Build detail page for company with complete required fields.
Acceptance Criteria:
1. All required fields are displayed cleanly.
2. Job postings and media gallery render correctly.
3. External links are validated and safe.

### FE-007 Self-service create and claim flows
Priority: P0
Estimate: 1.5 days
Dependencies: FE-006, BE-008, BE-009
Description: Build submit listing, claim listing, and verification status UX.
Acceptance Criteria:
1. User can create or claim with clear guidance.
2. Verification state and next steps are visible.
3. Owner edit access appears only when authorized.

### FE-008 Company owner edit dashboard
Priority: P1
Estimate: 1 day
Dependencies: FE-007, BE-011
Description: Build editable profile form with autosave or explicit publish flow.
Acceptance Criteria:
1. Owner can update all editable fields.
2. Validation and preview are available.
3. Change history entry appears after publish.

### FE-009 Admin content management screens
Priority: P1
Estimate: 1.5 days
Dependencies: BE-010
Description: Build non-technical CMS-like views for resource and company updates.
Acceptance Criteria:
1. Admin can create, edit, and archive records.
2. Bulk update path exists for spreadsheet refresh.
3. Admin can review claim queue and verification status.

### FE-010 Persona validation harness
Priority: P0
Estimate: 0.5 day
Dependencies: FE-004, FE-005
Description: Add test mode or scripted scenarios for six required personas.
Acceptance Criteria:
1. Persona presets can run end-to-end quickly.
2. Output differences are visible and explainable.
3. Screenshots or logs can be exported for demo evidence.

### FE-011 Performance and accessibility pass
Priority: P0
Estimate: 1 day
Dependencies: FE-004, FE-005, FE-006
Description: Optimize loading, interactions, and keyboard/screen-reader support.
Acceptance Criteria:
1. Core user flows remain smooth on mid-range mobile.
2. Keyboard navigation works across critical interactions.
3. Contrast and semantic structure meet accessibility baseline.

### FE-012 Investor-ready visual polish and storytelling
Priority: P1
Estimate: 1 day
Dependencies: FE-011
Description: Final visual and narrative polish for presentation and production confidence.
Acceptance Criteria:
1. Visual consistency is strong across all pages.
2. Empty/loading/error states look intentional.
3. Demo flow can be presented without design gaps.

## Integration and QA Tickets

### QA-001 API contract and integration tests
Priority: P0
Estimate: 1 day
Dependencies: BE-006, BE-007, FE-004, FE-005
Description: Validate endpoint contracts and key end-to-end frontend integrations.
Acceptance Criteria:
1. Contract tests cover critical endpoints.
2. CI fails on contract drift.
3. Core user journeys pass in integration test run.

### QA-002 Persona acceptance test suite
Priority: P0
Estimate: 0.5 day
Dependencies: FE-010
Description: Formalize tests for all six personas and expected differentiated outcomes.
Acceptance Criteria:
1. Each persona has expected top recommendation set.
2. Regression suite catches personalization failures.
3. Test report is shareable for judging/demo.

### QA-003 Security and abuse checks
Priority: P1
Estimate: 0.5 day
Dependencies: BE-009, BE-011
Description: Validate claim-flow abuse resistance and basic API hardening.
Acceptance Criteria:
1. Rate limits or anti-spam checks protect submissions.
2. Unauthorized profile edits are blocked.
3. Input validation covers all write endpoints.

## Suggested Build Order

1. BE-001 to BE-007 and FE-001 to FE-006 for MVP core.
2. BE-008, BE-009, FE-007 for self-service + verification.
3. FE-010, QA-002 to validate persona differentiation.
4. BE-010, FE-009 for non-technical content updates.
5. FE-011, FE-012, QA-001, QA-003 for final hardening.

## Demo Readiness Checklist

1. Founder intake produces personalized recommendations in under 2 minutes.
2. Map filters work and reveal complete company profiles.
3. Claim/create flow demonstrates verification and permissions.
4. Admin update path shows non-technical content editing.
5. Persona tests show clearly different outcomes.
