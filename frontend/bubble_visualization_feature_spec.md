# Bubble Visualization Feature Specification

## Overview
Replace the existing "mindmap" view with an interactive bubble/cluster visualization that displays companies grouped by filter categories (sector, size, stage, location). The map fades out and bubbles fade in with a scale animation when any filter is applied.

## Feature Requirements

### 1. View Behavior
- **Replaces**: Current mindmap view entirely
- **Trigger**: Any active filter (sector, size, stage, or location)
- **Return**: Clearing all filters returns to map view automatically
- **Component**: New `BubbleClusterView` component to replace mindmap rendering

### 2. Visual Layout

#### Bubble Arrangement
- **Layout Algorithm**: Force-directed layout (physics-based simulation)
- **Library**: D3.js for full control and power
- **Behavior**: Bubbles naturally push apart and settle into an organic layout

#### Bubble Sizing
- **Proportional**: Bubble size based on number of companies in category
- **Constraints**: Implement min/max limits to prevent extremely tiny or huge bubbles
- **Recommended Range**: 
  - Minimum: 80px diameter
  - Maximum: 300px diameter
  - Scale factor: `sqrt(companyCount)` for better visual proportion

#### Bubble Styling
- **Border**: Subtle stroke (2-3px solid)
- **Background**: Semi-transparent fill
- **Label Position**: Above/outside the bubble
- **Label Content**: Category name + count (e.g., "Fintech (23)")
- **Typography**: 
  - Category name: Bold, 16-18px
  - Count: Regular, 14px

### 3. Company Representation

#### Icon Style
- **Reuse Existing**: Same colored letter icons from map (`LeafletClusterMap`)
- **Size**: 32-40px diameter circles
- **Letter**: First letter of company name (uppercase)
- **Color**: Individual letter-based colors from existing map (NOT category-based colors)
- **Positioning**: Distributed within parent bubble using force simulation

#### Zoom State
- When zoomed into a bubble:
  - Companies spread out for better visibility
  - Company names displayed below icons
  - Increased spacing between company nodes
  - Name typography: 12px, truncated if too long

### 4. Interactions

#### Click Category Bubble
- **Action**: Zoom into that bubble
- **Visual Effect**: 
  - Smooth camera transition (1-1.5s)
  - Selected bubble grows to fill most of viewport
  - Companies spread out within the expanded bubble
  - Company names become visible
  - Other bubbles fade out or shrink to edges
- **Exit**: Click outside or "Back" button to return to all bubbles

#### Click Company Icon
- **Action**: Show company detail panel/popup (same as map view)
- **Implementation**: Reuse existing `selectedCompanyId` state and detail panel component
- **Visual**: Highlight selected company icon (scale up slightly, add glow)

#### Hover Effects
- **Bubble Hover**: Subtle scale (1.05x), shadow enhancement
- **Company Hover**: Scale (1.1x), show company name tooltip
- **Cursor**: Pointer on all interactive elements

### 5. Animation & Transitions

#### Initial Render (Map → Bubbles)
- **Map**: Fade out over 400ms
- **Bubbles**: 
  - Start from center point at 0 scale
  - Scale up to final size over 600ms
  - Ease function: `easeBackOut` for slight overshoot effect
  - Fade in from 0 to 1 opacity over 400ms (delayed 200ms)
- **Total Duration**: ~800ms

#### Exit (Bubbles → Map)
- **Bubbles**: Scale down to center + fade out over 400ms
- **Map**: Fade in over 400ms (delayed 200ms)
- **Total Duration**: ~600ms

#### Force Simulation
- **Initial**: Allow 300-500 iterations for layout settlement before showing
- **Interactive**: Continuous simulation with damping for smooth repositioning

### 6. Multi-Filter Handling

#### Hierarchical Nesting
When multiple filters are active (e.g., sector=fintech AND stage=seed):
- **Primary Level**: Outer bubbles represent primary filter (e.g., sectors)
- **Secondary Level**: Inner sub-bubbles represent secondary filter (e.g., stages within that sector)
- **Companies**: Positioned within the innermost applicable bubble
- **Visual Hierarchy**: 
  - Primary bubbles: Larger, bold labels
  - Secondary bubbles: Smaller, nested inside primary
  - Use z-index and borders to show containment

#### Filter Priority
1. Sector (if active) → primary level
2. Stage (if active) → secondary level
3. Size (if active) → secondary or tertiary level
4. Location (if active) → secondary or tertiary level

### 7. Responsive Design

#### Desktop (≥960px)
- Full force-directed layout
- Large bubbles with comfortable spacing
- All labels visible

#### Tablet (600-960px)
- Scaled-down layout
- Slightly reduced bubble sizes
- May need to scroll/pan

#### Mobile (<600px)
- Simplified layout or vertical stack
- Touch-friendly targets (min 44px)
- Consider alternative layout (list with visual grouping) if force-directed is too cramped

### 8. Data Structure

```javascript
// Expected data format from backend
{
  categories: [
    {
      id: "fintech",
      label: "Fintech",
      type: "sector", // or "size", "stage", "location"
      companies: [
        { id: 1, name: "Company A", ... },
        { id: 2, name: "Company B", ... }
      ],
      subcategories: [ // for hierarchical nesting
        {
          id: "fintech-seed",
          label: "Seed",
          type: "stage",
          companies: [...]
        }
      ]
    }
  ]
}
```

### 9. Technical Implementation

#### Component Structure
```
frontend/
  components/
    BubbleClusterView.jsx         # Main container
    BubbleNode.jsx                # Individual category bubble
    CompanyNode.jsx               # Individual company icon (reusable)
    ForceSimulation.js            # D3 force simulation logic
    BubbleClusterControls.jsx     # Zoom controls, back button
```

#### State Management
- Reuse existing state from `map/page.jsx`:
  - `appliedFilters`
  - `selectedCompanyId`
  - `companiesPayload`
- New state:
  - `bubbleZoomTarget` - which bubble is zoomed (null = all visible)
  - `simulationNodes` - D3 simulation data
  - `isTransitioning` - prevent interaction during animation

#### Dependencies
```json
{
  "d3-force": "^3.0.0",
  "d3-scale": "^4.0.0",
  "d3-selection": "^3.0.0",
  "d3-transition": "^3.0.0",
  "d3-ease": "^3.0.1"
}
```

### 10. Performance Considerations

- **Large Datasets**: If >500 companies visible, consider:
  - Aggressive min bubble size to reduce company icons shown
  - Virtualization for company nodes
  - Render preview icons only (full icons on zoom)
- **Force Simulation**: 
  - Limit iterations with `alphaMin` and `alphaDecay`
  - Use quadtree for collision detection optimization
  - Disable simulation when view is inactive
- **Animation**: Use `requestAnimationFrame` for smooth 60fps

### 11. Accessibility

- **Keyboard Navigation**: 
  - Tab through bubbles and companies
  - Enter to select/zoom
  - Escape to go back
- **Screen Readers**:
  - ARIA labels for all interactive elements
  - Announce category and company counts
  - Describe current zoom state
- **Focus Management**: 
  - Visible focus indicators
  - Focus trap when zoomed into bubble

### 12. Testing Scenarios

1. **Single filter active** (e.g., sector=fintech)
   - Verify bubbles appear with correct grouping
   - Check animation timing

2. **Multiple filters active** (e.g., sector + stage)
   - Verify hierarchical nesting works
   - Check sub-bubble positioning

3. **Zoom interaction**
   - Click bubble → verify zoom
   - Click outside → verify return
   - Click company → verify detail panel

4. **Clear filters**
   - Verify smooth transition back to map
   - Check state cleanup

5. **Edge cases**
   - Empty category (0 companies)
   - Single category with many companies (>100)
   - Many categories with few companies each

## Implementation Phases

### Phase 1: Core Visualization (MVP)
- [ ] Install D3.js dependencies
- [ ] Create `BubbleClusterView` component with basic force layout
- [ ] Render category bubbles with labels and counts
- [ ] Implement company icon positioning within bubbles
- [ ] Basic click handlers (bubble and company)

### Phase 2: Polish & Interactions
- [ ] Implement scale + fade animations
- [ ] Add zoom functionality for bubble selection
- [ ] Integrate with existing company detail panel
- [ ] Refine force simulation parameters
- [ ] Add hover effects

### Phase 3: Advanced Features
- [ ] Hierarchical nesting for multi-filter scenarios
- [ ] Responsive layout adjustments
- [ ] Performance optimizations
- [ ] Accessibility enhancements

### Phase 4: Testing & Refinement
- [ ] User testing
- [ ] Performance testing with large datasets
- [ ] Cross-browser testing
- [ ] Animation timing tweaks

## Success Criteria

- ✓ Map smoothly transitions to bubbles when any filter applied
- ✓ Bubbles accurately group companies by filter category
- ✓ Company icons maintain consistent visual style from map
- ✓ Zoom interaction provides clear view of companies within category
- ✓ Performance remains smooth with 100+ companies visible
- ✓ Animations feel natural and polished (60fps)
- ✓ Works across desktop, tablet, and mobile
- ✓ Accessible via keyboard and screen readers

## Open Questions / Future Enhancements

1. Should we support filtering while in bubble view, or require return to map?
2. Consider adding a "search" feature to highlight specific companies across bubbles
3. Potential for multiple zoom levels (sector → stage → company detail)
4. Export/share functionality for current bubble view
5. Animation prefers vs accessibility (reduced motion support)
