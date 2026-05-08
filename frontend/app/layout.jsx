import { Fraunces, Public_Sans } from "next/font/google";
import "./globals.css";

const headingFont = Fraunces({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-heading"
});

const bodyFont = Public_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-body"
});

export const metadata = {
  title: "GOED Founders",
  description: "Find the right startup support path in Utah, fast."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${headingFont.variable} ${bodyFont.variable}`}>
      <body>{children}</body>
    </html>
  );
}
