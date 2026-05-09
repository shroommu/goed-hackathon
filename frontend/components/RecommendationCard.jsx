import {
  Card,
  CardActions,
  CardContent,
  Chip,
  Link as MuiLink,
  Stack,
  Typography
} from "@mui/material";
import { splitResourceTags } from "../lib/tagUtils";

const chipSx = {
  fontSize: "0.75rem",
  maxWidth: "100%",
  height: "auto",
  "& .MuiChip-label": {
    whiteSpace: "normal",
    overflow: "visible",
    textOverflow: "clip",
    py: 0.5
  }
};

function TagChipRow({ items }) {
  if (!items.length) {
    return null;
  }
  return (
    <Stack direction="row" useFlexGap flexWrap="wrap" spacing={0.75}>
      {items.map((label, idx) => (
        <Chip
          key={`${idx}-${label}`}
          size="small"
          label={label}
          variant="outlined"
          sx={chipSx}
        />
      ))}
    </Stack>
  );
}

function TagSection({ title, items }) {
  if (!items.length) {
    return null;
  }
  return (
    <Stack spacing={0.5}>
      <Typography
        variant="caption"
        sx={{
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: "text.secondary",
          fontWeight: 600
        }}
      >
        {title}
      </Typography>
      <TagChipRow items={items} />
    </Stack>
  );
}

export default function RecommendationCard({ recommendation }) {
  const industries = splitResourceTags(recommendation.industries);
  const topics = splitResourceTags(recommendation.topics);
  const communities = splitResourceTags(recommendation.communities);
  const locations = splitResourceTags(recommendation.locations);
  const hasTags =
    industries.length > 0 ||
    topics.length > 0 ||
    communities.length > 0 ||
    locations.length > 0;

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

        {hasTags && (
          <Stack spacing={1.5}>
            <TagSection title="Sector & industry" items={industries} />
            <TagSection title="Topics & program types" items={topics} />
            <TagSection title="Communities" items={communities} />
            <TagSection title="Location" items={locations} />
          </Stack>
        )}
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
