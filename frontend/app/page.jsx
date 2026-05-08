import SiteShell from "@/components/SiteShell";
import { Box, Button, Card, CardContent, Stack, Typography } from "@mui/material";

export default function HomePage() {
  return (
    <SiteShell>
      <Box component="section" aria-labelledby="hero-title" sx={{ maxWidth: "44rem" }}>
        <Typography
          variant="overline"
          sx={{ letterSpacing: "0.08em", fontWeight: 700, color: "text.secondary" }}
        >
          Utah startup launchpad
        </Typography>
        <Typography id="hero-title" variant="h1" sx={{ mt: 1, mb: 2, fontSize: { xs: "2rem", md: "3.4rem" } }}>
          Navigate funding, mentors, and programs in under 2 minutes.
        </Typography>
        <Typography variant="body1" sx={{ color: "text.secondary", fontSize: { xs: "1rem", md: "1.2rem" } }}>
          GOED Founders helps you choose the right support path and move from idea to execution with local, relevant recommendations.
        </Typography>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} mt={4} id="get-started">
          <Button variant="contained" color="primary" href="#how-it-works" size="large">
            Start as founder
          </Button>
          <Button
            variant="outlined"
            color="primary"
            href="#why-goed"
            size="large"
            sx={{ backgroundColor: "#ede7d8", borderColor: "#d7d2c7" }}
          >
            Explore startup map
          </Button>
        </Stack>
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
              Share what you are building, your traction, and your funding target.
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 1, fontSize: "1.4rem" }}>
              Get matched
            </Typography>
            <Typography color="text.secondary">
              Receive personalized recommendations with clear rationale and links.
            </Typography>
          </CardContent>
        </Card>
        <Card id="why-goed">
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 1, fontSize: "1.4rem" }}>
              Take action
            </Typography>
            <Typography color="text.secondary">
              Move from discovery to outreach with curated next steps built for Utah founders.
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </SiteShell>
  );
}
