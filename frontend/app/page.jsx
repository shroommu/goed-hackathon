"use client";

import SiteShell from "@/components/SiteShell";
import { Box, Button, Card, CardContent, Chip, Stack, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";
import Link from "next/link";

export default function HomePage() {
  return (
    <SiteShell>
      <Box component="section" aria-labelledby="hero-title" sx={{ maxWidth: "48rem" }}>
        <Typography
          variant="overline"
          sx={{ letterSpacing: "0.08em", fontWeight: 700, color: "text.secondary" }}
        >
          Welcome to the Startup Capital of the World
        </Typography>
        <Typography id="hero-title" variant="h1" sx={{ mt: 1, mb: 2, fontSize: { xs: "2rem", md: "3.4rem" }, textWrap: "balance" }}>
          Start Something Here.
        </Typography>
        <Typography variant="body1" sx={{ color: "text.secondary", fontSize: { xs: "1rem", md: "1.2rem" } }} gutterBottom>
          Be a part of Utah&rsquo;s thriving startup scene. Start, grow, and build your business with personalized resources from the Governor&rsquo;s Office of Economic Opportunity.
        </Typography>
      </Box>

      <Stack component="section" id="get-started" aria-label="Choose your mode" spacing={3} sx={{ mt: 5 }}>
        <Box
          aria-labelledby="entrepreneur-header"
          sx={(theme) => ({
            p: { xs: 2, md: 3 },
            borderRadius: 3,
            border: "1px solid",
            borderColor: "divider",
            backgroundColor: alpha(theme.palette.primary.main, 0.1)
          })}
        >
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
            <Chip label="Entrepreneurs" color="primary" size="small" />
            <Typography id="entrepreneur-header" variant="h2" sx={{ fontSize: "1.3rem" }}>
              Start, grow, or fund your business
            </Typography>
          </Stack>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h3" sx={{ mb: 1, fontSize: "1.5rem" }}>
                Resource Navigator
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                Tell us where you are in your journey. Get matched with ranked programs, funding, and ecosystem connections tailored to your stage.
              </Typography>
              <Button
                component={Link}
                href="/navigator?entry=landing&mode=guided"
                variant="contained"
                color="primary"
                size="large"
                fullWidth
              >
                Start your journey
              </Button>
            </CardContent>
          </Card>
        </Box>

        <Box
          aria-labelledby="investor-header"
          sx={(theme) => ({
            p: { xs: 2, md: 3 },
            borderRadius: 3,
            border: "1px solid",
            borderColor: "divider",
            backgroundColor: alpha(theme.palette.secondary.main, 0.1)
          })}
        >
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
            <Chip label="Investors" color="secondary" size="small"/>
            <Typography id="investor-header" variant="h2" sx={{ fontSize: "1.3rem" }}>
              Explore Utah&rsquo;s thriving startup ecosystem
            </Typography>
          </Stack>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h3" sx={{ mb: 1, fontSize: "1.5rem" }}>
                Utah Startup Map
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                Browse Utah&rsquo;s fastest-growing companies by sector and stage. Find opportunity clusters and build connections in the Startup Capital of the World.
              </Typography>
              <Button
                component={Link}
                href="http://localhost:8787"
                variant="contained"
                color="primary"
                size="large"
                fullWidth
              >
                Explore the ecosystem
              </Button>
            </CardContent>
          </Card>
        </Box>
      </Stack>

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
              Starting a Business
            </Typography>
            <Typography color="text.secondary">
              Utah provides fertile soil for innovators. Share your idea and get a clear path to launching your business.
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 1, fontSize: "1.4rem" }}>
              Grow Your Business
            </Typography>
            <Typography color="text.secondary">
              Access programs, mentors, and networks tailored to your stage — whether you&rsquo;re early or scaling fast.
            </Typography>
          </CardContent>
        </Card>
        <Card id="why-goed">
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 1, fontSize: "1.4rem" }}>
              Get Funding
            </Typography>
            <Typography color="text.secondary">
              Discover funding opportunities, grants, and investors that champion Utah&rsquo;s entrepreneurial spirit.
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </SiteShell>
  );
}
