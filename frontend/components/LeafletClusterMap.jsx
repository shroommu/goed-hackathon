"use client";

import { Box, Button, Chip, Stack } from "@mui/material";
import "leaflet/dist/leaflet.css";
import "@changey/react-leaflet-markercluster/dist/styles.min.css";
import { useEffect, useRef, useMemo } from "react";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import MarkerClusterGroup from "@changey/react-leaflet-markercluster";
import L from "leaflet";

// Extract domain from URL
function extractDomain(url) {
  if (!url) return null;
  try {
    const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`);
    return urlObj.hostname.replace(/^www\./, '');
  } catch {
    return null;
  }
}

// Create custom marker icon with company logo
function createCompanyIcon(company) {
  let logoUrl = null;
  
  // Try to get domain from website first, then LinkedIn
  const domain = extractDomain(company.website) || extractDomain(company.linkedin);
  
  if (domain) {
    // Use Clearbit Logo API
    logoUrl = `https://logo.clearbit.com/${domain}`;
  }
  
  const iconHtml = logoUrl
    ? `<div style="width: 40px; height: 40px; border-radius: 50%; overflow: hidden; border: 2px solid #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.3); background: #fff;">
         <img src="${logoUrl}" 
              style="width: 100%; height: 100%; object-fit: cover;" 
              onerror="this.parentElement.innerHTML='<div style=\\'width:100%;height:100%;background:#e0e0e0;display:flex;align-items:center;justify-content:center;font-size:18px;color:#666;\\'>?</div>';"
              alt="${company.startup_name || 'Company'} logo" />
       </div>`
    : `<div style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.3); background: #e0e0e0; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #666;">
         ?
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

  // Memoize company icons to avoid recreating them on every render
  const companyIcons = useMemo(() => {
    return mappedCompanies.reduce((acc, company) => {
      acc[company.id] = createCompanyIcon(company);
      return acc;
    }, {});
  }, [mappedCompanies]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }

    if (mappedCompanies.length) {
      map.fitBounds(
        mappedCompanies.map((company) => [company.latitude, company.longitude]),
        { padding: [24, 24], maxZoom: 10 }
      );
      return;
    }

    map.fitBounds(utahLeafletBounds, { padding: [24, 24] });
  }, [mappedCompanies, utahLeafletBounds]);

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
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MarkerClusterGroup
            chunkedLoading
            showCoverageOnHover={false}
            spiderfyOnMaxZoom
            maxClusterRadius={44}
          >
            {mappedCompanies.map((company) => (
              <Marker
                key={company.id}
                position={[company.latitude, company.longitude]}
                icon={companyIcons[company.id]}
                eventHandlers={{
                  click: () => onSelectCompany(company.id)
                }}
              >
                <Popup>
                  <strong>{company.startup_name || "Unnamed company"}</strong>
                  <br />
                  {company.sector || "Unknown sector"}
                  {company.stage ? ` - ${company.stage}` : ""}
                </Popup>
              </Marker>
            ))}
          </MarkerClusterGroup>
        </MapContainer>
      </Box>
    </>
  );
}
