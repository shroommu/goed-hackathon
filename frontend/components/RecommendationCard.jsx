import {
  Card,
  CardActions,
  CardContent,
  Chip,
  Link as MuiLink,
  Stack,
  Typography
} from "@mui/material";

export default function RecommendationCard({ recommendation }) {
  return (
    <Card
      sx={{
        maxWidth: "32rem",
        mt: 1,
        mb: 1,
        boxShadow: 2
      }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Typography variant="h3" sx={{ fontSize: "1.1rem", mb: 1, lineHeight: 1.3 }}>
          {recommendation.title}
        </Typography>

        {recommendation.description && (
          <Typography color="text.secondary" sx={{ mb: 1.5, fontSize: "0.9rem" }}>
            {recommendation.description}
          </Typography>
        )}

        {recommendation.rationale && (
          <>
            <Typography
              variant="subtitle2"
              sx={{ mb: 0.75, fontWeight: 700, fontSize: "0.85rem" }}
            >
              Why this matches
            </Typography>
            <Typography variant="body2" sx={{ mb: 1.5, fontStyle: "italic" }}>
              {recommendation.rationale}
            </Typography>
          </>
        )}

        <Stack direction="row" spacing={0.75} flexWrap="wrap" sx={{ rowGap: 0.75 }}>
          {recommendation.industries && (
            <Chip
              size="small"
              label={recommendation.industries}
              variant="outlined"
              sx={{ fontSize: "0.75rem" }}
            />
          )}
          {recommendation.topics && (
            <Chip
              size="small"
              label={recommendation.topics}
              variant="outlined"
              sx={{ fontSize: "0.75rem" }}
            />
          )}
          {recommendation.locations && (
            <Chip
              size="small"
              label={recommendation.locations}
              variant="outlined"
              sx={{ fontSize: "0.75rem" }}
            />
          )}
        </Stack>
      </CardContent>

      {recommendation.url && recommendation.url !== "#" && (
        <CardActions sx={{ px: 2.5, pb: 2.5, pt: 0 }}>
          <MuiLink
            href={recommendation.url}
            target="_blank"
            rel="noreferrer noopener"
            underline="hover"
            sx={{ fontWeight: 600, fontSize: "0.9rem" }}
          >
            Visit resource →
          </MuiLink>
        </CardActions>
      )}
    </Card>
  );
}
