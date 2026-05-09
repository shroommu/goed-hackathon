# Frontend Implementation Tickets

## Integration Guardrails

1. Frontend features must consume APIs exposed by the Flask backend service, not implement parallel domain APIs in Next.
2. Do not add feature APIs under `app/api/*` for resources, companies, claims, recommendations, or admin flows.
3. A Next route handler is only allowed for edge-case proxy use (for example third-party secret handling) and must be documented with rationale.
4. Frontend should read backend base URL from environment configuration (for example `NEXT_PUBLIC_API_BASE_URL`) and keep request/response contracts aligned with backend tickets.
5. Existing analytics handler is a telemetry exception and must not be used as a template for domain data APIs.

## P0 Core

### FE-001 Frontend app bootstrap and design system foundation [COMPLETED]
Estimate: 0.5 day
Dependencies: None
Acceptance Criteria:
1. Responsive shell with desktop and mobile nav.
2. Shared color, type, spacing tokens are implemented.
3. Accessibility baseline is configured.

### FE-002 Landing page and mode selection [COMPLETED]
Estimate: 0.5 day
Dependencies: FE-001
Acceptance Criteria:
1. User can choose navigator or map flow quickly.
2. Value proposition is clear in under one screen.
3. CTA paths are measurable and trackable.

### FE-003 Guided onboarding flow [SKIPPED]
Estimate: 1 day
Dependencies: FE-001, BE-006
Acceptance Criteria:
1. Guided onboarding completes in under 2 minutes for typical users.
2. Validation errors are clear and recoverable.
3. Progress state is preserved during navigation.
4. Onboarding submission and recommendation fetch use backend endpoints only.

### FE-004 Personalized recommendations UI [COMPLETED]
Estimate: 1 day
Dependencies: FE-003, BE-006
Acceptance Criteria:
1. Each recommendation shows why it matches.
2. Recommendation payload shape matches backend contract.

### FE-005 Interactive Utah startup map and filtered mindmap [COMPLETED]
Estimate: 2.5 days
Dependencies: FE-001, BE-007
Acceptance Criteria:
1. Map supports zoom, pan, marker select, and clustered points.
2. Applying filters auto-transforms the experience to a 2D mindmap organized as Sector -> Stage -> Company.
3. Mindmap view keeps full filter editability and can toggle back to map view without losing filter state.
4. Empty-state and no-result handling are clear and investor-oriented.
5. Mobile behavior uses simplified hierarchy plus drill-down to prevent dense unreadable layouts.
6. Map and mindmap data are sourced from backend listing/detail endpoints.

### FE-006 Company profile page [COMPLETED]
Estimate: 1 day
Dependencies: FE-005
Acceptance Criteria:
1. All required fields are displayed cleanly.
2. Media gallery renders correctly when URLs are present.
3. External links are validated and safe.
4. Company details are fetched from backend detail endpoint.

### FE-007 Self-service create and claim flows
Estimate: 1.5 days
Dependencies: FE-006, BE-008, BE-009
Acceptance Criteria:
1. User can create or claim with clear guidance.
2. Verification state and next steps are visible.
3. Owner edit access appears only when authorized.
4. Submission and claim actions call backend write endpoints with contract-aligned validation handling.

### FE-010 Persona validation harness
Estimate: 0.5 day
Dependencies: FE-004, FE-005
Acceptance Criteria:
1. Persona presets can run end-to-end quickly.
2. Output differences are visible and explainable.
3. Screenshots or logs can be exported for demo evidence.
4. Investor scenarios validate pattern discovery quality in filtered mindmap flows.

### FE-011 Performance and accessibility pass
Estimate: 1 day
Dependencies: FE-004, FE-005, FE-006
Acceptance Criteria:
1. Core user flows remain smooth on mid-range mobile.
2. Keyboard navigation works across critical interactions.
3. Contrast and semantic structure meet accessibility baseline.
4. Mindmap focus management and keyboard traversal are verified.

## P1 Hardening

### FE-008 Company owner edit dashboard
Estimate: 1 day
Dependencies: FE-007, BE-011
Acceptance Criteria:
1. Owner can update all editable fields.
2. Validation and preview are available.
3. Change history entry appears after publish.
4. Authorization and write access are enforced via backend authz responses.

### FE-009 Admin content management screens
Estimate: 1.5 days
Dependencies: FE-007, BE-010
Acceptance Criteria:
1. Admin can create, edit, and archive records.
2. Bulk update path exists for spreadsheet refresh.
3. Admin can review claim queue and verification status.
4. All admin operations use backend admin-safe endpoints.

### FE-012 Investor-ready visual polish and storytelling
Estimate: 1 day
Dependencies: FE-011
Acceptance Criteria:
1. Visual consistency is strong across all pages.
2. Empty/loading/error states look intentional.
3. Demo flow can be presented without design gaps.

### FE-013 Navigator chatbot interface
Estimate: 1.5 days
Dependencies: FE-003, BE-014
Acceptance Criteria:
1. Navigator route supports chat-first onboarding with message thread, composer, and loading/error states.
2. Chat requests use backend conversational endpoint only.
3. Session id is persisted client-side for refresh-safe resume.
4. Derived context is visible to users as editable chips or summary labels.

### FE-014 Conversational recommendation cards and feedback
Estimate: 1 day
Dependencies: FE-013, BE-015
Acceptance Criteria:
1. Chat responses render structured recommendation cards with rationale, tags, and official links.
2. Users can request refinement intents (for example broader, narrower, more like this) from the chat UI.
3. Recommendation feedback actions (thumbs up/down) are captured via backend feedback endpoint.
4. Recommendation rendering stays aligned with backend contract and handles partial data gracefully.

### FE-015 Chat accessibility and mobile hardening
Estimate: 1 day
Dependencies: FE-013, FE-014, BE-016
Acceptance Criteria:
1. Chat flow is fully keyboard accessible, including message traversal and recommendation card actions.
2. Screen reader labels announce role and message boundaries clearly.
3. Mobile layout keeps input/action controls visible and avoids nested scroll traps.
4. Failure states (LLM timeout/fallback) are communicated clearly without breaking the conversation flow.

## Frontend Build Order

1. FE-001 to FE-006, ensuring FE-005 includes filtered mindmap behavior.
2. FE-007.
3. FE-013 to FE-015.
4. FE-010 and FE-011, including investor mindmap validation and accessibility checks.
5. FE-008, FE-009, FE-012.