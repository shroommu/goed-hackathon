"use client";

import SiteShell from "@/components/SiteShell";
import { fetchCompanyDetail } from "@/lib/companiesApi";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  Link as MuiLink,
  Stack,
  Typography
} from "@mui/material";
import {
  Business as BusinessIcon,
  Language as LanguageIcon,
  LinkedIn as LinkedInIcon,
  LocationOn as LocationIcon,
  People as PeopleIcon,
  WorkOutline as WorkOutlineIcon
} from "@mui/icons-material";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

function isValidUrl(urlString) {
  try {
    const url = new URL(urlString);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function SafeExternalLink({ href, children, ...props }) {
  if (!href || !isValidUrl(href)) {
    return <Typography component="span" color="text.disabled">{children || "Invalid URL"}</Typography>;
  }
  
  return (
    <MuiLink
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
    </MuiLink>
  );
}

export default function CompanyProfilePage() {
  const params = useParams();
  const companyId = parseInt(params.id, 10);
  
  const [company, setCompany] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!companyId || !Number.isInteger(companyId)) {
      setError("Invalid company ID");
      setIsLoading(false);
      return;
    }

    const controller = new AbortController();

    async function loadCompany() {
      setIsLoading(true);
      setError("");

      try {
        const data = await fetchCompanyDetail(companyId, {
          signal: controller.signal
        });
        setCompany(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Unable to load company details");
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    loadCompany();

    return () => {
      controller.abort();
    };
  }, [companyId]);

  if (isLoading) {
    return (
      <SiteShell>
        <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
          <Stack direction="row" spacing={2} alignItems="center">
            <CircularProgress />
            <Typography>Loading company profile...</Typography>
          </Stack>
        </Box>
      </SiteShell>
    );
  }

  if (error) {
    return (
      <SiteShell>
        <Box sx={{ maxWidth: "52rem", mx: "auto", mt: 4 }}>
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
          <Button component={Link} href="http://localhost:8787" variant="contained">
            Back to Map
          </Button>
        </Box>
      </SiteShell>
    );
  }

  if (!company) {
    return (
      <SiteShell>
        <Box sx={{ maxWidth: "52rem", mx: "auto", mt: 4 }}>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Company not found
          </Alert>
          <Button component={Link} href="http://localhost:8787" variant="contained">
            Back to Map
          </Button>
        </Box>
      </SiteShell>
    );
  }

  const displayName = company.startup_name || "Unnamed Company";

  return (
    <SiteShell>
      <Box sx={{ maxWidth: "68rem", mx: "auto" }}>
        {/* Header Section */}
        <Box sx={{ mb: 3 }}>
          <Button
            component={Link}
            href="http://localhost:8787"
            variant="text"
            sx={{ mb: 2 }}
          >
            ← Back to Map
          </Button>
          
          <Typography variant="overline" sx={{ letterSpacing: "0.08em", fontWeight: 700, color: "text.secondary" }}>
            Company Profile
          </Typography>
          <Typography variant="h1" sx={{ mt: 1, mb: 2, fontSize: { xs: "2rem", md: "3rem" } }}>
            {displayName}
          </Typography>

          {/* Tags */}
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mb: 2 }}>
            {company.sector && (
              <Chip icon={<BusinessIcon />} label={company.sector} color="primary" variant="outlined" />
            )}
            {company.stage && (
              <Chip label={company.stage} variant="outlined" />
            )}
            {company.size && (
              <Chip icon={<PeopleIcon />} label={company.size} variant="outlined" />
            )}
            {company.employees && (
              <Chip label={`${company.employees} employees`} size="small" variant="outlined" />
            )}
          </Stack>
        </Box>

        <Grid container spacing={3}>
          {/* Main Content */}
          <Grid item xs={12} md={8}>
            {/* Description */}
            {company.description && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h2" sx={{ fontSize: "1.5rem", mb: 2 }}>
                    About
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ whiteSpace: "pre-wrap" }}>
                    {company.description}
                  </Typography>
                </CardContent>
              </Card>
            )}

            {/* Media gallery (URLs from backend + company_media) */}
            {company.photo_gallery && company.photo_gallery.length > 0 && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h2" sx={{ fontSize: "1.5rem", mb: 2 }}>
                    Media Gallery
                  </Typography>
                  <Grid container spacing={2}>
                    {company.photo_gallery
                      .filter(isValidUrl)
                      .map((photoUrl, index) => (
                        <Grid item xs={12} sm={6} md={4} key={`${photoUrl}-${index}`}>
                          <Card variant="outlined">
                            <CardMedia
                              component="img"
                              height="200"
                              image={photoUrl}
                              alt={`${displayName} - Image ${index + 1}`}
                              sx={{ objectFit: "cover" }}
                              onError={(e) => {
                                e.target.style.display = "none";
                              }}
                            />
                          </Card>
                        </Grid>
                      ))}
                  </Grid>
                  {company.photo_gallery.filter(isValidUrl).length === 0 && (
                    <Typography color="text.secondary">No valid images available</Typography>
                  )}
                </CardContent>
              </Card>
            )}
          </Grid>

          {/* Sidebar */}
          <Grid item xs={12} md={4}>
            <Card sx={{ position: { md: "sticky" }, top: { md: 16 } }}>
              <CardContent>
                <Typography variant="h2" sx={{ fontSize: "1.25rem", mb: 2 }}>
                  Company Information
                </Typography>
                
                <Stack spacing={2} divider={<Divider />}>
                  {company.website && (
                    <Box>
                      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                        <LanguageIcon color="action" fontSize="small" />
                        <Typography variant="subtitle2" color="text.secondary">
                          Website
                        </Typography>
                      </Stack>
                      <SafeExternalLink href={company.website}>
                        {company.website}
                      </SafeExternalLink>
                    </Box>
                  )}

                  {company.linkedin && (
                    <Box>
                      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                        <LinkedInIcon color="action" fontSize="small" />
                        <Typography variant="subtitle2" color="text.secondary">
                          LinkedIn
                        </Typography>
                      </Stack>
                      <SafeExternalLink href={company.linkedin}>
                        View LinkedIn Profile
                      </SafeExternalLink>
                    </Box>
                  )}

                  {company.full_address && (
                    <Box>
                      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                        <LocationIcon color="action" fontSize="small" />
                        <Typography variant="subtitle2" color="text.secondary">
                          Location
                        </Typography>
                      </Stack>
                      <Typography variant="body2">
                        {company.full_address}
                      </Typography>
                    </Box>
                  )}

                  {company.display_type && (
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                        Display Type
                      </Typography>
                      <Typography variant="body2">
                        {company.display_type}
                      </Typography>
                    </Box>
                  )}
                </Stack>

                {(!company.website && !company.linkedin && !company.full_address && !company.display_type) && (
                  <Typography color="text.secondary" variant="body2">
                    No additional information available
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </SiteShell>
  );
}
