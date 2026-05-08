import SiteShell from "@/components/SiteShell";
import { Box, Button, Card, CardContent, Stack, Typography } from "@mui/material";
import Link from "next/link";

export default function MapPage() {
  return (
    <SiteShell>
      <Box component="section" aria-labelledby="map-title" sx={{ maxWidth: "44rem" }}>
        <Typography variant="overline" sx={{ letterSpacing: "0.08em", fontWeight: 700, color: "text.secondary" }}>
          Utah Startup Map
        </Typography>
        <Typography id="map-title" variant="h1" sx={{ mt: 1, mb: 2, fontSize: { xs: "2rem", md: "3rem" } }}>
          Explore Utah companies by sector, stage, and hiring momentum.
        </Typography>
        <Typography variant="body1" sx={{ color: "text.secondary" }}>
          This route is ready for FE-005 interactive map experiences. It currently acts as the mode destination for investor and ecosystem exploration.
        </Typography>
      </Box>

      <Stack direction={{ xs: "column", md: "row" }} spacing={2} mt={4}>
        <Card sx={{ flex: 1 }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h2" sx={{ mb: 1, fontSize: "1.35rem" }}>
              Next up
            </Typography>
            <Typography color="text.secondary">
              FE-005 adds pan/zoom map rendering, filter controls, clustering, and linked list views.
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
