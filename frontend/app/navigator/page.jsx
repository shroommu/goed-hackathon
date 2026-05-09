"use client";

import SiteShell from "@/components/SiteShell";
import ChatInterface from "@/components/ChatInterface";
import { Box, Typography } from "@mui/material";

/**
 * Navigator page with conversational AI interface (FE-013)
 * Integrates with BE-014 endpoint for personalized resource recommendations
 */
export default function NavigatorPage() {
  return (
    <SiteShell>
      <Box component="section" aria-labelledby="navigator-title" sx={{ maxWidth: "52rem" }}>
        <Typography
          variant="overline"
          sx={{ letterSpacing: "0.08em", fontWeight: 700, color: "text.secondary" }}
        >
          Guided Resource Match
        </Typography>
        <Typography
          id="navigator-title"
          variant="h1"
          sx={{ mt: 1, mb: 2, fontSize: { xs: "2rem", md: "3rem" } }}
        >
          Tell us your startup goals and get personalized next steps.
        </Typography>
        <Typography variant="body1" sx={{ color: "text.secondary" }}>
          Share your stage, needs, and constraints. The assistant recommends relevant programs,
          funding, and ecosystem connections.
        </Typography>
      </Box>

      <Box sx={{ mt: 4 }}>
        <ChatInterface />
      </Box>
    </SiteShell>
  );
}
