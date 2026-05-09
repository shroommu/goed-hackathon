"use client";

import { Box, Tooltip, Typography } from "@mui/material";
import { getCompanyColor } from "@/lib/forceSimulation";

/**
 * CompanyNode - Individual company icon within a bubble
 * Reuses the same colored letter style as the map markers
 */
export default function CompanyNode({
  company,
  x,
  y,
  radius = 20,
  isZoomed = false,
  isSelected = false,
  onClick
}) {
  const firstLetter = (company.startup_name || company.name || '?')[0].toUpperCase();
  const bgColor = getCompanyColor(company.startup_name || company.name);
  
  const handleClick = (e) => {
    e.stopPropagation();
    if (onClick) {
      onClick(company);
    }
  };
  
  return (
    <Tooltip 
      title={company.startup_name || company.name || "Unknown"} 
      arrow
      placement="top"
    >
      <Box
        onClick={handleClick}
        sx={(theme) => ({
          position: "absolute",
          left: x - radius,
          top: y - radius,
          width: radius * 2,
          height: radius * 2,
          borderRadius: "50%",
          border: isSelected ? `3px solid ${theme.palette.text.primary}` : `2px solid ${theme.palette.background.default}`,
          boxShadow: isSelected
            ? `0 4px 12px rgba(0,0,0,0.55), 0 0 0 2px ${theme.palette.primary.main}`
            : "0 2px 4px rgba(0,0,0,0.45)",
          background: bgColor,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          transition: "all 0.2s ease",
          transform: isSelected ? "scale(1.2)" : "scale(1)",
          zIndex: isSelected ? 1000 : 10,
          "&:hover": {
            transform: "scale(1.15)",
            boxShadow: "0 4px 8px rgba(0,0,0,0.4)",
            zIndex: 100
          }
        })}
      >
        <Typography
          sx={(theme) => ({
            fontSize: radius * 0.8,
            color: theme.palette.getContrastText(bgColor),
            fontWeight: "bold",
            userSelect: "none",
            pointerEvents: "none",
          })}
        >
          {firstLetter}
        </Typography>
      </Box>
    </Tooltip>
  );
}
