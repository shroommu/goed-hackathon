import { Box, IconButton, Paper, Stack, Tooltip, Typography } from "@mui/material";
import { ContentCopy } from "@mui/icons-material";
import { useEffect, useState } from "react";
import RecommendationCard from "./RecommendationCard";

function AnimatedText({ text, speed = 20 }) {
  const [displayedText, setDisplayedText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText((prev) => prev + text[currentIndex]);
        setCurrentIndex((prev) => prev + 1);
      }, speed);

      return () => clearTimeout(timeout);
    }
  }, [currentIndex, text, speed]);

  return <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>{displayedText}</Typography>;
}

export default function ChatMessage({ message, isLatest }) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const fullCopyText =
    message.content +
    (message.followUpQuestion ? `\n\n${message.followUpQuestion}` : "");

  const handleCopy = () => {
    navigator.clipboard.writeText(fullCopyText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        mb: 2,
        px: { xs: 2, sm: 3 }
      }}
    >
      <Paper
        elevation={isUser ? 1 : 0}
        sx={{
          maxWidth: { xs: "85%", sm: "70%", md: "60%" },
          p: 2,
          bgcolor: isUser ? "primary.main" : "background.paper",
          color: isUser ? "primary.contrastText" : "text.primary",
          borderRadius: 2,
          position: "relative"
        }}
      >
        <Stack spacing={1}>
          {/* Message content with optional streaming animation */}
          {isLatest && !isUser && message.streaming ? (
            <AnimatedText text={message.content} />
          ) : (
            <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
              {message.content}
            </Typography>
          )}

          {!isUser && message.followUpQuestion && (
            <Box
              sx={{
                mt: 1.5,
                pl: 1.5,
                borderLeft: 3,
                borderColor: "primary.main",
                borderRadius: 0.5
              }}
            >
              <Typography
                variant="caption"
                component="p"
                sx={{
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  color: "text.secondary",
                  mb: 0.5
                }}
              >
                Next question
              </Typography>
              <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
                {message.followUpQuestion}
              </Typography>
            </Box>
          )}

          {/* Recommendations */}
          {message.recommendations && message.recommendations.length > 0 && (
            <Stack spacing={1} sx={{ mt: 1 }}>
              {message.recommendations.map((rec) => (
                <RecommendationCard key={rec.id} recommendation={rec} />
              ))}
            </Stack>
          )}

          {/* Message actions */}
          {!isUser && (
            <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 0.5 }}>
              <Tooltip title={copied ? "Copied!" : "Copy message"}>
                <IconButton
                  size="small"
                  onClick={handleCopy}
                  sx={{
                    opacity: 0.7,
                    "&:hover": { opacity: 1 }
                  }}
                >
                  <ContentCopy fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          )}
        </Stack>

        {/* Timestamp */}
        <Typography
          variant="caption"
          sx={{
            display: "block",
            mt: 1,
            opacity: 0.7,
            fontSize: "0.7rem"
          }}
        >
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
          })}
        </Typography>
      </Paper>
    </Box>
  );
}
