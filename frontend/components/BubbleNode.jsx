"use client";

import { Box, Typography } from "@mui/material";
import { formatBubbleLabel } from "@/lib/forceSimulation";
import CompanyNode from "./CompanyNode";
import { useEffect, useState } from "react";
import { createCompanySimulation } from "@/lib/forceSimulation";

/**
 * BubbleNode - Represents a category bubble containing company icons
 */
export default function BubbleNode({
  bubble,
  x,
  y,
  radius,
  isZoomed = false,
  selectedCompanyId,
  onBubbleClick,
  onCompanyClick,
  scale = 1,
  opacity = 1,
  pointerEvents = "auto"
}) {
  const [companyNodes, setCompanyNodes] = useState([]);
  const [simulation, setSimulation] = useState(null);
  
  // Calculate bubble color based on type
  const getBubbleColor = (type) => {
    const colors = {
      sector: "rgba(56, 189, 248, 0.14)",
      stage: "rgba(34, 211, 238, 0.14)",
      size: "rgba(52, 211, 153, 0.14)",
      location: "rgba(16, 185, 129, 0.14)"
    };
    return colors[type] || "rgba(148, 163, 184, 0.12)";
  };

  const getBorderColor = (type) => {
    const colors = {
      sector: "rgba(56, 189, 248, 0.55)",
      stage: "rgba(34, 211, 238, 0.55)",
      size: "rgba(52, 211, 153, 0.55)",
      location: "rgba(16, 185, 129, 0.55)"
    };
    return colors[type] || "rgba(148, 163, 184, 0.45)";
  };
  
  // Initialize company positions with force simulation
  useEffect(() => {
    if (bubble.companies && bubble.companies.length > 0) {
      const { simulation: newSimulation, nodes } = createCompanySimulation(
        bubble.companies,
        radius * 0.85, // Use 85% of bubble radius for company area
        0, // Relative to bubble center
        0
      );
      
      // Update company positions on each tick
      newSimulation.on("tick", () => {
        setCompanyNodes([...nodes]);
      });
      
      // Let simulation run longer to ensure proper settling without overlap
      // Run enough iterations based on company count
      const iterations = Math.min(200, 100 + bubble.companies.length * 2);
      newSimulation.tick(iterations);
      
      setSimulation(newSimulation);
      setCompanyNodes(nodes);
      
      return () => {
        newSimulation.stop();
      };
    }
  }, [bubble.companies, radius]);
  
  const handleBubbleClick = (e) => {
    e.stopPropagation();
    if (onBubbleClick) {
      onBubbleClick(bubble);
    }
  };
  
  const handleCompanyClick = (company) => {
    if (onCompanyClick) {
      onCompanyClick(company.id);
    }
  };
  
  const bgColor = getBubbleColor(bubble.type);
  const borderColor = getBorderColor(bubble.type);
  const labelText = formatBubbleLabel(bubble.label, bubble.count);
  
  // Adjust company icon size based on zoom
  const companyRadius = isZoomed ? 25 : 18;
  
  return (
    <Box
      onClick={handleBubbleClick}
      sx={{
        position: "absolute",
        left: x - radius,
        top: y - radius,
        width: radius * 2,
        height: radius * 2,
        borderRadius: "50%",
        border: `3px solid ${borderColor}`,
        background: bgColor,
        cursor: "pointer",
        transition: "all 0.3s ease, opacity 0.5s ease",
        transform: `scale(${scale})`,
        transformOrigin: "center",
        opacity: opacity,
        pointerEvents: pointerEvents,
        "&:hover": {
          transform: `scale(${scale * 1.05})`,
          boxShadow: "0 8px 28px rgba(0,0,0,0.45)"
        }
      }}
    >
      {/* Label positioned above bubble */}
      <Typography
        sx={(theme) => ({
          position: "absolute",
          top: -35,
          left: "50%",
          transform: "translateX(-50%)",
          fontSize: isZoomed ? "18px" : "14px",
          fontWeight: "bold",
          color: theme.palette.text.primary,
          whiteSpace: "nowrap",
          background: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
          padding: "4px 12px",
          borderRadius: "12px",
          boxShadow: "0 4px 14px rgba(0,0,0,0.35)",
          userSelect: "none",
          pointerEvents: "none"
        })}
      >
        {labelText}
      </Typography>
      
      {/* Company icons */}
      {companyNodes.map((node) => (
        <CompanyNode
          key={node.id}
          company={node}
          x={radius + node.x} // Offset by bubble radius since node positions are relative to center
          y={radius + node.y}
          radius={companyRadius}
          isZoomed={isZoomed}
          isSelected={node.id === selectedCompanyId}
          onClick={handleCompanyClick}
        />
      ))}
    </Box>
  );
}
