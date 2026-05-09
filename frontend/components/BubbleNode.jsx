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
      sector: "rgba(74, 144, 226, 0.15)",
      stage: "rgba(123, 104, 238, 0.15)",
      size: "rgba(80, 200, 120, 0.15)",
      location: "rgba(255, 107, 107, 0.15)"
    };
    return colors[type] || "rgba(100, 100, 100, 0.15)";
  };
  
  const getBorderColor = (type) => {
    const colors = {
      sector: "rgba(74, 144, 226, 0.6)",
      stage: "rgba(123, 104, 238, 0.6)",
      size: "rgba(80, 200, 120, 0.6)",
      location: "rgba(255, 107, 107, 0.6)"
    };
    return colors[type] || "rgba(100, 100, 100, 0.6)";
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
          boxShadow: "0 8px 24px rgba(0,0,0,0.2)"
        }
      }}
    >
      {/* Label positioned above bubble */}
      <Typography
        sx={{
          position: "absolute",
          top: -35,
          left: "50%",
          transform: "translateX(-50%)",
          fontSize: isZoomed ? "18px" : "14px",
          fontWeight: "bold",
          color: "#333",
          whiteSpace: "nowrap",
          background: "rgba(255, 255, 255, 0.9)",
          padding: "4px 12px",
          borderRadius: "12px",
          boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
          userSelect: "none",
          pointerEvents: "none"
        }}
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
