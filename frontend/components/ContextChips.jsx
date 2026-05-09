import { Chip, Stack, TextField } from "@mui/material";
import { useState } from "react";

const ARRAY_FIELDS = new Set(["objectives", "topics", "challenges"]);

export default function ContextChips({ context, onContextUpdate }) {
  const [editingField, setEditingField] = useState(null);
  const [editingValue, setEditingValue] = useState("");

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

  const formatContextValue = (value) => (Array.isArray(value) ? value.join(", ") : value || "");

  const parseContextValue = (key, value) => {
    if (!value.trim()) {
      return null;
    }

    if (ARRAY_FIELDS.has(key)) {
      const items = value.split(",").map((v) => v.trim()).filter(Boolean);
      return items.length > 0 ? items : null;
    }

    return value.trim();
  };

  const startEditing = (chip) => {
    setEditingField(chip.key);
    setEditingValue(chip.value);
  };

  const stopEditing = () => {
    setEditingField(null);
    setEditingValue("");
  };

  const saveEditing = () => {
    if (!editingField) {
      return;
    }

    const nextValue = parseContextValue(editingField, editingValue);
    onContextUpdate({ [editingField]: nextValue });
    stopEditing();
  };

  const handleEditKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      saveEditing();
    }

    if (event.key === "Escape") {
      stopEditing();
    }
  };

  const handleDelete = (key) => {
    if (editingField === key) {
      stopEditing();
    }

    onContextUpdate({ [key]: null });
  };

  const chips = chipFields
    .filter((field) => context[field.key])
    .map((field) => ({
      key: field.key,
      label: field.label,
      value: formatContextValue(context[field.key])
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
        {chips.map((chip) =>
          editingField === chip.key ? (
            <TextField
              key={chip.key}
              autoFocus
              label={chip.label}
              value={editingValue}
              onChange={(event) => setEditingValue(event.target.value)}
              onBlur={saveEditing}
              onKeyDown={handleEditKeyDown}
              size="small"
              variant="outlined"
              slotProps={{
                input: {
                  sx: { height: 28, fontSize: "0.8125rem" }
                },
                inputLabel: {
                  sx: { fontSize: "0.8125rem" }
                }
              }}
              sx={{
                width: { xs: 220, sm: 260 },
                flexShrink: 0
              }}
            />
          ) : (
            <Chip
              key={chip.key}
              label={`${chip.label}: ${chip.value}`}
              onClick={() => startEditing(chip)}
              onDelete={() => handleDelete(chip.key)}
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
          )
        )}
      </Stack>
    </Stack>
  );
}
