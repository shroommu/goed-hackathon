import {
  forceSimulation,
  forceCollide,
  forceCenter,
  forceManyBody,
  forceX,
  forceY,
} from "d3-force";
import { scaleLinear, scaleSqrt } from "d3-scale";

// Configuration constants
const BUBBLE_MIN_RADIUS = 40;
const BUBBLE_MAX_RADIUS = 300; // Increased to accommodate more companies
const COMPANY_ICON_RADIUS = 20;
const COMPANY_SPACING = 5;

/**
 * Calculate bubble radius based on company count with min/max constraints
 * Ensures bubble is large enough to fit all company icons without overlap
 */
export function calculateBubbleRadius(companyCount) {
  if (companyCount === 0) return BUBBLE_MIN_RADIUS;

  // Calculate minimum radius needed to fit all company icons without overlap
  // Each company icon needs space for its radius + spacing
  const iconDiameter = (COMPANY_ICON_RADIUS + COMPANY_SPACING) * 2;

  // Estimate area needed for all icons (with packing efficiency ~0.65)
  // We use 80% of bubble area to leave margin from edge
  const packingEfficiency = 0.65;
  const usableAreaFraction = 0.8;
  const totalIconArea =
    (companyCount * Math.PI * iconDiameter * iconDiameter) / 4;
  const requiredBubbleArea =
    totalIconArea / (packingEfficiency * usableAreaFraction);
  const minRequiredRadius = Math.sqrt(requiredBubbleArea / Math.PI);

  // Use square root scaling for aesthetic proportion, but ensure minimum is met
  const scale = scaleSqrt()
    .domain([1, 100]) // Assume max ~100 companies per category
    .range([BUBBLE_MIN_RADIUS, BUBBLE_MAX_RADIUS])
    .clamp(true);

  const aestheticRadius = scale(companyCount);

  // Return the larger of minimum required or aesthetic radius
  return Math.max(minRequiredRadius, aestheticRadius, BUBBLE_MIN_RADIUS);
}

/**
 * Transform filtered companies data into bubble hierarchy
 * Note: The backend already filters companies based on filters,
 * and the mindmap only contains sectors/stages present in those filtered results.
 */
export function buildBubbleHierarchy(companiesPayload, filters) {
  const bubbles = [];
  const items = companiesPayload.items || [];
  const hasMindmap =
    companiesPayload.mindmap?.sectors &&
    companiesPayload.mindmap.sectors.length > 0;

  // Determine primary grouping based on which filters are active
  // Priority: sector > stage > size > location
  if (filters.sector) {
    if (hasMindmap) {
      // Group by sector using mindmap structure
      const sectors = companiesPayload.mindmap.sectors;
      sectors.forEach((sector) => {
        const companies = getAllCompaniesFromSector(sector);
        if (companies.length > 0) {
          bubbles.push({
            id: `sector-${sector.name}`,
            label: sector.name,
            type: "sector",
            count: companies.length,
            companies: companies,
            subcategories: filters.stage
              ? buildStageSubcategories(sector, filters)
              : [],
          });
        }
      });
    } else if (items.length > 0) {
      // Fallback: group items directly by their sector field
      const sectorGroups = {};
      items.forEach((company) => {
        const sector = company.sector || "Unknown";
        if (!sectorGroups[sector]) {
          sectorGroups[sector] = [];
        }
        sectorGroups[sector].push(company);
      });

      Object.entries(sectorGroups).forEach(([sectorName, companies]) => {
        if (companies.length > 0) {
          bubbles.push({
            id: `sector-${sectorName}`,
            label: sectorName,
            type: "sector",
            count: companies.length,
            companies: companies.map((c) => ({
              id: c.id,
              name: c.startup_name,
            })),
            subcategories: [],
          });
        }
      });
    }
  } else if (filters.stage) {
    if (hasMindmap) {
      // Group by stage across all sectors (mindmap already filtered)
      const stageGroups = {};
      const sectors = companiesPayload.mindmap.sectors;

      sectors.forEach((sector) => {
        (sector.stages || []).forEach((stage) => {
          if (!stageGroups[stage.name]) {
            stageGroups[stage.name] = [];
          }
          stageGroups[stage.name].push(...(stage.companies || []));
        });
      });

      Object.entries(stageGroups).forEach(([stageName, companies]) => {
        if (companies.length > 0) {
          bubbles.push({
            id: `stage-${stageName}`,
            label: stageName,
            type: "stage",
            count: companies.length,
            companies: companies,
            subcategories: [],
          });
        }
      });
    } else if (items.length > 0) {
      // Fallback: group items directly by their stage field
      const stageGroups = {};
      items.forEach((company) => {
        const stage = company.stage || "Unknown";
        if (!stageGroups[stage]) {
          stageGroups[stage] = [];
        }
        stageGroups[stage].push(company);
      });

      Object.entries(stageGroups).forEach(([stageName, companies]) => {
        if (companies.length > 0) {
          bubbles.push({
            id: `stage-${stageName}`,
            label: stageName,
            type: "stage",
            count: companies.length,
            companies: companies.map((c) => ({
              id: c.id,
              name: c.startup_name,
            })),
            subcategories: [],
          });
        }
      });
    }
  } else if (filters.size && items.length > 0) {
    // Group by size
    const sizeGroups = {};
    companiesPayload.items.forEach((company) => {
      const size = company.size || "unknown";
      if (!sizeGroups[size]) {
        sizeGroups[size] = [];
      }
      sizeGroups[size].push(company);
    });

    Object.entries(sizeGroups).forEach(([size, companies]) => {
      if (companies.length > 0) {
        bubbles.push({
          id: `size-${size}`,
          label: size,
          type: "size",
          count: companies.length,
          companies: companies,
          subcategories: [],
        });
      }
    });
  } else if (filters.location && items.length > 0) {
    // Group by location (backend has already filtered, group all returned items)
    const locationGroups = {};
    items.forEach((company) => {
      const location = company.city || "unknown";
      if (!locationGroups[location]) {
        locationGroups[location] = [];
      }
      locationGroups[location].push(company);
    });

    Object.entries(locationGroups).forEach(([location, companies]) => {
      if (companies.length > 0) {
        bubbles.push({
          id: `location-${location}`,
          label: location,
          type: "location",
          count: companies.length,
          companies: companies,
          subcategories: [],
        });
      }
    });
  }

  return bubbles;
}

/**
 * Helper to get all companies from a sector (flattened from stages)
 */
function getAllCompaniesFromSector(sector) {
  const companies = [];
  (sector.stages || []).forEach((stage) => {
    companies.push(...(stage.companies || []));
  });
  return companies;
}

/**
 * Build stage subcategories for hierarchical nesting
 */
function buildStageSubcategories(sector, filters) {
  const subcategories = [];

  (sector.stages || []).forEach((stage) => {
    const companies = stage.companies || [];
    if (companies.length > 0) {
      subcategories.push({
        id: `stage-${stage.name}`,
        label: stage.name,
        type: "stage",
        count: companies.length,
        companies: companies,
      });
    }
  });

  return subcategories;
}

/**
 * Create force simulation for bubble layout
 */
export function createBubbleSimulation(bubbles, width, height) {
  // Create nodes with positions and radii
  const nodes = bubbles.map((bubble, i) => ({
    ...bubble,
    radius: calculateBubbleRadius(bubble.count),
    x: width / 2 + (Math.random() - 0.5) * 100, // Start near center with slight randomness
    y: height / 2 + (Math.random() - 0.5) * 100,
    vx: 0,
    vy: 0,
  }));

  // Create simulation
  const simulation = forceSimulation(nodes)
    .force("charge", forceManyBody().strength(-200))
    .force("center", forceCenter(width / 2, height / 2))
    .force(
      "collision",
      forceCollide()
        .radius((d) => d.radius + 20)
        .strength(0.9),
    )
    .force("x", forceX(width / 2).strength(0.05))
    .force("y", forceY(height / 2).strength(0.05))
    .alphaDecay(0.02) // Slow decay for smoother settling
    .velocityDecay(0.3); // Some friction

  return { simulation, nodes };
}

/**
 * Create force simulation for company icons within a bubble
 */
export function createCompanySimulation(
  companies,
  bubbleRadius,
  bubbleX,
  bubbleY,
) {
  // Calculate positions for companies within the bubble
  const nodes = companies.map((company, i) => ({
    ...company,
    radius: COMPANY_ICON_RADIUS,
    x: bubbleX + (Math.random() - 0.5) * bubbleRadius,
    y: bubbleY + (Math.random() - 0.5) * bubbleRadius,
    vx: 0,
    vy: 0,
  }));

  // Constrain companies within the parent bubble
  const constrainToBubble = (alpha) => {
    nodes.forEach((node) => {
      const dx = node.x - bubbleX;
      const dy = node.y - bubbleY;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const maxDistance = bubbleRadius - node.radius - COMPANY_SPACING;

      if (distance > maxDistance) {
        const angle = Math.atan2(dy, dx);
        node.x = bubbleX + Math.cos(angle) * maxDistance;
        node.y = bubbleY + Math.sin(angle) * maxDistance;
        node.vx = 0;
        node.vy = 0;
      }
    });
  };

  const simulation = forceSimulation(nodes)
    .force("charge", forceManyBody().strength(-50)) // Increased repulsion to prevent overlap
    .force("center", forceCenter(bubbleX, bubbleY))
    .force(
      "collision",
      forceCollide()
        .radius(COMPANY_ICON_RADIUS + COMPANY_SPACING)
        .strength(1.0),
    ) // Stronger collision with proper spacing
    .force("constrain", constrainToBubble)
    .alphaDecay(0.03) // Slower decay for better settling
    .velocityDecay(0.5); // More friction for stability

  return { simulation, nodes };
}

/**
 * Get color for company icon based on first letter
 */
export function getCompanyColor(companyName) {
  const firstLetter = (companyName || "?")[0].toUpperCase();
  const colorIndex = firstLetter.charCodeAt(0) % 10;
  const colors = [
    "#4A90E2",
    "#7B68EE",
    "#50C878",
    "#FF6B6B",
    "#FFA500",
    "#9B59B6",
    "#3498DB",
    "#E74C3C",
    "#1ABC9C",
    "#F39C12",
  ];
  return colors[colorIndex];
}

/**
 * Format category label with count
 */
export function formatBubbleLabel(label, count) {
  return `${label} (${count})`;
}
