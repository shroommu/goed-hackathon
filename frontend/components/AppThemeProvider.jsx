"use client";

import CssBaseline from "@mui/material/CssBaseline";
import GlobalStyles from "@mui/material/GlobalStyles";
import { ThemeProvider, createTheme } from "@mui/material/styles";

const BG_DEFAULT = "#0a0f1e";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#d4af37",
      light: "#ffd700",
      dark: "#b8860b",
      contrastText: BG_DEFAULT,
    },
    secondary: {
      main: "#64a0ff",
      light: "#93c5fd",
      dark: "#3b82f6",
      contrastText: "#f1f5f9",
    },
    background: {
      default: BG_DEFAULT,
      paper: "#111827",
    },
    text: {
      primary: "#e2e8f0",
      secondary: "#94a3b8",
    },
    divider: "rgba(148, 163, 184, 0.18)",
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily: "var(--font-body)",
    h1: {
      fontFamily: "var(--font-heading)",
      fontWeight: 650,
      lineHeight: 1.12,
    },
    h2: {
      fontFamily: "var(--font-heading)",
      fontWeight: 600,
      lineHeight: 1.15,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: ({ theme: t }) => ({
          border: `1px solid ${t.palette.divider}`,
          boxShadow: "0 18px 50px rgb(0 0 0 / 0.35)",
        }),
      },
    },
    MuiButton: {
      styleOverrides: {
        containedPrimary: {
          background: `linear-gradient(135deg, #b8860b 0%, #ffd700 100%)`,
          color: BG_DEFAULT,
          fontWeight: 700,
          letterSpacing: "0.04em",
          boxShadow: "0 0 28px rgba(255, 215, 0, 0.22)",
          "&:hover": {
            background: `linear-gradient(135deg, #a67c00 0%, #e6c200 100%)`,
            boxShadow: "0 0 40px rgba(255, 215, 0, 0.35)",
          },
        },
        outlinedPrimary: {
          borderColor: "rgba(212, 175, 55, 0.55)",
          color: "primary.light",
          "&:hover": {
            borderColor: "primary.main",
            backgroundColor: "rgba(212, 175, 55, 0.08)",
          },
        },
        textPrimary: {
          color: "primary.light",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        colorPrimary: {
          backgroundColor: "rgba(212, 175, 55, 0.18)",
          color: "primary.light",
          border: "1px solid rgba(212, 175, 55, 0.35)",
        },
        colorSecondary: {
          backgroundColor: "rgba(100, 160, 255, 0.14)",
          color: "secondary.light",
          border: "1px solid rgba(100, 160, 255, 0.3)",
        },
      },
    },
  },
});

export default function AppThemeProvider({ children }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline enableColorScheme />
      <GlobalStyles
        styles={{
          body: {
            backgroundColor: theme.palette.background.default,
            backgroundImage: `
              radial-gradient(ellipse 75% 42% at 50% 36%, rgba(184, 134, 11, 0.09) 0%, transparent 56%),
              radial-gradient(ellipse 95% 55% at 100% -8%, rgba(100, 160, 255, 0.055) 0%, transparent 46%),
              linear-gradient(180deg, ${BG_DEFAULT} 0%, #050810 100%)
            `,
            backgroundAttachment: "fixed",
          },
        }}
      />
      {children}
    </ThemeProvider>
  );
}
