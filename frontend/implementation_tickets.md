# Frontend Implementation Tickets

## P0 Core

### FE-001 Frontend app bootstrap and design system foundation
Estimate: 0.5 day
Dependencies: None
Acceptance Criteria:
1. Responsive shell with desktop and mobile nav.
2. Shared color, type, spacing tokens are implemented.
3. Accessibility baseline is configured.

### FE-002 Landing page and mode selection
Estimate: 0.5 day
Dependencies: FE-001
Acceptance Criteria:
1. User can choose navigator or map flow quickly.
2. Value proposition is clear in under one screen.
3. CTA paths are measurable and trackable.

### FE-003 Founder intake experience
Estimate: 1 day
Dependencies: FE-001
Acceptance Criteria:
1. Intake completes in under 2 minutes for typical users.
2. Validation errors are clear and recoverable.
3. Progress state is preserved during navigation.

### FE-004 Personalized recommendations UI
Estimate: 1 day
Dependencies: FE-003
Acceptance Criteria:
1. Each recommendation shows why it matches.
2. Resource cards include direct links and tags.
3. Users can compare or save items for later.

### FE-005 Interactive Utah startup map
Estimate: 2 days
Dependencies: FE-001
Acceptance Criteria:
1. Map supports zoom, pan, marker select, and clustered points.
2. Filter changes update map and list view quickly.
3. Empty-state and no-result handling are clear.

### FE-006 Company profile page
Estimate: 1 day
Dependencies: FE-005
Acceptance Criteria:
1. All required fields are displayed cleanly.
2. Job postings and media gallery render correctly.
3. External links are validated and safe.

### FE-007 Self-service create and claim flows
Estimate: 1.5 days
Dependencies: FE-006
Acceptance Criteria:
1. User can create or claim with clear guidance.
2. Verification state and next steps are visible.
3. Owner edit access appears only when authorized.

### FE-010 Persona validation harness
Estimate: 0.5 day
Dependencies: FE-004, FE-005
Acceptance Criteria:
1. Persona presets can run end-to-end quickly.
2. Output differences are visible and explainable.
3. Screenshots or logs can be exported for demo evidence.

### FE-011 Performance and accessibility pass
Estimate: 1 day
Dependencies: FE-004, FE-005, FE-006
Acceptance Criteria:
1. Core user flows remain smooth on mid-range mobile.
2. Keyboard navigation works across critical interactions.
3. Contrast and semantic structure meet accessibility baseline.

## P1 Hardening

### FE-008 Company owner edit dashboard
Estimate: 1 day
Dependencies: FE-007
Acceptance Criteria:
1. Owner can update all editable fields.
2. Validation and preview are available.
3. Change history entry appears after publish.

### FE-009 Admin content management screens
Estimate: 1.5 days
Dependencies: FE-007
Acceptance Criteria:
1. Admin can create, edit, and archive records.
2. Bulk update path exists for spreadsheet refresh.
3. Admin can review claim queue and verification status.

### FE-012 Investor-ready visual polish and storytelling
Estimate: 1 day
Dependencies: FE-011
Acceptance Criteria:
1. Visual consistency is strong across all pages.
2. Empty/loading/error states look intentional.
3. Demo flow can be presented without design gaps.

## Frontend Build Order

1. FE-001 to FE-006.
2. FE-007.
3. FE-010 and FE-011.
4. FE-008, FE-009, FE-012.