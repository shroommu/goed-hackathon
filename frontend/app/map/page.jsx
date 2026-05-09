"use client";

import SiteShell from "@/components/SiteShell";
import { fetchCompaniesList, fetchCompanyDetail } from "@/lib/companiesApi";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  MenuItem,
  Stack,
  TextField,
  Typography,
  useMediaQuery,
  useTheme
} from "@mui/material";
import Link from "next/link";
import dynamic from "next/dynamic";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";

const LeafletClusterMap = dynamic(() => import("@/components/LeafletClusterMap"), {
  ssr: false
});

const BubbleClusterView = dynamic(() => import("@/components/BubbleClusterView"), {
  ssr: false
});

const UTAH_BOUNDS = {
  minLat: 36.95,
  maxLat: 42.05,
  minLng: -114.05,
  maxLng: -109.05
};

const SIZE_OPTIONS = ["micro", "small", "medium", "large", "enterprise"];
const STAGE_OPTIONS = [
  "idea",
  "pre-seed",
  "seed",
  "series-a",
  "series-b",
  "series-c",
  "growth",
  "late-stage",
  "public",
  "unknown"
];

function parseFiltersFromParams(searchParams) {
  return {
    sector: (searchParams.get("sector") || "").trim(),
    size: (searchParams.get("size") || "").trim(),
    stage: (searchParams.get("stage") || "").trim(),
    location: (searchParams.get("location") || "").trim()
  };
}

function hasActiveFilters(filters) {
  return Boolean(filters.sector || filters.size || filters.stage || filters.location);
}

function formatValue(value) {
  return (value || "unknown").replace(/-/g, " ");
}

function areFiltersEqual(left, right) {
  return (
    (left.sector || "") === (right.sector || "") &&
    (left.size || "") === (right.size || "") &&
    (left.stage || "") === (right.stage || "") &&
    (left.location || "") === (right.location || "")
  );
}

function hasCoordinates(company) {
  return typeof company.latitude === "number" && typeof company.longitude === "number";
}

function MapPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const theme = useTheme();

  const appliedFilters = useMemo(() => parseFiltersFromParams(searchParams), [searchParams]);
  const [draftFilters, setDraftFilters] = useState(appliedFilters);
  const [activeView, setActiveView] = useState("map");
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState("");
  const [companiesPayload, setCompaniesPayload] = useState({
    items: [],
    mindmap: { levels: ["sector", "stage", "company"], sectors: [] },
    pagination: null
  });
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [isLoadingCompany, setIsLoadingCompany] = useState(false);
  const [companyError, setCompanyError] = useState("");

  const filtersAreActive = hasActiveFilters(appliedFilters);
  const mappedCompanies = companiesPayload.items.filter(hasCoordinates);
  const unmappedCompanies = companiesPayload.items.filter((item) => !hasCoordinates(item));

  const utahLeafletBounds = useMemo(
    () => [
      [UTAH_BOUNDS.minLat, UTAH_BOUNDS.minLng],
      [UTAH_BOUNDS.maxLat, UTAH_BOUNDS.maxLng]
    ],
    []
  );
  const mapCenter = useMemo(() => {
    if (!mappedCompanies.length) {
      return [39.32, -111.1];
    }

    const totals = mappedCompanies.reduce(
      (accumulator, company) => {
        return {
          latitude: accumulator.latitude + company.latitude,
          longitude: accumulator.longitude + company.longitude
        };
      },
      { latitude: 0, longitude: 0 }
    );

    return [totals.latitude / mappedCompanies.length, totals.longitude / mappedCompanies.length];
  }, [mappedCompanies]);

  useEffect(() => {
    setDraftFilters(appliedFilters);
  }, [appliedFilters]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadCompanies() {
      setIsLoading(true);
      setFetchError("");

      try {
        const payload = await fetchCompaniesList(appliedFilters, {
          signal: controller.signal
        });

        setCompaniesPayload(payload);
      } catch (error) {
        if (error.name !== "AbortError") {
          setCompaniesPayload({
            items: [],
            mindmap: { levels: ["sector", "stage", "company"], sectors: [] },
            pagination: null
          });
          setFetchError(error.message || "Unable to load companies.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    loadCompanies();

    return () => {
      controller.abort();
    };
  }, [appliedFilters]);

  useEffect(() => {
    if (hasActiveFilters(draftFilters)) {
      setActiveView("mindmap");
    } else {
      setActiveView("bubble
    }
  }, [draftFilters]);

  useEffect(() => {
    if (!selectedCompanyId) {
      setSelectedCompany(null);
      setCompanyError("");
      return;
    }

    const controller = new AbortController();

    async function loadCompanyDetail() {
      setIsLoadingCompany(true);
      setCompanyError("");

      try {
        const item = await fetchCompanyDetail(selectedCompanyId, {
          signal: controller.signal
        });
        setSelectedCompany(item);
      } catch (error) {
        if (error.name !== "AbortError") {
          setSelectedCompany(null);
          setCompanyError(error.message || "Unable to load company details.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoadingCompany(false);
        }
      }
    }

    loadCompanyDetail();

    return () => {
      controller.abort();
    };
  }, [selectedCompanyId]);

  useEffect(() => {
    if (!companiesPayload.items.some((item) => item.id === selectedCompanyId)) {
      setSelectedCompanyId(null);
    }
  }, [companiesPayload.items, selectedCompanyId]);

  useEffect(() => {
    (nextFilters) => {
      const params = new URLSearchParams(searchParams.toString());

      ["sector", "size", "stage", "location"].forEach((key) => {
        if (nextFilters[key]) {
          params.set(key, nextFilters[key]);
        } else {
          params.delete(key);
        }
      });

      const nextQueryString = params.toString();
      router.replace(nextQueryString ? `${pathname}?${nextQueryString}` : pathname, {
        scroll: false
      });
    },
    [pathname, router, searchParams]
  );

  useEffect(() => {
    if (areFiltersEqual(draftFilters, appliedFilters)) {
      return;
    }

    const timer = window.setTimeout(() => {
      updateSearchParams(draftFilters);
    }, 250);

    return () => {
      window.clearTimeout(timer);
    };
  }, [draftFilters, appliedFilters, updateSearchParams]);

  function handleApplyFilters(event) {
    event.preventDefault();
    updateSearchParams(draftFilters);
    if (hasActiveFilters(draftFilters)) {
      setActiveView("mindmap");
    }
  }

  function handleClearFilters() {
    const cleared = {
      sector: "",
      size: "",
      stage: "",
      location: ""
    };
    setDraftFilters(cleared);
    updateSearchParams(cleared);
    setActiveView("map");
  }

  const desktopSelectedSector =
    sectors.find((sectorNode) => sectorNode.stages.some((stageNode) => stageNode.companies.some((company) => company.id === selectedCompanyId))) ||
    sectors[0] ||
    null;
  const desktopSelectedStage =
    desktopSelectedSector?.stages.find((stageNode) => stageNode.companies.some((company) => company.id === selectedCompanyId)) ||
    desktopSelectedSector?.stages[0] ||
    null;

  const mobileSelectedSector = sectors.find((sectorNode) => sectorNode.name === mobileSector) || null;
  const mobileSelectedStage =
    mobileSelectedSector?.stages.find((stageNode) => stageNode.name === mobileStage) || null;

  return (
    <SiteShell>
      <Box component="section" aria-labelledby="map-title" sx={{ maxWidth: "52rem" }}>
        <Typography variant="overline" sx={{ letterSpacing: "0.08em", fontWeight: 700, color: "text.secondary" }}>
          Utah Startububblerer
        </Typography>
        <Typography id="map-title" variant="h1" sx={{ mt: 1, mb: 2, fontSize: { xs: "2rem", md: "3rem" } }}>
          Switch between geo-cluster map and sector mindmap without losing filter context.
        </Typography>
        <Typography variant="body1" sx={{ color: "text.secondary" }}>
          Filter by sector, company size, stage, or location. As filters change, the experience auto-shifts to a connected investor mindmap organized by sector, then stage, then company.
        </Typography>
      </Box>

      <Card sx={{ mt: 4 }}>
        <CardContent sx={{ p: 3 }}>
          <Stack
            component="form"
   
              select
              label="Company size"
              value={draftFilters.size}
              onChange={(event) => setDraftFilters((prev) => ({ ...prev, size: event.target.value }))}
            >
              <MenuItem value="">Any</MenuItem>
              {SIZE_OPTIONS.map((value) => (
                <MenuItem key={value} value={value}>
                  {formatValue(value)}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Stage"
              value={draftFilters.stage}
              onChange={(event) => setDraftFilters((prev) => ({ ...prev, stage: event.target.value }))}
            >
              <MenuItem value="">Any</MenuItem>
              {STAGE_OPTIONS.map((value) => (
                <MenuItem key={value} value={value}>
          Explore Utah startups with map and bubble views
        </Typography>
        <Typography variant="body1" sx={{ color: "text.secondary" }}>
          Filter by sector, company size, stage, or location. Switch between geographic map view and interactive bubble visualization to explore the startup ecosystem
            <TextField
              label="Location"
              value={draftFilters.location}
              onChange={(event) => setDraftFilters((prev) => ({ ...prev, location: event.target.value }))}
              placeholder="ex: Salt Lake"
            />

            <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ gridColumn: { xs: "1 / -1" } }}>
              <Button type="submit" variant="contained" disabled={isLoading}>
                Apply filters
              </Button>
              <Button type="button" variant="outlined" onClick={handleClearFilters}>
                Clear
              </Button>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {filtersAreActive ? (
                  <Chip label="Filters active" color="secondary" variant="outlined" />
                ) : (
                  <Chip label="No filters" variant="outlined" />
                )}
                <Chip
                  label={`Showing ${companiesPayload.pagination?.total ?? companiesPayload.items.length} companies`}
                  variant="outlined"
                />
              </Stack>
            </Stack>
          </Stack>

          <Stack direction="row" spacing={1} sx={{ mt: 3 }}>
            <Button
              variant={activeView === "map" ? "contained" : "outlined"}
              onClick={() => setActiveView("map")}
              aria-pressed={activeView === "map"}
            >
              Map view
            </Button>
            <Button
              variant={activeView === "mindmap" ? "contained" : "outlined"}
              onClick={() => setActiveView("mindmap")}
              aria-pressed={activeView === "mindmap"}
            >
              Mindmap view
            </Button>
          </Stack>
        </CardContent>
      </Card>

      {fetchError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {fetchError}
        </Alert>
      )}

      {!fetchError && !isLoading && companiesPayload.items.length === 0 && filtersAreActive && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No companies matched this strategy. Investors often broaden one dimension first, such as using a wider location or removing stage constraints.
        </Alert>
      )}

      {!fetchError && !isLoading && companiesPayload.items.length === 0 && !filtersAreActive && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          No startup data is currently available from the backend listing endpoint.
        </Alert>
      )}

      <Box
        sx={{
          mt: 3,
          display: "grid",
          gap: 2,
          gridTemplateColumns: { xs: "1fr", lg: "minmax(0, 1fr) 22rem" }
        }}
      >
        <Card sx={{ minHeight: 500 }}>
          <CardContent sx={{ p: 3 }}>
            {isLoading ? (
              <Stack direction="row" spacing={1} alignItems="center">
                <CircularProgress size={20} />
                <Typography>Loading company data...</Typography>
              </Stack>
            ) : activeView === "map" ? (
              <Box
                sx={{
                  opacity: activeView =bubble" ? "contained" : "outlined"}
              onClick={() => setActiveView("bubble")}
              aria-pressed={activeView === "bubble"}
            >
              Bubble
                <LeafletClusterMap
                  mappedCompanies={mappedCompanies}
                  unmappedCompanies={unmappedCompanies}
                  onSelectCompany={setSelectedCompanyId}
                  mapCenter={mapCenter}
                  utahLeafletBounds={utahLeafletBounds}
                />
              </Box>
            ) : filtersAreActive && !isMobile ? (
              <BubbleClusterView
                companiesPayload={companiesPayload}
                filters={appliedFilters}
                selectedCompanyId={selectedCompanyId}
                onSelectCompany={setSelectedCompanyId}
                onClearFilters={handleClearFilters}
              />
            ) : isMobile ? (
              <Stack spacing={2}>
                <Typography variant="h2" sx={{ fontSize: "1.25rem" }}>
                  Mobile drill-down
                </Typography>
                (
              <BubbleClusterView
                companiesPayload={companiesPayload}
                filters={appliedFilters}
                selectedCompanyId={selectedCompanyId}
                onSelectCompany={setSelectedCompanyId}
                onClearFilters={handleClearFilters}
              /ect a marker or mindmap node to load company profile details from the backend detail endpoint.
              </Typography>
            )}

            {companyError && <Alert severity="error">{companyError}</Alert>}

            {isLoadingCompany && (
              <Stack direction="row" spacing={1} alignItems="center">
                <CircularProgress size={18} />
                <Typography>Loading company profile...</Typography>
              </Stack>
            )}

            {selectedCompany && (
              <Stack spacing={1.5}>
                <Typography variant="h3" sx={{ fontSize: "1.15rem" }}>
                  {selectedCompany.startup_name || "Unnamed company"}
                </Typography>

                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  {selectedCompany.sector && <Chip label={selectedCompany.sector} size="small" variant="outlined" />}
                  {selectedCompany.stage && <Chip label={selectedCompany.stage} size="small" variant="outlined" />}
                  {selectedCompany.size && <Chip label={selectedCompany.size} size="small" variant="outlined" />}
                  {selectedCompany.employees && <Chip label={`${selectedCompany.employees} employees`} size="small" variant="outlined" />}
                </Stack>

                {selectedCompany.description && (
                  <Typography color="text.secondary">{selectedCompany.description}</Typography>
                )}

                <Divider />

                {selectedCompany.website && (
                  <Typography variant="body2">
                    Website: <a href={selectedCompany.website} target="_blank" rel="noreferrer">{selectedCompany.website}</a>
                  </Typography>
                )}
                {selectedCompany.linkedin && (
                  <Typography variant="body2">
                    LinkedIn: <a href={selectedCompany.linkedin} target="_blank" rel="noreferrer">{selectedCompany.linkedin}</a>
                  </Typography>
                )}
                {selectedCompany.full_address && (
                  <Typography variant="body2">Address: {selectedCompany.full_address}</Typography>
                )}
                <Typography variant="body2" color="text.secondary">
                  Photo gallery items: {selectedCompany.photo_gallery.length}
                </Typography>
              </Stack>
            )}
          </CardContent>
        </Card>
      </Box>

      <Button component={Link} href="/" variant="text" sx={{ mt: 3 }}>
        Back to landing
      </Button>
    </SiteShell>
  );
}

export default function MapPage() {
  return (
    <Suspense fallback={<SiteShell><Box sx={{ mt: 4 }}><CircularProgress size={24} /></Box></SiteShell>}>
      <MapPageContent />
    </Suspense>
  );
}
