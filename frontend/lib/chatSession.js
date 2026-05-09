/**
 * Chat session management for navigator interface
 * Handles localStorage-based session persistence and context management
 */

const SESSION_ID_KEY = "navigator_session_id";
const SESSION_CONTEXT_KEY = "navigator_session_context";
const SESSION_MESSAGES_KEY = "navigator_session_messages";

/**
 * Generate a new UUID v4
 */
function generateUUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Get or create session ID
 * @returns {string} Session UUID
 */
export function getSessionId() {
  if (typeof window === "undefined") {
    return null;
  }

  let sessionId = localStorage.getItem(SESSION_ID_KEY);
  if (!sessionId) {
    sessionId = generateUUID();
    localStorage.setItem(SESSION_ID_KEY, sessionId);
  }
  return sessionId;
}

/**
 * Get current session context
 * @returns {Object} Context object with stage, industry, location, etc.
 */
export function getSessionContext() {
  if (typeof window === "undefined") {
    return {};
  }

  try {
    const contextJson = localStorage.getItem(SESSION_CONTEXT_KEY);
    return contextJson ? JSON.parse(contextJson) : {};
  } catch (error) {
    console.error("Failed to parse session context:", error);
    return {};
  }
}

/**
 * Update session context by merging with existing
 * @param {Object} derivedContext - New context fields from backend
 */
export function updateSessionContext(derivedContext) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    const currentContext = getSessionContext();
    const mergedContext = { ...currentContext, ...derivedContext };
    
    // Clean up null/undefined values
    Object.keys(mergedContext).forEach((key) => {
      if (mergedContext[key] === null || mergedContext[key] === undefined) {
        delete mergedContext[key];
      }
    });

    localStorage.setItem(SESSION_CONTEXT_KEY, JSON.stringify(mergedContext));
  } catch (error) {
    console.error("Failed to update session context:", error);
  }
}

/**
 * Get stored messages from session
 * @returns {Array} Array of message objects
 */
export function getSessionMessages() {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const messagesJson = localStorage.getItem(SESSION_MESSAGES_KEY);
    return messagesJson ? JSON.parse(messagesJson) : [];
  } catch (error) {
    console.error("Failed to parse session messages:", error);
    return [];
  }
}

/**
 * Store messages in session
 * @param {Array} messages - Array of message objects
 */
export function setSessionMessages(messages) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.setItem(SESSION_MESSAGES_KEY, JSON.stringify(messages));
  } catch (error) {
    console.error("Failed to store session messages:", error);
  }
}

/**
 * Clear all session data (for reset/restart)
 */
export function clearSession() {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem(SESSION_ID_KEY);
  localStorage.removeItem(SESSION_CONTEXT_KEY);
  localStorage.removeItem(SESSION_MESSAGES_KEY);
}

/**
 * Get editable context fields for chip display
 * @param {Object} context - Current context
 * @returns {Array} Array of {key, label, value} objects
 */
export function getContextChips(context) {
  const chipFields = [
    { key: "stage", label: "Stage" },
    { key: "industry", label: "Industry" },
    { key: "location", label: "Location" },
    { key: "objectives", label: "Objectives" },
    { key: "topics", label: "Topics" },
    { key: "challenges", label: "Challenges" }
  ];

  return chipFields
    .filter((field) => context[field.key])
    .map((field) => ({
      key: field.key,
      label: field.label,
      value: Array.isArray(context[field.key])
        ? context[field.key].join(", ")
        : context[field.key]
    }));
}
