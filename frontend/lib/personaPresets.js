/**
 * Persona presets for the resource navigator validation harness (FE-010).
 *
 * Source of truth: `project_requirements.md` § 4 "Test Personas (Validation Set)".
 * The platform must produce meaningfully different top recommendations across
 * these six personas (resource navigator acceptance criterion #2 and
 * deliverable definition of done #6).
 *
 * Each persona is a single-turn scenario with the persona's preset context
 * and a short, in-character message so the recommendation surface can be
 * compared apples-to-apples.
 */

export const PERSONA_PRESETS = [
  {
    id: "jordan-slc-preseed",
    name: "Jordan — pre-seed, first-time founder (SLC)",
    summary:
      "Jordan, 20, Salt Lake City. Pre-seed, first-time founder exploring an early idea.",
    expectedSignals: [
      "Pre-seed / idea-stage programs",
      "First-time founder education and mentorship",
      "Salt Lake City / Wasatch Front community resources"
    ],
    context: {
      stage: "pre-seed",
      industry: "Technology",
      location: "Salt Lake City, UT",
      objectives: ["validate idea", "find mentorship", "early funding"],
      topics: ["first-time founder"],
      challenges: ["never started a company before"]
    },
    message:
      "I'm Jordan, 20, in Salt Lake City. I'm a first-time founder at the pre-seed stage and I want to figure out what programs and mentors I should be talking to. Where do I start?"
  },
  {
    id: "maria-washington-rural-ag",
    name: "Maria — rural woman-owned agriculture (Washington County)",
    summary:
      "Maria, 38, Washington County. Rural woman-owned agricultural business looking to scale.",
    expectedSignals: [
      "Agriculture-specific programs",
      "Rural Utah / Washington County resources",
      "Women-owned business support and capital access"
    ],
    context: {
      stage: "growth",
      industry: "Agriculture",
      location: "Washington County, UT",
      objectives: ["scale operations", "funding", "women-owned business support"],
      topics: ["agriculture", "rural business"],
      challenges: ["rural location", "scaling capital"]
    },
    message:
      "I'm Maria, 38, running a woman-owned agricultural business in rural Washington County. We're ready to scale and need capital and any programs that specifically support rural or women-owned businesses in Utah."
  },
  {
    id: "marcus-ogden-veteran-mfg",
    name: "Marcus — veteran-owned manufacturing startup (Ogden)",
    summary:
      "Marcus, 34, Ogden / Weber County. Veteran founder building a manufacturing startup.",
    expectedSignals: [
      "Veteran-owned business resources",
      "Manufacturing / advanced manufacturing programs",
      "Weber County / Ogden workforce support"
    ],
    context: {
      stage: "startup",
      industry: "Manufacturing",
      location: "Ogden, UT (Weber County)",
      objectives: ["funding", "workforce development", "veteran resources"],
      topics: ["veteran-owned", "manufacturing"],
      challenges: ["hiring skilled labor", "capital equipment"]
    },
    message:
      "I'm Marcus, 34, a Navy veteran starting a manufacturing company in Ogden. I'm looking for veteran-owned business support, manufacturing programs, and any workforce help available in Weber County."
  },
  {
    id: "priya-slc-b2b-saas-raise",
    name: "Priya — B2B SaaS, first VC/angel raise (SLC)",
    summary:
      "Priya, 31, Salt Lake City. B2B SaaS founder preparing for her first VC/angel round.",
    expectedSignals: [
      "Investor / VC and angel network connections",
      "Pitch readiness and accelerator programs",
      "B2B SaaS / tech ecosystem support"
    ],
    context: {
      stage: "early-stage",
      industry: "B2B SaaS",
      location: "Salt Lake City, UT",
      objectives: ["raise first round", "investor introductions", "pitch readiness"],
      topics: ["VC", "angel investors", "SaaS"],
      challenges: ["fundraising", "investor network access"]
    },
    message:
      "I'm Priya, 31, building a B2B SaaS in Salt Lake City. We have product-market fit signals and I'm getting ready for my first VC or angel raise. What investor networks, pitch programs, or accelerators in Utah should I be plugged into?"
  },
  {
    id: "david-provo-meddevice-growth",
    name: "David — med-device growth-stage, international (Provo)",
    summary:
      "David, 45, Provo / Utah County. Med-device growth-stage company expanding internationally.",
    expectedSignals: [
      "Growth-stage and international expansion programs",
      "Export assistance and trade missions",
      "Medical device / regulated industry resources"
    ],
    context: {
      stage: "growth",
      industry: "Medical devices",
      location: "Provo, UT (Utah County)",
      objectives: ["international expansion", "export assistance", "regulatory support"],
      topics: ["med-device", "international trade"],
      challenges: ["FDA / regulatory complexity", "entering foreign markets"]
    },
    message:
      "I'm David, 45, leading a growth-stage medical-device company in Provo. We're expanding internationally and need help with export programs, trade missions, and any Utah resources that understand regulated medical-device markets."
  },
  {
    id: "amir-slc-university-research",
    name: "Dr. Amir — university researcher commercializing tech (SLC)",
    summary:
      "Dr. Amir, 29, Salt Lake City. University researcher commercializing novel technology.",
    expectedSignals: [
      "University commercialization / tech transfer support",
      "Non-dilutive R&D funding (SBIR/STTR)",
      "Deep-tech / research-to-startup programs"
    ],
    context: {
      stage: "pre-seed",
      industry: "Deep tech / research commercialization",
      location: "Salt Lake City, UT",
      objectives: ["commercialize research", "non-dilutive funding", "tech transfer"],
      topics: ["university spin-out", "SBIR", "deep tech"],
      challenges: ["IP and licensing", "long R&D timeline"]
    },
    message:
      "I'm Dr. Amir, 29, a university researcher in Salt Lake City spinning a novel technology out of the lab. I'm looking for tech-transfer support, SBIR-style non-dilutive funding, and programs designed for university-based commercialization in Utah."
  }
];

export function getPersonaById(id) {
  return PERSONA_PRESETS.find((p) => p.id === id) || null;
}
