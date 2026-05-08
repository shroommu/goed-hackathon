"use client";

import CssBaseline from "@mui/material/CssBaseline";
import GlobalStyles from "@mui/material/GlobalStyles";
import { ThemeProvider, createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#14213d"
    },
    secondary: {
      main: "#fca311"
    },
    background: {
      default: "#f8f6f1",
      paper: "#fffdf7"
    },
    text: {
      primary: "#14213d",
      secondary: "#425466"
    }
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
        root: {
          border: "1px solid #d7d2c7",
          boxShadow: "0 16px 45px rgb(20 33 61 / 0.1)"
        }
      }
    }
  }
});

export default function AppThemeProvider({ children }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <GlobalStyles
        styles={{
          body: {
            background:
              "radial-gradient(circle at 10% 0%, #ffe8b7 0%, rgb(255 232 183 / 0%) 32%), linear-gradient(180deg, #f8f6f1 0%, #f4f0e5 100%)"
          },
          ".skip-link": {
            position: "absolute",
            left: "1rem",
            top: "-120px",
            zIndex: 1200,
            padding: "0.75rem 1rem",
            borderRadius: "0.5rem",
            background: "#14213d",
            color: "#f8f6f1",
            textDecoration: "none",
            transition: "top 180ms ease"
          },
          ".skip-link:focus": {
            top: "0.75rem"
          }
        }}
      />
      {children}
    </ThemeProvider>
  );
}