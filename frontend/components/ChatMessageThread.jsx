import { Box, Skeleton, Stack } from "@mui/material";
import { useEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";
import TypingIndicator from "./TypingIndicator";

export default function ChatMessageThread({ messages, isLoading, showWelcome }) {
  const messagesEndRef = useRef(null);
  const threadRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  // Initial skeleton for first load
  if (showWelcome && messages.length === 0 && isLoading) {
    return (
      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          py: 3,
          px: { xs: 2, sm: 3 }
        }}
      >
        <Stack spacing={2}>
          <Skeleton variant="rectangular" height={60} sx={{ borderRadius: 2 }} />
          <Skeleton variant="rectangular" height={80} sx={{ borderRadius: 2 }} />
        </Stack>
      </Box>
    );
  }

  return (
    <Box
      ref={threadRef}
      sx={{
        flex: 1,
        overflowY: "auto",
        overflowX: "hidden",
        py: 3,
        display: "flex",
        flexDirection: "column"
      }}
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
    >
      <Box sx={{ width: "100%", maxWidth: "58rem", mx: "auto" }}>
        {messages.map((message, index) => (
          <ChatMessage
            key={message.id || index}
            message={message}
            isLatest={index === messages.length - 1}
          />
        ))}

        {isLoading && <TypingIndicator />}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </Box>
    </Box>
  );
}
