import { Box, IconButton, TextField } from "@mui/material";
import { Send } from "@mui/icons-material";
import { useState } from "react";

export default function ChatComposer({ onSendMessage, disabled, placeholder }) {
  const [input, setInput] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const message = input.trim();
    if (message && !disabled) {
      onSendMessage(message);
      setInput("");
    }
  };

  const handleKeyPress = (e) => {
    // Send on Enter, new line on Shift+Enter
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <Box
      sx={{
        p: { xs: 2, sm: 3 },
        bgcolor: "background.paper",
        borderTop: 1,
        borderColor: "divider",
        position: { xs: "sticky", sm: "relative" },
        bottom: { xs: 0, sm: "auto" },
        zIndex: 1
      }}
    >
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          width: "100%",
          maxWidth: "58rem",
          mx: "auto",
          display: "flex",
          gap: 1
        }}
      >
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder || "Type your message..."}
          disabled={disabled}
          variant="outlined"
          size="medium"
          sx={{
            "& .MuiOutlinedInput-root": {
              borderRadius: 3
            }
          }}
          inputProps={{
            "aria-label": "Chat message input"
          }}
        />
        <IconButton
          type="submit"
          color="primary"
          disabled={disabled || !input.trim()}
          size="large"
          sx={{
            alignSelf: "flex-end",
            bgcolor: "primary.main",
            color: "primary.contrastText",
            "&:hover": {
              bgcolor: "primary.dark"
            },
            "&:disabled": {
              bgcolor: "action.disabledBackground"
            }
          }}
          aria-label="Send message"
        >
          <Send />
        </IconButton>
      </Box>
    </Box>
  );
}
