"use client";

import SiteShell from "@/components/SiteShell";
import { fetchResourceRecommendations } from "@/lib/resourcesApi";
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  Link as MuiLink,
  MenuItem,
  Stack,
  TextField,
  Typography
} from "@mui/material";
import Link from "next/link";
import { useMemo, useState } from "react";

const stageOptions = [
  { value: "idea", label: "Idea" },
  { value: "pre_seed", label: "Pre-seed" },
  { value: "seed", label: "Seed" },
  { value: "growth", label: "Growth" },
  { value: "expansion", label: "Expansion" }
];

const industryOptions = [
  "Aerospace",
  "Agritech",
  "Biotech",
  "Clean Energy",
  "Consumer",
  "EdTech",
  "FinTech",
  "HealthTech",
  "SaaS"
];

const locationOptions = ["Utah", "Salt Lake City", "Provo", "Ogden", "St. George"];

function containsValue(text, value) {
  if (!text || !value) {
    return false;
  }

  return text.toLowerCase().includes(value.toLowerCase());
}

function buildMatchReasons(resource, preferences) {
  const reasons = [];
  const joinedResourceText = [
    resource.description,
    resource.communities,
    resource.industries,
    resource.locations,
    resource.topics
  ]
    .filter(Boolean)
    .join(" ");

  if (containsValue(resource.industries, preferences.industry)) {
    reasons.push(`Aligned with your industry focus: ${preferences.industry}.`);
  }

  if (containsValue(resource.locations, preferences.location)) {
    reasons.push(`Relevant in your target location: ${preferences.location}.`);
  }

  if (preferences.objective && containsValue(joinedResourceText, preferences.objective)) {
    reasons.push(`Matches your stated objective: ${preferences.objective}.`);
  }

  if (preferences.stage) {
    const stageReasonByValue = {
      idea: "Useful for early-stage ideation and first-program discovery.",
      pre_seed: "Supports pre-seed founders seeking traction and funding prep.",
      seed: "Fits seed-stage teams preparing for growth milestones.",
      growth: "Supports growth-stage execution and scaling priorities.",
      expansion: "Helps expansion-stage teams with broader market development."
    };
    reasons.push(stageReasonByValue[preferences.stage]);
  }

  if (resource.link) {
    reasons.push("Includes an official link so you can move to outreach quickly.");
  }

  return reasons.slice(0, 3);
}

export default function NavigatorPage() {
  const [preferences, setPreferences] = useState({
    stage: "seed",
    industry: "SaaS",
    location: "Utah",
    objective: "funding and mentorship"
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState([]);
  const [pagination, setPagination] = useState(null);

  const hasResults = results.length > 0;

  const headline = useMemo(() => {
    return `Top recommendations for ${preferences.stage.replace("_", " ")} stage ${preferences.industry} teams`;
  }, [preferences.industry, preferences.stage]);

  async function handleFindRecommendations(event) {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const payload = await fetchResourceRecommendations(preferences);
      setResults(payload.items);
      setPagination(payload.pagination);
    } catch (requestError) {
      setResults([]);
      setPagination(null);
      setError(requestError.message || "Unable to load recommendations right now.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <SiteShell>
      <Box component="section" aria-labelledby="navigator-title" sx={{ maxWidth: "44rem" }}>
        <Typography variant="overline" sx={{ letterSpacing: "0.08em", fontWeight: 700, color: "text.secondary" }}>
          Resource Navigator
        </Typography>
        <Typography id="navigator-title" variant="h1" sx={{ mt: 1, mb: 2, fontSize: { xs: "2rem", md: "3rem" } }}>
          Personalized startup support, tuned to your stage.
        </Typography>
        <Typography variant="body1" sx={{ color: "text.secondary" }}>
          Share a few details and get recommendations sourced directly from the backend resource catalog.
        </Typography>
      </Box>

      <Stack component="form" onSubmit={handleFindRecommendations} spacing={2} mt={4} aria-label="Recommendation preferences">
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 2, fontSize: "1.35rem" }}>
              Your startup profile
            </Typography>
            <Box
              sx={{
                display: "grid",
                gap: 2,
                gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" }
              }}
            >
              <TextField
                select
                label="Stage"
                name="stage"
                value={preferences.stage}
                onChange={(event) =>
                  setPreferences((prev) => ({
                    ...prev,
                    stage: event.target.value
                  }))
                }
              >
                {stageOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                select
                label="Industry"
                name="industry"
                value={preferences.industry}
                onChange={(event) =>
                  setPreferences((prev) => ({
                    ...prev,
                    industry: event.target.value
                  }))
                }
              >
                {industryOptions.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                select
                label="Location"
                name="location"
                value={preferences.location}
                onChange={(event) =>
                  setPreferences((prev) => ({
                    ...prev,
                    location: event.target.value
                  }))
                }
              >
                {locationOptions.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                label="Current objective"
                name="objective"
                placeholder="ex: grants, talent, introductions"
                value={preferences.objective}
                onChange={(event) =>
                  setPreferences((prev) => ({
                    ...prev,
                    objective: event.target.value
                  }))
                }
              />
            </Box>

            <CardActions sx={{ px: 0, pt: 3 }}>
              <Button type="submit" variant="contained" size="large" disabled={isLoading}>
                {isLoading ? "Finding matches..." : "Find recommendations"}
              </Button>
              <Chip label="BE-006 contract aligned" color="secondary" variant="outlined" />
            </CardActions>
          </CardContent>
        </Card>

        {error && <Alert severity="error">{error}</Alert>}

        {hasResults && (
          <Typography variant="h2" sx={{ fontSize: "1.5rem", mt: 1 }}>
            {headline}
          </Typography>
        )}

        {hasResults && (
          <Box
            sx={{
              display: "grid",
              gap: 2,
              gridTemplateColumns: "repeat(auto-fit, minmax(16rem, 1fr))"
            }}
          >
            {results.map((resource) => {
              const reasons = buildMatchReasons(resource, preferences);

              return (
                <Card key={resource.id} sx={{ height: "100%" }}>
                  <CardContent sx={{ p: 3 }}>
                    <Typography variant="h3" sx={{ fontSize: "1.15rem", mb: 1, lineHeight: 1.3 }}>
                      {resource.title || "Untitled resource"}
                    </Typography>

                    {resource.description && (
                      <Typography color="text.secondary" sx={{ mb: 2 }}>
                        {resource.description}
                      </Typography>
                    )}

                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 700 }}>
                      Why this matches
                    </Typography>

                    <Stack component="ul" sx={{ pl: 2, m: 0, gap: 0.75 }}>
                      {reasons.map((reason) => (
                        <Typography component="li" variant="body2" key={reason}>
                          {reason}
                        </Typography>
                      ))}
                    </Stack>

                    <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 2, rowGap: 1 }}>
                      {resource.industries && <Chip size="small" label={resource.industries} variant="outlined" />}
                      {resource.locations && <Chip size="small" label={resource.locations} variant="outlined" />}
                    </Stack>
                  </CardContent>

                  {resource.link && (
                    <CardActions sx={{ px: 3, pb: 3, pt: 0 }}>
                      <MuiLink href={resource.link} target="_blank" rel="noreferrer" underline="hover">
                        Visit official resource
                      </MuiLink>
                    </CardActions>
                  )}
                </Card>
              );
            })}
          </Box>
        )}

        {!isLoading && !error && pagination && pagination.total === 0 && (
          <Alert severity="info">
            No results found for this profile. Try broadening your objective or selecting a wider location.
          </Alert>
        )}
      </Stack>

      <Button component={Link} href="/" variant="text" sx={{ mt: 3 }}>
        Back to landing
      </Button>
    </SiteShell>
  );
}
