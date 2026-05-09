/**
 * Navigator API client for conversational resource recommendations
 * Integrates with BE-014 endpoint: POST /api/navigator/chat/message
 *
 * Always use relative paths - Next.js rewrites handle routing
 */

/**
 * Send a chat message and get AI response with recommendations
 *
 * @param {string} message - User's message
 * @param {Object} context - Current conversation context
 * @returns {Promise<Object>} Response with assistant_message, derived_context, recommendations
 * @throws {Error} With code and message properties for error handling
 */
export async function sendChatMessage(message, context = {}) {
  const endpoint = "/api/navigator/chat/message";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        context,
      }),
    });

    if (!response.ok) {
      // Handle error response from backend
      let errorData;
      try {
        errorData = await response.json();
      } catch (parseError) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (errorData.error) {
        const error = new Error(errorData.error.message || "Request failed");
        error.code = errorData.error.code || "unknown_error";
        error.details = errorData.error.details;
        throw error;
      }

      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    // Validate response structure
    if (!data.assistant_message) {
      throw new Error("Invalid response format: missing assistant_message");
    }

    return {
      assistantMessage: data.assistant_message,
      derivedContext: data.derived_context || {},
      recommendations: data.recommendations || [],
    };
  } catch (error) {
    // Enhance error with user-friendly messages
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      const networkError = new Error(
        "Unable to connect to the server. Please check your internet connection.",
      );
      networkError.code = "network_error";
      throw networkError;
    }

    // Map backend error codes to user-friendly messages
    if (error.code) {
      const errorMessages = {
        invalid_request: "Invalid request. Please try again.",
        llm_timeout: "The AI is taking longer than expected. Please try again.",
        llm_error: "The AI service encountered an issue. Please try again.",
        no_resources_found:
          "No matching resources found. Let's try a different approach.",
        internal_error: "Something went wrong. Please try again.",
      };

      error.userMessage = errorMessages[error.code] || error.message;
    }

    throw error;
  }
}

/**
 * Format recommendations for display
 * @param {Array} recommendations - Raw recommendations from backend
 * @returns {Array} Formatted recommendations with safe fallbacks
 */
export function formatRecommendations(recommendations) {
  if (!Array.isArray(recommendations)) {
    return [];
  }

  return recommendations.map((rec) => ({
    id: rec.id,
    title: rec.title || "Untitled Resource",
    description: rec.description || "",
    rationale: rec.rationale || "Recommended based on your profile",
    url: rec.url || rec.link || "#",
    topics: rec.topics || "",
    industries: rec.industries || "",
    communities: rec.communities || "",
    locations: rec.locations || "",
  }));
}

/**
 * Check if error is recoverable (user can retry)
 * @param {Error} error - Error object with code property
 * @returns {boolean}
 */
export function isRecoverableError(error) {
  const recoverableCodes = [
    "network_error",
    "llm_timeout",
    "llm_error",
    "internal_error",
  ];

  return recoverableCodes.includes(error.code);
}
