"use client";

import SiteShell from "@/components/SiteShell";
import ChatInterface from "@/components/ChatInterface";
import { Box, Link as MuiLink, Stack, Typography } from "@mui/material";
import Link from "next/link";

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
          Utah&rsquo;s Startup State — Your Journey Starts Here
        </Typography>
        <Typography
          id="navigator-title"
          variant="h1"
          sx={{ mt: 1, mb: 2, fontSize: { xs: "2rem", md: "3rem" } }}
        >
          Find the right resources for where you are today.
        </Typography>
        <Typography variant="body1" sx={{ color: "text.secondary" }}>
          Share your stage, goals, and needs. The assistant connects you with relevant programs,
          funding, and ecosystem partners from Utah&rsquo;s thriving entrepreneurial community.
        </Typography>
      </Box>

      <Box sx={{ mt: 4 }}>
        <ChatInterface />
      </Box>

      <Stack
        direction="row"
        justifyContent="flex-end"
        sx={{ mt: 2 }}
      >
        <MuiLink
          component={Link}
          href="/navigator/validate"
          variant="caption"
          color="text.secondary"
          underline="hover"
          aria-label="Open the persona validation harness"
        >
          Persona validation harness →
        </MuiLink>
      </Stack>
    </SiteShell>
  );
}
