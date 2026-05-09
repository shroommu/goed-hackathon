const DEFAULT_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";

function normalizeBaseUrl(baseUrl) {
  return (baseUrl || "").replace(/\/$/, "");
}

function isNullableString(value) {
  return typeof value === "string" || value === null;
}

function isValidResourceItem(item) {
  return (
    item &&
    typeof item === "object" &&
    Number.isInteger(item.id) &&
    isNullableString(item.title) &&
    isNullableString(item.description) &&
    isNullableString(item.communities) &&
    isNullableString(item.industries) &&
    isNullableString(item.locations) &&
    isNullableString(item.topics) &&
    isNullableString(item.link) &&
    isNullableString(item.email)
  );
}

function isValidPagination(pagination) {
  return (
    pagination &&
    typeof pagination === "object" &&
    Number.isInteger(pagination.page) &&
    Number.isInteger(pagination.per_page) &&
    Number.isInteger(pagination.total) &&
    Number.isInteger(pagination.total_pages)
  );
}

function isValidFilters(filters) {
  return (
    filters &&
    typeof filters === "object" &&
    isNullableString(filters.communities) &&
    isNullableString(filters.industries) &&
    isNullableString(filters.locations) &&
    isNullableString(filters.topics) &&
    isNullableString(filters.search)
  );
}

function isValidListResponse(payload) {
  return (
    payload &&
    typeof payload === "object" &&
    Array.isArray(payload.items) &&
    payload.items.every(isValidResourceItem) &&
    isValidPagination(payload.pagination) &&
    isValidFilters(payload.filters)
  );
}

function buildResourcesUrl({
  industry,
  location,
  objective,
  stage,
  page = 1,
  perPage = 6,
}) {
  const baseUrl = normalizeBaseUrl(DEFAULT_API_BASE_URL);
  const url = new URL(`${baseUrl}/resources`);

  url.searchParams.set("page", String(page));
  url.searchParams.set("per_page", String(perPage));

  if (industry) {
    url.searchParams.set("industries", industry.trim());
  }

  if (location) {
    url.searchParams.set("locations", location.trim());
  }

  if (objective) {
    url.searchParams.set("search", objective.trim());
  }

  if (stage) {
    const stageToTopics = {
      idea: "mentorship",
      pre_seed: "funding",
      seed: "grants",
      growth: "scaling",
      expansion: "market access",
    };

    const stageTopic = stageToTopics[stage];
    if (stageTopic) {
      url.searchParams.set("topics", stageTopic);
    }
  }

  return url;
}

export async function fetchResourceRecommendations(preferences, options = {}) {
  const response = await fetch(buildResourcesUrl(preferences), {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    signal: options.signal,
    cache: "no-store",
  });

  let payload = null;

  try {
    payload = await response.json();
  } catch {
    throw new Error("Backend response was not valid JSON.");
  }

  if (!response.ok) {
    const message =
      payload?.error?.message || "Failed to load recommendations.";
    throw new Error(message);
  }

  if (!isValidListResponse(payload)) {
    throw new Error(
      "Recommendation response did not match the BE-006 contract.",
    );
  }

  return payload;
}
