"use client";

import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Stack
} from "@mui/material";
import { useEffect, useState } from "react";
import ChatComposer from "./ChatComposer";
import ChatMessageThread from "./ChatMessageThread";
import ContextChips from "./ContextChips";
import {
  getSessionContext,
  getSessionId,
  getSessionMessages,
  setSessionMessages,
  updateSessionContext,
  clearSession
} from "@/lib/chatSession";
import {
  sendChatMessage,
  formatRecommendations,
  isRecoverableError
} from "@/lib/navigatorApi";

const WELCOME_MESSAGE = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi! I'm here to help you discover resources for your startup. Tell me about what you're building, and I'll recommend programs, funding opportunities, and connections tailored to your needs.",
  timestamp: Date.now(),
  recommendations: []
};

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [context, setContext] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [clearConfirmOpen, setClearConfirmOpen] = useState(false);

  // Initialize session on mount
  useEffect(() => {
    const id = getSessionId();
    setSessionId(id);

    const savedMessages = getSessionMessages();
    const savedContext = getSessionContext();

    if (savedMessages.length > 0) {
      setMessages(savedMessages);
      setContext(savedContext);
    } else {
      // Show welcome message for new sessions
      setMessages([WELCOME_MESSAGE]);
    }

    setIsInitialized(true);
  }, []);

  // Persist messages when they change
  useEffect(() => {
    if (isInitialized && messages.length > 0) {
      // Don't persist the welcome message if it's the only one
      if (messages.length === 1 && messages[0].id === "welcome") {
        return;
      }
      setSessionMessages(messages);
    }
  }, [messages, isInitialized]);

  const handleSendMessage = async (messageText) => {
    setError(null);

    // Add user message to thread
    const userMessage = {
      id: Date.now(),
      role: "user",
      content: messageText,
      timestamp: Date.now()
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Send to backend
      const response = await sendChatMessage(messageText, context);

      // Update context
      if (response.derivedContext) {
        const updatedContext = { ...context, ...response.derivedContext };
        setContext(updatedContext);
        updateSessionContext(response.derivedContext);
      }

      // Add assistant response
      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: response.assistantMessage,
        timestamp: Date.now(),
        recommendations: formatRecommendations(response.recommendations),
        streaming: true
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error("Chat error:", err);
      
      setError({
        message: err.userMessage || err.message || "Something went wrong",
        code: err.code,
        recoverable: isRecoverableError(err)
      });

      // Add error message to thread for context
      const errorMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content:
          "I apologize, but I encountered an issue. " +
          (err.userMessage || "Please try rephrasing your message or try again later."),
        timestamp: Date.now(),
        isError: true
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleContextUpdate = (updates) => {
    const updatedContext = { ...context, ...updates };
    Object.keys(updatedContext).forEach((key) => {
      if (
        updatedContext[key] === null ||
        updatedContext[key] === undefined ||
        updatedContext[key] === "" ||
        (Array.isArray(updatedContext[key]) && updatedContext[key].length === 0)
      ) {
        delete updatedContext[key];
      }
    });

    setContext(updatedContext);
    updateSessionContext(updates);
  };

  const handleRetry = () => {
    setError(null);
    // Remove last error message
    setMessages((prev) => prev.filter((msg) => !msg.isError));
  };

  const handleClearSession = () => {
    clearSession();
    setMessages([WELCOME_MESSAGE]);
    setContext({});
    setError(null);
    setSessionId(getSessionId());
    setClearConfirmOpen(false);
  };

  if (!isInitialized) {
    return null; // or a loading skeleton
  }

  return (
    <Stack
      sx={{
        height: { xs: "70vh", md: "72vh" },
        minHeight: { xs: 480, md: 560 },
        display: "flex",
        flexDirection: "column",
        bgcolor: "background.default",
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 2,
        overflow: "hidden"
      }}
    >
      <Box
        sx={{
          flexShrink: 0,
          px: { xs: 1.5, sm: 2 },
          py: 1,
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",
          borderBottom: 1,
          borderColor: "divider",
          bgcolor: "background.paper"
        }}
      >
        <Button
          size="small"
          variant="outlined"
          onClick={() => setClearConfirmOpen(true)}
          aria-label="Clear chat session and start over"
        >
          Clear session
        </Button>
      </Box>

      <Dialog
        open={clearConfirmOpen}
        onClose={() => setClearConfirmOpen(false)}
        aria-labelledby="clear-session-dialog-title"
        aria-describedby="clear-session-dialog-description"
      >
        <DialogTitle id="clear-session-dialog-title">Clear session?</DialogTitle>
        <DialogContent>
          <DialogContentText id="clear-session-dialog-description">
            This removes your conversation and saved context from this device. You can start a fresh
            chat afterward.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setClearConfirmOpen(false)} color="inherit">
            Cancel
          </Button>
          <Button onClick={handleClearSession} variant="contained" color="primary" autoFocus>
            Clear session
          </Button>
        </DialogActions>
      </Dialog>

      {/* Error banner */}
      {error && (
        <Alert
          severity="error"
          onClose={() => setError(null)}
          action={
            error.recoverable && (
              <Button color="inherit" size="small" onClick={handleRetry}>
                Retry
              </Button>
            )
          }
          sx={{ borderRadius: 0 }}
        >
          {error.message}
        </Alert>
      )}

      {/* Message thread: flex column + minHeight 0 so the child can shrink and scroll */}
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden"
        }}
      >
        <ChatMessageThread
          messages={messages}
          isLoading={isLoading}
          showWelcome={messages.length === 1 && messages[0].id === "welcome"}
        />
      </Box>

      {/* Context chips */}
      {Object.keys(context).length > 0 && (
        <ContextChips context={context} onContextUpdate={handleContextUpdate} />
      )}

      {/* Composer */}
      <ChatComposer
        onSendMessage={handleSendMessage}
        disabled={isLoading}
        placeholder="Ask about programs, funding, mentorship..."
      />
    </Stack>
  );
}
