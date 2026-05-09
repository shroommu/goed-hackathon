"use client";

import CssBaseline from "@mui/material/CssBaseline";
import GlobalStyles from "@mui/material/GlobalStyles";
import { ThemeProvider, createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#38bdf8",
      light: "#7dd3fc",
      dark: "#0284c7",
      contrastText: "#0b1120"
    },
    secondary: {
      main: "#34d399",
      light: "#6ee7b7",
      dark: "#059669",
      contrastText: "#052e16"
    },
    background: {
      default: "#0b1120",
      paper: "#111c2e"
    },
    text: {
      primary: "#e8f4fc",
      secondary: "#94a3b8"
    },
    divider: "rgba(148, 163, 184, 0.18)"
  },
  shape: {
    borderRadius: 12
  },
  typography: {
    fontFamily: "var(--font-body)",
    h1: {
      fontFamily: "var(--font-heading)",
      fontWeight: 650,
      lineHeight: 1.12
    },
    h2: {
      fontFamily: "var(--font-heading)",
      fontWeight: 600,
      lineHeight: 1.15
    }
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: ({ theme: t }) => ({
          border: `1px solid ${t.palette.divider}`,
          boxShadow: "0 18px 50px rgb(0 0 0 / 0.35)"
        })
      }
    }
  }
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
              radial-gradient(ellipse 120% 80% at 0% -20%, rgb(56 189 248 / 0.14), transparent 50%),
              radial-gradient(ellipse 90% 60% at 100% 0%, rgb(52 211 153 / 0.1), transparent 45%),
              linear-gradient(180deg, #0b1120 0%, #070b14 100%)
            `,
            backgroundAttachment: "fixed"
          }
        }}
      />
      {children}
    </ThemeProvider>
  );
}