# GOED Webapp

## Project Overview

Build a production-quality web platform for the Utah Governor's Office of Economic Development (GOED) that combines:
1. A Founder Resource Navigator (personalized resource discovery).
2. A Utah Startup Map (interactive ecosystem map with company profiles).

The platform must work for two audiences:
1. Time-constrained founders seeking relevant support quickly.
2. Investors and ecosystem stakeholders evaluating Utah's startup landscape.

## Goals

1. Reduce resource discovery time to under 2 minutes for founders.
2. Provide clearly personalized recommendations based on founder context.
3. Showcase Utah startup companies through a filterable, interactive map.
4. Enable non-technical content updates for both resources and company data.
5. Deliver investor-ready visual polish and usability.

## Non-Negotiable Requirements

1. Working prototype: a live, clickable, usable product.
2. Personalized experience: recommendations and flows adapt to user type and stage.
3. Easily updatable content: non-technical admins can add/edit data without redeployment.
4. Map self-service profiles: businesses can add/claim/update listing with lightweight verification.
5. Required company profile fields are present.
6. Dual-audience readiness: useful for both founders and investors.
7. Production-quality UX/UI suitable for potential deployment on startup.utah.gov.

## Data Inputs

1. Resources spreadsheet (official starter dataset).
2. Map/company dataset (official starter dataset).
3. Existing startup.utah.gov content and structure for reference.

## 1. Utah Startup Map Requirements

### Core Capabilities

1. Interactive visual map of Utah startup ecosystem.
2. Company discovery through map browsing and filters.
3. Fast, responsive interaction with smooth zoom/pan/select behavior.
4. Company profile detail pages.

### Company Profile Requirements

Each company profile must include:
1. Company name.
2. Website.
3. Employee count.
4. Sector/industry.
5. Year founded.
6. LinkedIn URL.
7. Description.
8. Address/location.
9. Hiring status.
10. Job postings.
11. Photo gallery.

### Filtering and Search

Users must be able to filter by:
1. Sector.
2. Company size.
3. Stage.
4. Hiring status.
5. Location.

Search/discovery must encourage exploration and fast narrowing of results.

### Self-Service + Verification

1. Businesses can create new profile listings.
2. Businesses can claim existing listings.
3. Businesses can edit/update their own listings.
4. Include lightweight verification flow (for example: domain email verification, LinkedIn/company website confirmation, or admin approval queue).

### Map Acceptance Criteria

1. A user can discover relevant companies in less than 3 interactions after applying filters.
2. All required profile fields are visible and editable where permitted.
3. Profile claim/create flow prevents obvious spam entries.
4. Map and profile pages are mobile-friendly and desktop-ready.

## 2. Founder Resource Navigator Requirements

### Core Capabilities

1. Personalized resource discovery from state-provided programs.
2. Guidance flow that can be implemented as one or more of:
	- Guided questionnaire/quiz.
	- Smart filter interface.
	- AI assistant/chat interface.
3. Recommendations presented clearly with links and next actions.

### Personalization Dimensions

Recommendations should adapt using context such as:
1. Founder stage (idea, pre-seed, early-stage, growth).
2. Business type/industry.
3. Geography (urban/rural, county/city).
4. Founder attributes where relevant (for example veteran, woman-owned, university researcher).
5. Current objective (funding, mentorship, commercialization, export, hiring, etc.).

### Resource Result Requirements

For each recommended program/resource, include at minimum:
1. Program name.
2. Short description.
3. Why it matches this founder/context.
4. Link to official source.
5. Category/tags.

### Updateability Requirements

1. Non-technical users can add/edit/archive resources.
2. Content updates do not require code changes or redeployment.
3. Changes are reflected in user-facing search/recommendation results.

### Resource Navigator Acceptance Criteria

1. First-time users can complete onboarding/intake and see tailored results in under 2 minutes.
2. Distinct personas receive meaningfully different top recommendations.
3. Users can quickly identify next best action from recommendation cards/pages.
4. Broken/invalid resource links are detectable and manageable.

## 3. End-to-End User Flows

### Founder Journey

1. Land on platform and choose goal (find resources, explore companies, or both).
2. Provide context through intake flow.
3. Receive personalized resources.
4. Optionally explore relevant companies on map.
5. Save/share relevant resources or company profiles.

### Company Owner Journey

1. Find existing listing or create new profile.
2. Verify ownership/legitimacy via lightweight flow.
3. Update profile details and media.
4. Publish updates and verify changes are visible.

### Investor Journey

1. Open map and apply strategic filters.
2. Review profile quality, hiring signals, and sectors.
3. Quickly evaluate ecosystem breadth and opportunity clusters.

## 4. Test Personas (Validation Set)

The platform should be validated against these personas with clearly different outcomes:
1. Jordan, 20, Salt Lake City, pre-seed, first-time founder.
2. Maria, 38, Washington County, rural woman-owned agricultural business looking to scale.
3. Marcus, 34, Ogden (Weber County), veteran, manufacturing startup.
4. Priya, 31, Salt Lake City, B2B SaaS founder ready for first VC/angel raise.
5. David, 45, Provo (Utah County), med-device growth-stage company expanding internationally.
6. Dr. Amir, 29, Salt Lake City, university researcher commercializing novel technology.

## 5. Quality and Non-Functional Requirements

1. Performance: key pages load quickly on standard broadband/mobile networks.
2. Accessibility: semantic structure, keyboard support, and sufficient contrast.
3. Responsive design: desktop, tablet, and mobile support.
4. Reliability: graceful handling of missing/incomplete data.
5. Maintainability: clear content model and admin update path.
6. Security: basic protection for self-service submission and profile claims.

## 6. Judging Alignment (Priority Weights)

Implementation should prioritize:
1. 30% Usability and experience.
2. 25% Technical execution.
3. 25% Design and visual impact.
4. 20% Innovation and creativity.

## 7. Recommended MVP Scope

To maximize execution quality if time is constrained:
1. Deliver one polished, complete product first (Navigator or Map).
2. If both are included, keep fundamentals complete for each before advanced features.
3. Prefer depth and reliability over breadth of partially implemented ideas.

## 8. Deliverable Definition of Done

1. Deployed web app with live functionality.
2. Founder navigator provides personalized recommendations from dataset.
3. Startup map supports interactive exploration and required profile fields.
4. Self-service listing/claim flow is functional with basic verification.
5. Non-technical update path is documented and usable.
6. Persona-based test run shows distinct, relevant outcomes.
7. Visual quality is presentation-ready for GOED and investor demo use.

