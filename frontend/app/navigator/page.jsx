import SiteShell from "@/components/SiteShell";
import { Box, Button, Card, CardContent, Stack, Typography } from "@mui/material";
import Link from "next/link";

export default function NavigatorPage() {
  return (
    <SiteShell>
      <Box component="section" aria-labelledby="navigator-title" sx={{ maxWidth: "44rem" }}>
        <Typography variant="overline" sx={{ letterSpacing: "0.08em", fontWeight: 700, color: "text.secondary" }}>
          Resource Navigator
        </Typography>
        <Typography id="navigator-title" variant="h1" sx={{ mt: 1, mb: 2, fontSize: { xs: "2rem", md: "3rem" } }}>
          Personalized startup support, tuned to your stage.
        </Typography>
        <Typography variant="body1" sx={{ color: "text.secondary" }}>
          Start with your goals and we will match Utah programs, mentors, and funding resources.
        </Typography>
      </Box>

      <Stack direction={{ xs: "column", md: "row" }} spacing={2} mt={4}>
        <Card sx={{ flex: 1 }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 1, fontSize: "1.35rem" }}>
              Next up
            </Typography>
            <Typography color="text.secondary">
              FE-013 adds a chat-first navigator with guided questions, loading and error states, and persistent session context.
            </Typography>
          </CardContent>
        </Card>
      </Stack>

      <Button component={Link} href="/" variant="text" sx={{ mt: 3 }}>
        Back to landing
      </Button>
    </SiteShell>
  );
}
