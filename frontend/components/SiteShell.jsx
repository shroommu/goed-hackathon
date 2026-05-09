"use client";

import MenuIcon from "@mui/icons-material/Menu";
import {
  AppBar,
  Box,
  Container,
  Drawer,
  IconButton,
  Link as MuiLink,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Toolbar,
  Typography,
  Button
} from "@mui/material";
import Link from "next/link";
import { useState } from "react";

const navLinks = [
  { href: "/navigator", label: "Resource Navigator" },
  { href: "/map", label: "Startup Map" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#get-started", label: "Choose mode" }
];

export default function SiteShell({ children }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      <AppBar
        position="sticky"
        color="transparent"
        elevation={0}
        sx={{
          borderBottom: "1px solid #d7d2c7",
          backdropFilter: "blur(8px)",
          backgroundColor: "rgb(248 246 241 / 92%)"
        }}
      >
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ minHeight: 72 }}>
            <MuiLink
              component={Link}
              href="/"
              underline="none"
              aria-label="GOED home"
              sx={{
                display: "inline-flex",
                alignItems: "center",
                gap: 1.25,
                color: "text.primary",
                mr: 2
              }}
            >
              <Box
                aria-hidden="true"
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: "999px",
                  backgroundColor: "primary.main",
                  color: "background.default",
                  display: "grid",
                  placeItems: "center",
                  fontFamily: "var(--font-heading)",
                  fontWeight: 700
                }}
              >
                G
              </Box>
              <Typography fontWeight={700} letterSpacing="0.02em">
                GOED Navigator
              </Typography>
            </MuiLink>

            <Box sx={{ display: { xs: "none", md: "flex" }, gap: 1, ml: "auto" }}>
              {navLinks.map((link) => (
                <Button key={link.href} component="a" href={link.href} color="inherit" sx={{ fontWeight: 600 }}>
                  {link.label}
                </Button>
              ))}
            </Box>

            <IconButton
              aria-label="Open menu"
              aria-controls="primary-navigation"
              aria-expanded={isMobileMenuOpen}
              onClick={() => setIsMobileMenuOpen(true)}
              sx={{ ml: "auto", display: { xs: "inline-flex", md: "none" } }}
            >
              <MenuIcon />
            </IconButton>
          </Toolbar>
        </Container>
      </AppBar>

      <Drawer
        id="primary-navigation"
        anchor="right"
        open={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
        sx={{ display: { xs: "block", md: "none" } }}
      >
        <Box sx={{ width: 280, pt: 2 }} role="presentation">
          <List>
            {navLinks.map((link) => (
              <ListItem key={link.href} disablePadding>
                <ListItemButton component="a" href={link.href} onClick={() => setIsMobileMenuOpen(false)}>
                  <ListItemText primary={link.label} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      <Box component="main" id="main-content" tabIndex={-1}>
        <Container maxWidth="lg" sx={{ py: { xs: 6, md: 8 } }}>
          {children}
        </Container>
      </Box>

      <Box component="footer" sx={{ borderTop: "1px solid #d7d2c7" }}>
        <Container maxWidth="lg" sx={{ py: 3, color: "text.secondary", fontSize: "0.9rem" }}>
          <Typography variant="body2">Built for Utah startup discovery and resource navigation.</Typography>
        </Container>
      </Box>
    </>
  );
}
