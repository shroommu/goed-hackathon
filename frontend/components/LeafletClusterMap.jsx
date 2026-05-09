"use client";

import { Box, Button, Chip, Stack } from "@mui/material";
import "leaflet/dist/leaflet.css";
import "@changey/react-leaflet-markercluster/dist/styles.min.css";
import { useEffect, useRef, useMemo, useState } from "react";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import MarkerClusterGroup from "@changey/react-leaflet-markercluster";
import L from "leaflet";

// Create custom marker icon with colored letter
function createCompanyIcon(company) {
  // Get first letter of company name for the icon
  const firstLetter = (company.startup_name || '?')[0].toUpperCase();
  
  // Generate a color based on the first letter for visual variety
  const colorIndex = firstLetter.charCodeAt(0) % 10;
  const colors = ['#4A90E2', '#7B68EE', '#50C878', '#FF6B6B', '#FFA500', '#9B59B6', '#3498DB', '#E74C3C', '#1ABC9C', '#F39C12'];
  const bgColor = colors[colorIndex];
  
  const iconHtml = `<div style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.3); background: ${bgColor}; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #fff; font-weight: bold;">
       ${firstLetter}
     </div>`;
  
  return L.divIcon({
    html: iconHtml,
    className: 'company-marker-icon',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -20]
  });
}

export default function LeafletClusterMap({
  mappedCompanies,
  unmappedCompanies,
  onSelectCompany,
  mapCenter,
  utahLeafletBounds
}) {
  const mapRef = useRef(null);
  const [hasInitialFit, setHasInitialFit] = useState(false);
  const prevCompanyCountRef = useRef(0);

  // Memoize company icons to avoid recreating them on every render
  const companyIcons = useMemo(() => {
    return mappedCompanies.reduce((acc, company) => {
      acc[company.id] = createCompanyIcon(company);
      return acc;
    }, {});
  }, [mappedCompanies]);

  // Reset initial fit flag when company list changes (filters applied)
  useEffect(() => {
    if (prevCompanyCountRef.current !== mappedCompanies.length) {
      setHasInitialFit(false);
      prevCompanyCountRef.current = mappedCompanies.length;
    }
  }, [mappedCompanies.length]);

  // Only fit bounds on initial load or when company list changes, not on every render
  useEffect(() => {
    const map = mapRef.current;
    if (!map || hasInitialFit) {
      return;
    }

    if (mappedCompanies.length) {
      map.fitBounds(
        mappedCompanies.map((company) => [company.latitude, company.longitude]),
        { padding: [24, 24], maxZoom: 10 }
      );
      setHasInitialFit(true);
      return;
    }

    map.fitBounds(utahLeafletBounds, { padding: [24, 24] });
    setHasInitialFit(true);
  }, [mappedCompanies, utahLeafletBounds, hasInitialFit]);

  return (
    <>
      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <Button size="small" variant="outlined" onClick={() => mapRef.current?.zoomIn()}>
          Zoom in
        </Button>
        <Button size="small" variant="outlined" onClick={() => mapRef.current?.zoomOut()}>
          Zoom out
        </Button>
        <Button
          size="small"
          variant="outlined"
          onClick={() => mapRef.current?.fitBounds(utahLeafletBounds, { padding: [24, 24] })}
        >
          Reset
        </Button>
        <Chip label={`${mappedCompanies.length} mapped`} size="small" variant="outlined" />
        {unmappedCompanies.length > 0 && (
          <Chip label={`${unmappedCompanies.length} without coordinates`} size="small" variant="outlined" />
        )}
      </Stack>

      <Box
        role="application"
        aria-label="Utah startup map"
        sx={{
          position: "relative",
          height: { xs: 340, md: 460 },
          borderRadius: 2,
          overflow: "hidden",
          border: "1px solid #d7d2c7"
        }}
      >
        <MapContainer
          ref={mapRef}
          center={mapCenter}
          zoom={7}
          minZoom={6}
          maxZoom={14}
          maxBounds={utahLeafletBounds}
          maxBoundsViscosity={0.8}
          scrollWheelZoom
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />

          <MarkerClusterGroup
            chunkedLoading
            showCoverageOnHover={false}
            spiderfyOnMaxZoom={true}
            maxClusterRadius={44}
          >
            {mappedCompanies.map((company) => (
              <Marker
                key={company.id}
                position={[company.latitude, company.longitude]}
                icon={companyIcons[company.id]}
                eventHandlers={{
                  click: (e) => {
                    // Prevent default behavior that might cause zoom/pan
                    L.DomEvent.stopPropagation(e);
                    onSelectCompany(company.id);
                  }
                }}
              />
            ))}
          </MarkerClusterGroup>
        </MapContainer>
      </Box>
    </>
  );
}
