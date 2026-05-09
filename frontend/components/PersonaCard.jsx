import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Stack,
  Typography
} from "@mui/material";

const STATUS_LABEL = {
  idle: "Not run",
  running: "Running…",
  ok: "Done",
  error: "Error"
};

const STATUS_COLOR = {
  idle: "default",
  running: "info",
  ok: "success",
  error: "error"
};

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
 * Mirrors the pattern used in RecommendationCard so chips look consistent
 * across the harness and the chat surface.
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

function formatContextValue(value) {
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  return String(value);
}

function prettyKey(key) {
  return KEY_LABELS[key] || key.charAt(0).toUpperCase() + key.slice(1);
}

export default function PersonaCard({
  persona,
  status = "idle",
  durationMs,
  recommendationCount = 0,
  onRun,
  onSelect,
  selected = false,
  disabled = false
}) {
  const contextEntries = Object.entries(persona.context).filter(
    ([, value]) => value !== undefined && value !== null && value !== ""
  );

  return (
    <Card
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        outline: selected ? "2px solid" : "none",
        outlineColor: "primary.main",
        outlineOffset: selected ? "2px" : 0,
        transition: "outline-color 120ms ease"
      }}
    >
      <CardContent
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: 2,
          p: { xs: 2, md: 2.5 }
        }}
      >
        <Stack
          direction="row"
          spacing={0.75}
          alignItems="center"
          flexWrap="wrap"
          useFlexGap
          sx={{ minHeight: 28 }}
        >
          <Chip
            size="small"
            color={STATUS_COLOR[status] || "default"}
            label={STATUS_LABEL[status] || status}
            variant={status === "idle" ? "outlined" : "filled"}
            icon={status === "running" ? <CircularProgress size={12} color="inherit" /> : undefined}
          />
          {status === "ok" && typeof durationMs === "number" && (
            <Chip
              size="small"
              variant="outlined"
              label={`${(durationMs / 1000).toFixed(1)}s`}
            />
          )}
          {status === "ok" && (
            <Chip
              size="small"
              variant="outlined"
              label={`${recommendationCount} rec${recommendationCount === 1 ? "" : "s"}`}
            />
          )}
        </Stack>

        <Box>
          <Typography
            variant="h3"
            sx={{ fontSize: "1.05rem", lineHeight: 1.3, wordBreak: "break-word" }}
          >
            {persona.name}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {persona.summary}
          </Typography>
        </Box>

        <Box>
          <Typography
            variant="caption"
            sx={{
              display: "block",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              color: "text.secondary",
              fontWeight: 700,
              mb: 0.75
            }}
          >
            Context
          </Typography>
          <Stack direction="column" spacing={0.75} alignItems="flex-start">
            {contextEntries.map(([key, value]) => (
              <Chip
                key={key}
                size="small"
                variant="outlined"
                label={`${prettyKey(key)}: ${formatContextValue(value)}`}
                sx={wrappingChipSx}
              />
            ))}
          </Stack>
        </Box>

        <Box>
          <Typography
            variant="caption"
            sx={{
              display: "block",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              color: "text.secondary",
              fontWeight: 700,
              mb: 0.75
            }}
          >
            Expected signals
          </Typography>
          <Stack component="ul" spacing={0.5} sx={{ pl: 2.5, m: 0 }}>
            {persona.expectedSignals.map((signal) => (
              <Typography
                key={signal}
                variant="body2"
                component="li"
                color="text.secondary"
                sx={{ lineHeight: 1.4 }}
              >
                {signal}
              </Typography>
            ))}
          </Stack>
        </Box>

        <Stack
          direction="row"
          spacing={1}
          flexWrap="wrap"
          useFlexGap
          sx={{ mt: "auto", pt: 1, rowGap: 1 }}
        >
          <Button
            size="small"
            variant="contained"
            onClick={() => onRun?.(persona)}
            disabled={disabled || status === "running"}
          >
            {status === "ok" || status === "error" ? "Run again" : "Run persona"}
          </Button>
          <Button
            size="small"
            variant="outlined"
            onClick={() => onSelect?.(persona)}
            disabled={status !== "ok"}
          >
            View result
          </Button>
        </Stack>
      </CardContent>
    </Card>
  );
}
