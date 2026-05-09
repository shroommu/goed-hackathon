import { Chip, Stack } from "@mui/material";
import { useState } from "react";

export default function ContextChips({ context, onContextUpdate }) {
  const [editingField, setEditingField] = useState(null);

  const chipFields = [
    { key: "stage", label: "Stage" },
    { key: "industry", label: "Industry" },
    { key: "location", label: "Location" }
  ];

  // Show objectives, topics, challenges if they exist
  if (context.objectives && context.objectives.length > 0) {
    chipFields.push({ key: "objectives", label: "Goals" });
  }
  if (context.topics && context.topics.length > 0) {
    chipFields.push({ key: "topics", label: "Topics" });
  }
  if (context.challenges && context.challenges.length > 0) {
    chipFields.push({ key: "challenges", label: "Challenges" });
  }

  const handleChipClick = (field) => {
    const newValue = prompt(
      `Edit ${field.label}:`,
      Array.isArray(context[field.key])
        ? context[field.key].join(", ")
        : context[field.key] || ""
    );

    if (newValue !== null) {
      // Handle array fields
      if (["objectives", "topics", "challenges"].includes(field.key)) {
        onContextUpdate({
          [field.key]: newValue.split(",").map((v) => v.trim()).filter(Boolean)
        });
      } else {
        onContextUpdate({ [field.key]: newValue.trim() });
      }
    }
  };

  const chips = chipFields
    .filter((field) => context[field.key])
    .map((field) => ({
      key: field.key,
      label: field.label,
      value: Array.isArray(context[field.key])
        ? context[field.key].join(", ")
        : context[field.key]
    }));

  if (chips.length === 0) {
    return null;
  }

  return (
    <Stack
      sx={{
        px: { xs: 2, sm: 3 },
        py: 1.5,
        bgcolor: "background.paper",
        borderTop: 1,
        borderColor: "divider"
      }}
    >
      <Stack
        direction="row"
        spacing={1}
        flexWrap="wrap"
        sx={{
          width: "100%",
          maxWidth: "58rem",
          mx: "auto",
          rowGap: 1,
          overflowX: { xs: "auto", sm: "visible" },
          overflowY: "visible"
        }}
        role="group"
        aria-label="Conversation context"
      >
        {chips.map((chip) => (
          <Chip
            key={chip.key}
            label={`${chip.label}: ${chip.value}`}
            onClick={() => handleChipClick(chipFields.find((f) => f.key === chip.key))}
            color="primary"
            variant="outlined"
            size="small"
            sx={{
              cursor: "pointer",
              flexShrink: { xs: 0, sm: 1 },
              "&:hover": {
                bgcolor: "primary.light",
                color: "primary.contrastText"
              }
            }}
          />
        ))}
      </Stack>
    </Stack>
  );
}
