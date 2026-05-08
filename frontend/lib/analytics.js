const STORAGE_KEY = "goed:landingCtaEvents";
const MAX_STORED_EVENTS = 100;

function pushToStorage(eventPayload) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    const existing = JSON.parse(
      window.localStorage.getItem(STORAGE_KEY) || "[]",
    );
    existing.push(eventPayload);
    const recentEvents = existing.slice(-MAX_STORED_EVENTS);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(recentEvents));
  } catch (error) {
    // Ignore storage issues in private browsing or restricted contexts.
  }
}

function pushToDataLayer(eventPayload) {
  if (typeof window === "undefined") {
    return;
  }

  if (Array.isArray(window.dataLayer)) {
    window.dataLayer.push(eventPayload);
  }

  if (typeof window.gtag === "function") {
    window.gtag("event", "landing_cta_click", {
      cta_id: eventPayload.ctaId,
      mode: eventPayload.mode,
      destination: eventPayload.destination,
      page_path: eventPayload.path,
    });
  }
}

function sendBeacon(eventPayload) {
  if (typeof window === "undefined") {
    return;
  }

  const body = JSON.stringify(eventPayload);

  if (typeof window.navigator?.sendBeacon === "function") {
    window.navigator.sendBeacon(
      "/api/analytics",
      new Blob([body], { type: "application/json" }),
    );
    return;
  }

  fetch("/api/analytics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    keepalive: true,
  }).catch(() => {
    // Non-blocking tracking fallback.
  });
}

export function trackLandingCta({ ctaId, mode, destination }) {
  if (typeof window === "undefined") {
    return;
  }

  const payload = {
    event: "landing_cta_click",
    ctaId,
    mode,
    destination,
    timestamp: new Date().toISOString(),
    path: window.location.pathname,
  };

  pushToStorage(payload);
  pushToDataLayer(payload);
  sendBeacon(payload);
}
