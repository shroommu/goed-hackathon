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
import { alpha } from "@mui/material/styles";
import Link from "next/link";
import { useState } from "react";

const navLinks = [
  { href: "/navigator", label: "Start Your Journey" },
  { href: "/map", label: "Explore Ecosystem" },
  { href: "#how-it-works", label: "Resources" },
  { href: "#get-started", label: "Get Started" }
];

export default function SiteShell({ children }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <>
      <AppBar
        position="sticky"
        color="transparent"
        elevation={0}
        sx={(theme) => ({
          borderBottom: `1px solid ${theme.palette.divider}`,
          backdropFilter: "blur(12px)",
          backgroundColor: alpha(theme.palette.background.default, 0.88)
        })}
      >
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ minHeight: 72 }}>
            <MuiLink
              component={Link}
              href="/"
              underline="none"
              aria-label="Utah Startup State home"
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
                  color: "primary.contrastText",
                  display: "grid",
                  placeItems: "center",
                  fontFamily: "var(--font-heading)",
                  fontWeight: 700
                }}
              >
                U
              </Box>
              <Typography fontWeight={700} letterSpacing="0.02em">
                Utah Startup State
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
        <Container
          maxWidth="lg"
          sx={{
            py: { xs: 6, md: 8 },
            px: { xs: 2, md: 3 },
            width: "100%"
          }}
        >
          {children}
        </Container>
      </Box>

      <Box component="footer" sx={{ borderTop: 1, borderColor: "divider" }}>
        <Container maxWidth="lg" sx={{ py: 3, color: "text.secondary", fontSize: "0.9rem" }}>
          <Typography variant="body2">Governor&rsquo;s Office of Economic Opportunity &mdash; Empowering Utah&rsquo;s entrepreneurs and the Startup Capital of the World.</Typography>
        </Container>
      </Box>
    </>
  );
}
