## Plan: Filtered Map to 2D Company Mindmap

Implement FE-005 and BE-007 together so applying filters transforms the map experience into a 2D mindmap of companies, while preserving map parity through a view toggle and shared query state. This approach satisfies MVP scope, keeps the feature investor-focused, and reduces risk by introducing backend filter APIs first, then frontend visualization/state orchestration, then performance/accessibility hardening.

**Steps**
1. Phase 1: Define and lock API contract for filtered company results (blocks all UI work).
2. In backend, add BE-007 company listing and detail endpoints in /home/akrucken/dev/goed-hackathon/backend/app/routes.py with support for sector, size, stage, hiring status, and location query parameters; include pagination and explicit response schema for lightweight node rendering (name-first payload plus optional metadata).
3. Add query parsing and SQLAlchemy filtering in backend service/repository logic using the existing Company model in /home/akrucken/dev/goed-hackathon/backend/app/models.py, with a compatibility shim for legacy model field names versus migration schema names.
4. Add API-level validation and error normalization (bad filter values, empty results, invalid paging) and include structured logging points for mindmap-related request telemetry, aligned with BE-013 patterns.
5. Phase 2: Build shared frontend data/state layer (depends on 1-4).
6. In /home/akrucken/dev/goed-hackathon/frontend/app/map/page.jsx, replace placeholder content with map workspace state: filter model, result collection, loading/error states, and current visualization mode.
7. Persist filter state in URL search params (single source of truth) so back/forward navigation and shareable links preserve context; API calls should derive only from URL state.
8. Add a map-to-mindmap behavior rule: applying filters auto-switches to mindmap mode (per decision), with an explicit toggle to return to geographic map without resetting filters.
9. Phase 3: Implement 2D mindmap rendering and interactions (depends on 5-8).
10. Introduce a dedicated mindmap component under /home/akrucken/dev/goed-hackathon/frontend/components/ (new file) that renders Sector -> Stage -> Company hierarchy from filtered API data.
11. Keep company nodes lightweight by default (name-only primary label), with optional progressive disclosure panel on selection.
12. Enable in-mindmap filter edits (full filter controls available in mindmap mode) and trigger debounced refetch/re-render loops.
13. Add mobile-specific behavior: simplified hierarchy with drill-down navigation to avoid dense graph rendering on small screens.
14. Phase 4: Analytics, performance, and quality hardening (parallel with late Phase 3 polish).
15. Extend /home/akrucken/dev/goed-hackathon/frontend/lib/analytics.js with map/mindmap events (view_entered, filter_applied, node_selected, profile_opened) and include active-filter payload dimensions.
16. Add frontend empty/loading/error states and no-results narrative optimized for investor pattern discovery.
17. Validate keyboard navigation semantics and focus management for node traversal; ensure responsive behavior for mobile and desktop baselines.
18. Phase 5: Persona-oriented validation and acceptance (depends on 14-17).
19. Run investor-centered scenarios using strategic filters and verify discovery quality outcomes (pattern visibility, cluster comprehension, profile drill-through usefulness).
20. Confirm FE-005 acceptance criteria still hold in both views (zoom/pan/select/clustering for map mode; quick filter-to-result updates; clear empty states), and confirm BE-007 filter completeness and response suitability.

**Relevant files**
- /home/akrucken/dev/goed-hackathon/frontend/app/map/page.jsx - replace placeholder route with integrated filter/query/view orchestration.
- /home/akrucken/dev/goed-hackathon/frontend/lib/analytics.js - extend event instrumentation beyond landing CTA tracking.
- /home/akrucken/dev/goed-hackathon/frontend/components/SiteShell.jsx - reuse shell/layout patterns and responsive behavior conventions.
- /home/akrucken/dev/goed-hackathon/backend/app/routes.py - add company list/detail endpoints and request validation.
- /home/akrucken/dev/goed-hackathon/backend/app/models.py - reuse Company ORM model and resolve field mapping constraints.
- /home/akrucken/dev/goed-hackathon/backend/db/migrations/0001_be002_core_schema.sql - source of truth for required map/company filter dimensions and indexed fields.
- /home/akrucken/dev/goed-hackathon/frontend/implementation_tickets.md - FE-005/FE-011 acceptance and quality gates.
- /home/akrucken/dev/goed-hackathon/backend/implementation_tickets.md - BE-007 dependency/order and API acceptance.
- /home/akrucken/dev/goed-hackathon/project_requirements.md - map acceptance (<3 interactions), dual-audience behavior, and mobile/desktop requirements.

**Verification**
1. Backend: call company list endpoint with each filter independently and in combinations; verify deterministic paging and schema shape.
2. Backend: validate empty-result and invalid-filter responses with consistent error structure and status codes.
3. Frontend: apply filters and verify auto-transition to mindmap mode occurs without losing URL/search-param state.
4. Frontend: toggle back to map and confirm filters persist and datasets remain synchronized.
5. Frontend: in mindmap mode, edit filters and verify debounced refresh plus stable layout updates.
6. Frontend: mobile viewport test confirms simplified drill-down behavior and avoids unreadable dense rendering.
7. Analytics: verify event emission for view enter, filter apply, node select, and profile open with expected payload keys.
8. Product acceptance: investor scenario walkthrough validates improved pattern discovery quality while preserving FE-005 speed/usability criteria.

**Decisions**
- Included scope: MVP delivery now.
- Included scope: auto-transform behavior after filter apply.
- Included scope: hierarchy model is Sector -> Stage -> Company.
- Included scope: full filter editability within mindmap mode.
- Included scope: company node default detail is name-only for visual clarity.
- Included scope: mobile uses simplified hierarchy plus drill-down interaction.
- Primary success signal: investor pattern discovery quality.
- Excluded for now: advanced graph relationships beyond filter hierarchy (for example force-directed affinity links).
- Excluded for now: replacing map mode as the sole visualization (map remains available via toggle and parity checks).

**Further Considerations**
1. Data model alignment strategy: either normalize Company ORM fields to migration schema now (lower long-term risk) or add temporary mapping adapter for MVP speed.
2. Mindmap rendering library choice: choose between custom SVG (higher control) and lightweight visualization dependency (faster build) based on timebox.
3. Profile panel richness: keep node-only minimal at launch, then layer additional metadata in side panel if investor testing requests it.
