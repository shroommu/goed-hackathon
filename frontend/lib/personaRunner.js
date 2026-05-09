/**
 * Persona runner — drives the navigator backend with a persona preset
 * and captures a structured result for the validation harness (FE-010).
 *
 * Single-turn by design: each persona sends its scripted message with its
 * preset context. This keeps runs deterministic and end-to-end fast.
 */

import { sendChatMessage, formatRecommendations } from "./navigatorApi";

/**
 * Run a single persona against the navigator endpoint.
 *
 * @param {Object} persona - Persona preset from `personaPresets.js`.
 * @returns {Promise<Object>} Structured run result (success or error).
 */
export async function runPersona(persona) {
  const startedAt = Date.now();

  try {
    const response = await sendChatMessage(persona.message, persona.context);

    return {
      personaId: persona.id,
      status: "ok",
      durationMs: Date.now() - startedAt,
      assistantMessage: response.assistantMessage,
      followUpQuestion: response.followUpQuestion || null,
      derivedContext: response.derivedContext || {},
      recommendations: formatRecommendations(response.recommendations)
    };
  } catch (err) {
    return {
      personaId: persona.id,
      status: "error",
      durationMs: Date.now() - startedAt,
      error: {
        message: err.userMessage || err.message || "Unknown error",
        code: err.code || "unknown_error"
      }
    };
  }
}

/**
 * Run a list of personas, one at a time.
 *
 * Sequential execution keeps backend load predictable (the navigator
 * endpoint hits an LLM) and lets the UI stream completions in order.
 *
 * @param {Array<Object>} personas - Persona presets to run.
 * @param {(personaId: string, result: Object) => void} [onResult]
 *   Optional callback invoked after each persona completes.
 * @returns {Promise<Object>} Map of personaId -> run result.
 */
export async function runPersonas(personas, onResult) {
  const results = {};

  for (const persona of personas) {
    const result = await runPersona(persona);
    results[persona.id] = result;
    if (typeof onResult === "function") {
      onResult(persona.id, result);
    }
  }

  return results;
}

/**
 * Build a comparison summary across persona run results.
 *
 * Produces:
 *  - `unionTitles`: every recommendation title that appeared in any run,
 *    sorted by how often it appeared (descending).
 *  - `byPersona`: map of personaId -> Set-like object of recommended titles
 *    (used for fast lookup in the comparison matrix).
 *  - `uniqueByPersona`: map of personaId -> array of titles only that persona received.
 *
 * Titles are used as the comparison key (rather than IDs) so the matrix
 * is human-readable. IDs are surfaced separately in the per-persona panel.
 *
 * @param {Object} results - Map of personaId -> run result.
 * @returns {Object} Comparison summary.
 */
export function buildComparison(results) {
  const titleCounts = new Map();
  const byPersona = {};
  const personaIds = Object.keys(results);

  personaIds.forEach((personaId) => {
    const result = results[personaId];
    const titles = new Set();
    if (result?.status === "ok" && Array.isArray(result.recommendations)) {
      result.recommendations.forEach((rec) => {
        if (rec?.title) {
          titles.add(rec.title);
          titleCounts.set(rec.title, (titleCounts.get(rec.title) || 0) + 1);
        }
      });
    }
    byPersona[personaId] = titles;
  });

  const unionTitles = Array.from(titleCounts.entries())
    .sort((a, b) => {
      if (b[1] !== a[1]) {
        return b[1] - a[1];
      }
      return a[0].localeCompare(b[0]);
    })
    .map(([title, count]) => ({ title, count }));

  const uniqueByPersona = {};
  personaIds.forEach((personaId) => {
    const titles = byPersona[personaId];
    uniqueByPersona[personaId] = Array.from(titles).filter(
      (title) => titleCounts.get(title) === 1
    );
  });

  return {
    unionTitles,
    byPersona,
    uniqueByPersona,
    personaCount: personaIds.length
  };
}
