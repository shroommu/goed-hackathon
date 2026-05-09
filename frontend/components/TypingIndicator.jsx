import { Box, keyframes } from "@mui/material";

const bounce = keyframes`
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
`;

export default function TypingIndicator() {
  return (
    <Box
      sx={{
        display: "flex",
        gap: 0.5,
        alignItems: "center",
        py: 2,
        px: 2
      }}
      role="status"
      aria-label="AI is typing"
    >
      <Box
        sx={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          bgcolor: "text.secondary",
          animation: `${bounce} 1.4s infinite ease-in-out both`,
          animationDelay: "0s"
        }}
      />
      <Box
        sx={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          bgcolor: "text.secondary",
          animation: `${bounce} 1.4s infinite ease-in-out both`,
          animationDelay: "0.16s"
        }}
      />
      <Box
        sx={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          bgcolor: "text.secondary",
          animation: `${bounce} 1.4s infinite ease-in-out both`,
          animationDelay: "0.32s"
        }}
      />
    </Box>
  );
}
