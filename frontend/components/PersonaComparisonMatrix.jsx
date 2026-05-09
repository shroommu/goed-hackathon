import {
  Box,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography
} from "@mui/material";

/**
 * Recommendation overlap matrix across persona runs.
 *
 * Rows: every recommended resource title that appeared in any run.
 * Columns: each persona that has a completed run.
 * Cells: filled marker when that persona received that recommendation,
 *        with a tooltip showing the rationale for explainability.
 *
 * The legend below the table summarizes:
 *  - which titles were unique to a single persona (the "differentiators")
 *  - which titles were shared across all run personas (the "always-on" set)
 */
export default function PersonaComparisonMatrix({
  personas,
  results,
  comparison
}) {
  const completedPersonas = personas.filter(
    (persona) => results[persona.id]?.status === "ok"
  );

  if (completedPersonas.length === 0) {
    return (
      <Paper variant="outlined" sx={{ p: 3, textAlign: "center" }}>
        <Typography variant="body2" color="text.secondary">
          Run two or more personas to see how their recommendations differ.
        </Typography>
      </Paper>
    );
  }

  if (!comparison || comparison.unionTitles.length === 0) {
    return (
      <Paper variant="outlined" sx={{ p: 3, textAlign: "center" }}>
        <Typography variant="body2" color="text.secondary">
          No recommendations were returned for the completed runs.
        </Typography>
      </Paper>
    );
  }

  const sharedAcrossAll = comparison.unionTitles.filter(
    ({ count }) => count === completedPersonas.length
  );

  const recommendationLookup = new Map();
  completedPersonas.forEach((persona) => {
    const recs = results[persona.id]?.recommendations || [];
    recs.forEach((rec) => {
      recommendationLookup.set(`${persona.id}::${rec.title}`, rec);
    });
  });

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 700 }}>
          Recommendation overlap
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Each filled cell means the persona received that recommendation. Hover a cell to
          see the rationale the assistant gave.
        </Typography>
      </Box>

      <TableContainer component={Paper} variant="outlined">
        <Table
          size="small"
          aria-label="Persona recommendation overlap matrix"
          sx={{
            "& .MuiTableCell-root": {
              py: 1,
              verticalAlign: "middle"
            }
          }}
        >
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 700, minWidth: 220, width: "40%" }}>
                Resource
              </TableCell>
              <TableCell
                sx={{
                  fontWeight: 700,
                  width: 72,
                  textAlign: "center",
                  whiteSpace: "nowrap"
                }}
              >
                Used by
              </TableCell>
              {completedPersonas.map((persona) => (
                <TableCell
                  key={persona.id}
                  sx={{
                    fontWeight: 700,
                    minWidth: 132,
                    textAlign: "center",
                    whiteSpace: "normal",
                    wordBreak: "break-word",
                    lineHeight: 1.3
                  }}
                >
                  {persona.name}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {comparison.unionTitles.map(({ title, count }) => {
              const isShared = count === completedPersonas.length;
              const isUnique = count === 1;

              return (
                <TableRow key={title} hover>
                  <TableCell
                    sx={{
                      whiteSpace: "normal",
                      wordBreak: "break-word",
                      pr: 2,
                      borderLeft: 4,
                      borderLeftColor: isUnique
                        ? "secondary.main"
                        : isShared
                          ? "primary.main"
                          : "transparent"
                    }}
                  >
                    {title}
                  </TableCell>
                  <TableCell sx={{ textAlign: "center", whiteSpace: "nowrap" }}>
                    <Typography
                      variant="body2"
                      sx={{ fontVariantNumeric: "tabular-nums" }}
                    >
                      {count}/{completedPersonas.length}
                    </Typography>
                  </TableCell>
                  {completedPersonas.map((persona) => {
                    const matched = comparison.byPersona[persona.id]?.has(title);
                    const rec = recommendationLookup.get(`${persona.id}::${title}`);
                    return (
                      <TableCell
                        key={persona.id}
                        sx={{
                          textAlign: "center",
                          color: matched ? "primary.main" : "text.disabled"
                        }}
                      >
                        {matched ? (
                          <Tooltip
                            title={rec?.rationale || "(no rationale)"}
                            placement="top"
                            arrow
                          >
                            <Box
                              component="span"
                              aria-label={`${persona.name} received ${title}`}
                              sx={{
                                display: "inline-block",
                                width: 12,
                                height: 12,
                                borderRadius: "50%",
                                bgcolor: "primary.main"
                              }}
                            />
                          </Tooltip>
                        ) : (
                          <Box
                            component="span"
                            aria-hidden="true"
                            sx={{
                              display: "inline-block",
                              width: 12,
                              height: 12,
                              borderRadius: "50%",
                              border: "1px solid",
                              borderColor: "divider"
                            }}
                          />
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      <Stack
        direction="row"
        spacing={2.5}
        flexWrap="wrap"
        useFlexGap
        sx={{ rowGap: 1, alignItems: "center" }}
      >
        <Stack direction="row" spacing={1} alignItems="center">
          <Box
            sx={{ width: 12, height: 12, borderRadius: "50%", bgcolor: "primary.main" }}
            aria-hidden="true"
          />
          <Typography variant="body2" color="text.secondary">
            Recommended to that persona
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center">
          <Box
            sx={{
              width: 4,
              height: 16,
              bgcolor: "secondary.main",
              borderRadius: 1
            }}
            aria-hidden="true"
          />
          <Typography variant="body2" color="text.secondary">
            Unique to one persona (
            {comparison.unionTitles.filter((t) => t.count === 1).length})
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center">
          <Box
            sx={{
              width: 4,
              height: 16,
              bgcolor: "primary.main",
              borderRadius: 1
            }}
            aria-hidden="true"
          />
          <Typography variant="body2" color="text.secondary">
            Shared across all completed personas ({sharedAcrossAll.length})
          </Typography>
        </Stack>
      </Stack>
    </Stack>
  );
}
