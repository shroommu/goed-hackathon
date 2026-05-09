import {
  Alert,
  Box,
  Chip,
  Divider,
  Paper,
  Stack,
  Typography
} from "@mui/material";
import RecommendationCard from "./RecommendationCard";

const KEY_LABELS = {
  stage: "Stage",
  industry: "Industry",
  location: "Location",
  objectives: "Objectives",
  topics: "Topics",
  challenges: "Challenges"
};

/**
 * Chip styling that allows multi-line labels without clipping.
 * Mirrors the pattern used in RecommendationCard.
 */
const wrappingChipSx = {
  height: "auto",
  maxWidth: "100%",
  alignSelf: "flex-start",
  "& .MuiChip-label": {
    whiteSpace: "normal",
    overflow: "visible",
    textOverflow: "clip",
    wordBreak: "break-word",
    py: 0.5,
    lineHeight: 1.35
  }
};

const sectionLabelSx = {
  display: "block",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "text.secondary",
  fontWeight: 700,
  mb: 0.75
};

function formatContextValue(value) {
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  return String(value);
}

function prettyKey(key) {
  return KEY_LABELS[key] || key.charAt(0).toUpperCase() + key.slice(1);
}

function ContextBlock({ title, context }) {
  const entries = Object.entries(context || {}).filter(
    ([, value]) =>
      value !== undefined &&
      value !== null &&
      value !== "" &&
      !(Array.isArray(value) && value.length === 0)
  );

  return (
    <Box>
      <Typography variant="caption" sx={sectionLabelSx}>
        {title}
      </Typography>
      {entries.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          (none)
        </Typography>
      ) : (
        <Stack direction="column" spacing={0.75} alignItems="flex-start">
          {entries.map(([key, value]) => (
            <Chip
              key={key}
              size="small"
              variant="outlined"
              label={`${prettyKey(key)}: ${formatContextValue(value)}`}
              sx={wrappingChipSx}
            />
          ))}
        </Stack>
      )}
    </Box>
  );
}

/**
 * Render a single persona's run result. Designed for the validation
 * harness so it intentionally surfaces inputs and outputs side-by-side
 * (rather than the conversational layout used in the main chat view).
 */
export default function PersonaResult({ persona, result }) {
  if (!persona) {
    return null;
  }

  return (
    <Paper variant="outlined" sx={{ p: { xs: 2, md: 3 } }}>
      <Stack spacing={2.5}>
        <Box>
          <Typography
            variant="h2"
            sx={{ fontSize: "1.4rem", lineHeight: 1.25, wordBreak: "break-word" }}
          >
            {persona.name}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {persona.summary}
          </Typography>
        </Box>

        <Divider />

        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={3}
          divider={
            <Divider
              orientation="vertical"
              flexItem
              sx={{ display: { xs: "none", md: "block" } }}
            />
          }
        >
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="overline" sx={{ display: "block", color: "text.secondary", fontWeight: 700 }}>
              Input
            </Typography>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <ContextBlock title="Persona context" context={persona.context} />
              <Box>
                <Typography variant="caption" sx={sectionLabelSx}>
                  Message
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}
                >
                  {persona.message}
                </Typography>
              </Box>
            </Stack>
          </Box>

          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="overline" sx={{ display: "block", color: "text.secondary", fontWeight: 700 }}>
              Output
            </Typography>
            {!result && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Run this persona to see the navigator&apos;s response.
              </Typography>
            )}

            {result?.status === "error" && (
              <Alert severity="error" sx={{ mt: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {result.error?.code || "error"}
                </Typography>
                <Typography variant="body2">{result.error?.message}</Typography>
              </Alert>
            )}

            {result?.status === "ok" && (
              <Stack spacing={2} sx={{ mt: 1 }}>
                <Stack
                  direction="row"
                  spacing={0.75}
                  flexWrap="wrap"
                  useFlexGap
                  sx={{ rowGap: 0.75 }}
                >
                  <Chip
                    size="small"
                    color="success"
                    variant="outlined"
                    label={`${(result.durationMs / 1000).toFixed(1)}s`}
                  />
                  <Chip
                    size="small"
                    variant="outlined"
                    label={`${result.recommendations.length} recommendation${result.recommendations.length === 1 ? "" : "s"}`}
                  />
                </Stack>

                <Box>
                  <Typography variant="caption" sx={sectionLabelSx}>
                    Assistant message
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}
                  >
                    {result.assistantMessage}
                  </Typography>
                </Box>

                <ContextBlock title="Derived context" context={result.derivedContext} />
              </Stack>
            )}
          </Box>
        </Stack>

        {result?.status === "ok" && result.recommendations.length > 0 && (
          <>
            <Divider />
            <Box>
              <Typography
                variant="overline"
                sx={{ display: "block", color: "text.secondary", fontWeight: 700, mb: 1.25 }}
              >
                Recommended resources
              </Typography>
              <Stack
                direction="row"
                spacing={2}
                sx={{
                  overflowX: "auto",
                  pb: 1.5,
                  alignItems: "stretch",
                  WebkitOverflowScrolling: "touch"
                }}
              >
                {result.recommendations.map((rec) => (
                  <Box
                    key={rec.id}
                    sx={{
                      flex: "0 0 auto",
                      width: { xs: 280, sm: 320, md: 340 }
                    }}
                  >
                    <RecommendationCard recommendation={rec} />
                  </Box>
                ))}
              </Stack>
            </Box>
          </>
        )}
      </Stack>
    </Paper>
  );
}
