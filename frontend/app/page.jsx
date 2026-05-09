"use client";

import SiteShell from "@/components/SiteShell";
import { Box, Button, Card, CardContent, Chip, Stack, Typography } from "@mui/material";
import Link from "next/link";

export default function HomePage() {
  return (
    <SiteShell>
      <Box component="section" aria-labelledby="hero-title" sx={{ maxWidth: "48rem" }}>
        <Typography
          variant="overline"
          sx={{ letterSpacing: "0.08em", fontWeight: 700, color: "text.secondary" }}
        >
          Utah startup launchpad
        </Typography>
        <Typography id="hero-title" variant="h1" sx={{ mt: 1, mb: 2, fontSize: { xs: "2rem", md: "3.4rem" }, textWrap: "balance" }}>
          Choose your path in seconds: guided support or ecosystem map.
        </Typography>
        <Typography variant="body1" sx={{ color: "text.secondary", fontSize: { xs: "1rem", md: "1.2rem" } }} gutterBottom>
          GOED helps users and investors quickly find the right next move with personalized resources and a live view of Utah startups.
        </Typography>
      </Box>

      <Box
        component="section"
        id="get-started"
        aria-label="Choose your mode"
        sx={{
          mt: 5,
          display: "grid",
          gap: 2,
          gridTemplateColumns: "repeat(auto-fit, minmax(16rem, 1fr))"
        }}
      >
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 1, fontSize: "1.5rem" }}>
              Resource Navigator
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              Share your goals and focus. Get ranked resources with clear reasons and next steps.
            </Typography>
            <Button
              component={Link}
              href="/navigator?entry=landing&mode=guided"
              variant="contained"
              color="primary"
              size="large"
              fullWidth
            >
              Start navigator
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 1, fontSize: "1.5rem" }}>
              Utah Startup Map
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              Browse companies by sector, stage, and hiring signals to explore opportunity clusters fast.
            </Typography>
            <Button
              component={Link}
              href="/map?entry=landing&mode=investor"
              variant="contained"
              color="primary"
              size="large"
              fullWidth
            >
              Explore map flow
            </Button>
          </CardContent>
        </Card>
      </Box>

      <Box
        component="section"
        id="how-it-works"
        aria-label="How it works"
        sx={{
          mt: 6,
          display: "grid",
          gap: 2,
          gridTemplateColumns: "repeat(auto-fit, minmax(15rem, 1fr))"
        }}
      >
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 1, fontSize: "1.4rem" }}>
              Tell us your stage
            </Typography>
            <Typography color="text.secondary">
              Share what you are building, your traction, and what support you need right now.
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 1, fontSize: "1.4rem" }}>
              Get matched
            </Typography>
            <Typography color="text.secondary">
              Receive recommendations that explain why each program is a fit.
            </Typography>
          </CardContent>
        </Card>
        <Card id="why-goed">
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 1, fontSize: "1.4rem" }}>
              Take action
            </Typography>
            <Typography color="text.secondary">
              Move from discovery to outreach with direct links and clear next actions.
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </SiteShell>
  );
}
