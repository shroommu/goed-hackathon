"use client";

import Link from "next/link";
import { useState } from "react";

const navLinks = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#why-goed", label: "Why GOED" },
  { href: "#get-started", label: "Get started" }
];

export default function SiteShell({ children }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      <header className="site-header">
        <div className="site-header-inner">
          <Link className="brand" href="/" aria-label="GOED home">
            <span className="brand-mark" aria-hidden="true">
              G
            </span>
            <span className="brand-text">GOED Founders</span>
          </Link>

          <button
            type="button"
            className="mobile-menu-toggle"
            aria-controls="primary-navigation"
            aria-expanded={isMobileMenuOpen}
            onClick={() => setIsMobileMenuOpen((current) => !current)}
          >
            Menu
          </button>

          <nav
            id="primary-navigation"
            className={`site-nav ${isMobileMenuOpen ? "site-nav-open" : ""}`}
            aria-label="Primary"
          >
            <ul>
              {navLinks.map((link) => (
                <li key={link.href}>
                  <a href={link.href}>{link.label}</a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>

      <main id="main-content" tabIndex={-1}>
        {children}
      </main>

      <footer className="site-footer">
        <p>Built for Utah startup discovery and founder acceleration.</p>
      </footer>
    </>
  );
}
