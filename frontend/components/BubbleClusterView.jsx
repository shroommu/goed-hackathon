"use client";

import { Box, Button, Stack } from "@mui/material";
import { useEffect, useState, useRef } from "react";
import { buildBubbleHierarchy, createBubbleSimulation } from "@/lib/forceSimulation";
import BubbleNode from "./BubbleNode";

/**
 * BubbleClusterView - Main container for bubble visualization
 * Displays companies grouped by filter categories using force-directed layout
 */
export default function BubbleClusterView({
  companiesPayload,
  filters,
  selectedCompanyId,
  onSelectCompany,
  onClearFilters
}) {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [bubbleNodes, setBubbleNodes] = useState([]);
  const [simulation, setSimulation] = useState(null);
  const [zoomedBubble, setZoomedBubble] = useState(null);
  const [isVisible, setIsVisible] = useState(false);
  
  // Update dimensions on mount and resize
  useEffect(() => {
    if (!containerRef.current) return;
    
    const updateDimensions = () => {
      const rect = containerRef.current.getBoundingClientRect();
      setDimensions({
        width: rect.width,
        height: rect.height
      });
    };
    
    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    
    return () => {
      window.removeEventListener("resize", updateDimensions);
    };
  }, []);
  
  // Build bubble hierarchy and run simulation
  useEffect(() => {
    const bubbles = buildBubbleHierarchy(companiesPayload, filters);
    
    if (bubbles.length === 0) {
      setBubbleNodes([]);
      return;
    }
    
    const { simulation: newSimulation, nodes } = createBubbleSimulation(
      bubbles,
      dimensions.width,
      dimensions.height
    );
    
    // Update bubble positions on each tick
    newSimulation.on("tick", () => {
      setBubbleNodes([...nodes]);
    });
    
    setSimulation(newSimulation);
    setBubbleNodes(nodes);
    
    return () => {
      newSimulation.stop();
    };
  }, [companiesPayload, filters, dimensions]);
  
  // Trigger fade-in animation
  useEffect(() => {
    // Small delay to ensure render happens first
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 50);
    
    return () => clearTimeout(timer);
  }, []);
  
  const handleBubbleClick = (bubble) => {
    if (zoomedBubble?.id === bubble.id) {
      // Already zoomed, unzoom
      setZoomedBubble(null);
    } else {
      // Zoom into this bubble
      setZoomedBubble(bubble);
    }
  };
  
  const handleCompanyClick = (companyId) => {
    if (onSelectCompany) {
      onSelectCompany(companyId);
    }
  };
  
  const handleClearFilters = () => {
    setIsVisible(false);
    // Wait for fade out animation before clearing
    setTimeout(() => {
      if (onClearFilters) {
        onClearFilters();
      }
    }, 400);
  };
  
  const handleBackgroundClick = () => {
    if (zoomedBubble) {
      setZoomedBubble(null);
    }
  };
  
  // Calculate scale and position for zoomed bubble
  const getZoomedTransform = (bubble) => {
    if (!zoomedBubble || zoomedBubble.id !== bubble.id) {
      return { scale: 1, x: bubble.x, y: bubble.y };
    }
    
    // Calculate scale to make bubble fill most of the view
    const targetSize = Math.min(dimensions.width, dimensions.height) * 0.7;
    const scale = targetSize / (bubble.radius * 2);
    
    // Center the bubble
    const x = dimensions.width / 2;
    const y = dimensions.height / 2;
    
    return { scale, x, y };
  };
  
  return (
    <Box
      ref={containerRef}
      onClick={handleBackgroundClick}
      sx={{
        position: "relative",
        width: "100%",
        height: { xs: 400, md: 600 },
        borderRadius: 2,
        overflow: "hidden",
        border: "1px solid #d7d2c7",
        background: "linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%)",
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? "scale(1)" : "scale(0.8)",
        transition: "opacity 0.6s ease, transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)",
        cursor: zoomedBubble ? "pointer" : "default"
      }}
    >
      {/* Controls */}
      <Stack
        direction="row"
        spacing={1}
        sx={{
          position: "absolute",
          top: 16,
          right: 16,
          zIndex: 1000
        }}
      >
        {zoomedBubble && (
          <Button
            size="small"
            variant="outlined"
            onClick={(e) => {
              e.stopPropagation();
              setZoomedBubble(null);
            }}
            sx={{
              background: "rgba(255, 255, 255, 0.95)",
              "&:hover": {
                background: "rgba(255, 255, 255, 1)"
              }
            }}
          >
            Back to All
          </Button>
        )}
        <Button
          size="small"
          variant="contained"
          onClick={(e) => {
            e.stopPropagation();
            handleClearFilters();
          }}
          sx={{
            background: "rgba(74, 144, 226, 0.9)",
            "&:hover": {
              background: "rgba(74, 144, 226, 1)"
            }
          }}
        >
          Clear Filters
        </Button>
      </Stack>
      
      {/* Bubble visualization canvas */}
      <Box
        sx={{
          position: "relative",
          width: "100%",
          height: "100%"
        }}
      >
        {bubbleNodes.map((bubble) => {
          const transform = getZoomedTransform(bubble);
          const isZoomed = zoomedBubble?.id === bubble.id;
          const isOtherBubble = zoomedBubble && zoomedBubble.id !== bubble.id;
          
          return (
            <BubbleNode
              key={bubble.id}
              bubble={bubble}
              x={transform.x}
              y={transform.y}
              radius={bubble.radius}
              isZoomed={isZoomed}
              selectedCompanyId={selectedCompanyId}
              onBubbleClick={handleBubbleClick}
              onCompanyClick={handleCompanyClick}
              scale={transform.scale}
              opacity={isOtherBubble ? 0.2 : 1}
              pointerEvents={isOtherBubble ? "none" : "auto"}
            />
          );
        })}
        
        {bubbleNodes.length === 0 && (
          <Box
            sx={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              textAlign: "center",
              color: "#666"
            }}
          >
            No companies match the selected filters
          </Box>
        )}
      </Box>
    </Box>
  );
}
