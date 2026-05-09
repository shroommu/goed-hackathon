"use client";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Paper,
  Stack,
  Typography
} from "@mui/material";
import { useCallback, useMemo, useState } from "react";
import Link from "next/link";
import SiteShell from "@/components/SiteShell";
import PersonaCard from "@/components/PersonaCard";
import PersonaComparisonMatrix from "@/components/PersonaComparisonMatrix";
import PersonaResult from "@/components/PersonaResult";
import { PERSONA_PRESETS, getPersonaById } from "@/lib/personaPresets";
import { buildComparison, runPersona } from "@/lib/personaRunner";

/**
 * FE-010 — Persona validation harness for the resource navigator.
 *
 * Goals:
 *  1. Persona presets can run end-to-end quickly (single click per persona,
 *     or "Run all" which runs them sequentially).
 *  2. Output differences are visible and explainable: each completed run
 *     surfaces the assistant message, derived context, follow-up question,
 *     and recommendation cards. A comparison matrix highlights which
 *     resources are unique to a persona vs. shared across personas.
 */
export default function PersonaValidationPage() {
  const [results, setResults] = useState({});
  const [runningId, setRunningId] = useState(null);
  const [isRunningAll, setIsRunningAll] = useState(false);
  const [selectedPersonaId, setSelectedPersonaId] = useState(null);
  const [batchError, setBatchError] = useState(null);

  const runOne = useCallback(async (persona) => {
    setBatchError(null);
    setRunningId(persona.id);
    try {
      const result = await runPersona(persona);
      setResults((prev) => ({ ...prev, [persona.id]: result }));
      setSelectedPersonaId(persona.id);
      return result;
    } finally {
      setRunningId((current) => (current === persona.id ? null : current));
    }
  }, []);

  const handleRunAll = useCallback(async () => {
    setBatchError(null);
    setIsRunningAll(true);
    try {
      for (const persona of PERSONA_PRESETS) {
        setRunningId(persona.id);
        try {
          const result = await runPersona(persona);
          setResults((prev) => ({ ...prev, [persona.id]: result }));
        } catch (err) {
          setBatchError(
            err?.userMessage || err?.message || "A persona run failed unexpectedly."
          );
        }
      }
    } finally {
      setRunningId(null);
      setIsRunningAll(false);
    }
  }, []);

  const handleResetAll = useCallback(() => {
    setResults({});
    setSelectedPersonaId(null);
    setBatchError(null);
  }, []);

  const comparison = useMemo(() => buildComparison(results), [results]);

  const completedCount = useMemo(
    () => Object.values(results).filter((r) => r?.status === "ok").length,
    [results]
  );
  const errorCount = useMemo(
    () => Object.values(results).filter((r) => r?.status === "error").length,
    [results]
  );

  const selectedPersona = selectedPersonaId ? getPersonaById(selectedPersonaId) : null;
  const selectedResult = selectedPersonaId ? results[selectedPersonaId] : null;

  const personaStatus = (personaId) => {
    if (runningId === personaId) {
      return "running";
    }
    const result = results[personaId];
    if (!result) {
      return "idle";
    }
    return result.status;
  };

  return (
    <SiteShell>
      <Box component="header" sx={{ mb: 5 }}>
        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={2}
          justifyContent="space-between"
          alignItems={{ xs: "flex-start", md: "flex-end" }}
        >
          <Box sx={{ maxWidth: "48rem" }}>
            <Typography
              variant="overline"
              sx={{ letterSpacing: "0.08em", fontWeight: 700, color: "text.secondary" }}
            >
              FE-010 · Internal validation harness
            </Typography>
            <Typography
              variant="h1"
              sx={{ mt: 1, mb: 1.5, fontSize: { xs: "2rem", md: "2.6rem" }, lineHeight: 1.15 }}
            >
              Resource Navigator persona harness
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.55 }}>
              Run scripted personas through the live navigator endpoint to verify that
              recommendations shift in sensible ways across stage, industry, location, and
              goals. Each persona sends a single message with its preset context, so a full
              sweep takes well under a minute.
            </Typography>
          </Box>
          <Button
            variant="outlined"
            component={Link}
            href="/navigator"
            size="small"
            sx={{ flexShrink: 0 }}
          >
            Back to navigator
          </Button>
        </Stack>
      </Box>

      <Card sx={{ mb: 5 }}>
        <CardContent sx={{ p: { xs: 2, md: 2.5 } }}>
          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={2}
            alignItems={{ xs: "stretch", sm: "center" }}
            justifyContent="space-between"
          >
            <Stack
              direction="row"
              spacing={0.75}
              flexWrap="wrap"
              useFlexGap
              sx={{ rowGap: 0.75 }}
            >
              <Chip
                label={`${PERSONA_PRESETS.length} personas`}
                variant="outlined"
                size="small"
              />
              <Chip
                label={`${completedCount} completed`}
                color="success"
                variant={completedCount ? "filled" : "outlined"}
                size="small"
              />
              {errorCount > 0 && (
                <Chip label={`${errorCount} errored`} color="error" size="small" />
              )}
              {isRunningAll && (
                <Chip label="Running batch…" color="info" size="small" />
              )}
            </Stack>
            <Stack
              direction="row"
              spacing={1}
              flexWrap="wrap"
              useFlexGap
              sx={{ rowGap: 1, flexShrink: 0 }}
            >
              <Button
                variant="contained"
                onClick={handleRunAll}
                disabled={isRunningAll || runningId !== null}
              >
                {isRunningAll ? "Running all…" : "Run all personas"}
              </Button>
              <Button
                variant="outlined"
                onClick={handleResetAll}
                disabled={
                  isRunningAll || runningId !== null || completedCount + errorCount === 0
                }
              >
                Reset
              </Button>
            </Stack>
          </Stack>

          {batchError && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              {batchError}
            </Alert>
          )}
        </CardContent>
      </Card>

      <Box component="section" aria-labelledby="personas-heading" sx={{ mb: 6 }}>
        <Stack spacing={0.5} sx={{ mb: 2 }}>
          <Typography
            variant="overline"
            sx={{ color: "text.secondary", fontWeight: 700, letterSpacing: "0.08em" }}
          >
            Step 1
          </Typography>
          <Typography
            id="personas-heading"
            variant="h2"
            sx={{ fontSize: { xs: "1.4rem", md: "1.6rem" } }}
          >
            Personas
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Pick a persona to run individually, or use <strong>Run all personas</strong>{" "}
            above to sweep the full validation set.
          </Typography>
        </Stack>

        <Box
          sx={{
            display: "grid",
            gap: { xs: 2, md: 2.5 },
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, minmax(0, 1fr))",
              lg: "repeat(3, minmax(0, 1fr))"
            }
          }}
        >
          {PERSONA_PRESETS.map((persona) => {
            const status = personaStatus(persona.id);
            const result = results[persona.id];
            return (
              <PersonaCard
                key={persona.id}
                persona={persona}
                status={status}
                durationMs={result?.durationMs}
                recommendationCount={result?.recommendations?.length || 0}
                selected={selectedPersonaId === persona.id}
                disabled={isRunningAll || (runningId !== null && runningId !== persona.id)}
                onRun={runOne}
                onSelect={(p) => setSelectedPersonaId(p.id)}
              />
            );
          })}
        </Box>
      </Box>

      <Box component="section" aria-labelledby="comparison-heading" sx={{ mb: 6 }}>
        <Stack spacing={0.5} sx={{ mb: 2 }}>
          <Typography
            variant="overline"
            sx={{ color: "text.secondary", fontWeight: 700, letterSpacing: "0.08em" }}
          >
            Step 2
          </Typography>
          <Typography
            id="comparison-heading"
            variant="h2"
            sx={{ fontSize: { xs: "1.4rem", md: "1.6rem" } }}
          >
            Output comparison
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Compare which resources surfaced for each persona and which are unique
            differentiators.
          </Typography>
        </Stack>
        <PersonaComparisonMatrix
          personas={PERSONA_PRESETS}
          results={results}
          comparison={comparison}
        />
      </Box>

      <Divider sx={{ mb: 5 }} />

      <Box component="section" aria-labelledby="detail-heading">
        <Stack spacing={0.5} sx={{ mb: 2 }}>
          <Typography
            variant="overline"
            sx={{ color: "text.secondary", fontWeight: 700, letterSpacing: "0.08em" }}
          >
            Step 3
          </Typography>
          <Typography
            id="detail-heading"
            variant="h2"
            sx={{ fontSize: { xs: "1.4rem", md: "1.6rem" } }}
          >
            Persona detail
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Inspect the full input, derived context, and recommendation cards for the
            selected persona.
          </Typography>
        </Stack>
        {selectedPersona ? (
          <PersonaResult persona={selectedPersona} result={selectedResult} />
        ) : (
          <Paper
            variant="outlined"
            sx={{ p: 3, textAlign: "center" }}
          >
            <Typography variant="body2" color="text.secondary">
              Run a persona or click <em>View result</em> on a completed card to see the
              full response here.
            </Typography>
          </Paper>
        )}
      </Box>
    </SiteShell>
  );
}
