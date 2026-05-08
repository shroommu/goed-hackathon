# Backend Implementation Tickets

## P0 Core

### BE-001 Project bootstrap and environment setup [COMPLETED]
Estimate: 0.5 day
Dependencies: None
Acceptance Criteria:
1. API boots locally and in production mode.
2. Health endpoint returns status and build version.
3. Environment config supports local and deployed environments.

### BE-002 Core schema design for resources, companies, and profiles
Estimate: 1 day
Dependencies: BE-001
Acceptance Criteria:
1. Migrations exist for all core entities.
2. Required company fields are represented.
3. Seed script can load starter data packs.

### BE-003 Resource data ingestion pipeline
Estimate: 1 day
Dependencies: BE-002
Acceptance Criteria:
1. Import command ingests spreadsheet export reliably.
2. Validation reports row-level errors without failing whole import.
3. Imported resources are queryable by tags, stage, and location.

### BE-004 Company data ingestion pipeline
Estimate: 1 day
Dependencies: BE-002
Acceptance Criteria:
1. Company ingest supports create and update semantics.
2. Geocoding fallback strategy exists for missing coordinates.
3. Ingestion summary reports new, updated, and skipped rows.

### BE-005 Founder intake and personalization engine
Estimate: 2 days
Dependencies: BE-003
Acceptance Criteria:
1. Intake payload supports stage, industry, location, and objective.
2. Ranked recommendations include explanation for each match.
3. Distinct personas return meaningfully different top results.

### BE-006 Resource API endpoints
Estimate: 1 day
Dependencies: BE-005
Acceptance Criteria:
1. Endpoint latency remains responsive for typical datasets.
2. Pagination and filtering are supported.
3. Error responses are consistent and documented.

### BE-007 Company map API endpoints
Estimate: 1.5 days
Dependencies: BE-004
Acceptance Criteria:
1. Filters support sector, size, stage, hiring status, and location.
2. Map listing endpoint returns data suitable for clustered rendering.
3. Company details include all required profile fields.

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

## Backend Build Order

1. BE-001 to BE-007.
2. BE-008 and BE-009.
3. BE-010.
4. BE-011 to BE-013.