// Always use relative paths - Next.js rewrites handle routing

function isNullableString(value) {
  return typeof value === "string" || value === null;
}

function isValidCompanyItem(item) {
  return (
    item &&
    typeof item === "object" &&
    Number.isInteger(item.id) &&
    isNullableString(item.display_type) &&
    isNullableString(item.linkedin) &&
    isNullableString(item.startup_name) &&
    isNullableString(item.full_address) &&
    isNullableString(item.description) &&
    isNullableString(item.website) &&
    isNullableString(item.stage) &&
    isNullableString(item.employees) &&
    isNullableString(item.sector) &&
    (typeof item.latitude === "number" || item.latitude === null) &&
    (typeof item.longitude === "number" || item.longitude === null) &&
    (Number.isInteger(item.employee_count) || item.employee_count === null) &&
    isNullableString(item.size) &&
    Array.isArray(item.photo_gallery)
  );
}

function isValidMindmap(mindmap) {
  if (
    !mindmap ||
    typeof mindmap !== "object" ||
    !Array.isArray(mindmap.sectors)
  ) {
    return false;
  }

  return mindmap.sectors.every((sectorNode) => {
    if (
      !sectorNode ||
      typeof sectorNode !== "object" ||
      typeof sectorNode.name !== "string" ||
      !Array.isArray(sectorNode.stages)
    ) {
      return false;
    }

    return sectorNode.stages.every((stageNode) => {
      if (
        !stageNode ||
        typeof stageNode !== "object" ||
        typeof stageNode.name !== "string" ||
        !Array.isArray(stageNode.companies)
      ) {
        return false;
      }

      return stageNode.companies.every((companyNode) => {
        return (
          companyNode &&
          typeof companyNode === "object" &&
          Number.isInteger(companyNode.id) &&
          isNullableString(companyNode.name)
        );
      });
    });
  });
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
    isNullableString(filters.sector) &&
    isNullableString(filters.size) &&
    isNullableString(filters.stage) &&
    isNullableString(filters.location)
  );
}

function isValidCompanyListResponse(payload) {
  return (
    payload &&
    typeof payload === "object" &&
    Array.isArray(payload.items) &&
    payload.items.every(isValidCompanyItem) &&
    isValidMindmap(payload.mindmap) &&
    isValidPagination(payload.pagination) &&
    isValidFilters(payload.filters)
  );
}

function isValidCompanyDetailResponse(payload) {
  return (
    payload &&
    typeof payload === "object" &&
    payload.item &&
    isValidCompanyItem(payload.item)
  );
}

function buildCompaniesUrl(filters = {}) {
  const url = new URL("/api/companies", window.location.origin);

  url.searchParams.set("page", "1");
  url.searchParams.set("per_page", "100");

  if (filters.sector) {
    url.searchParams.set("sector", filters.sector.trim());
  }

  if (filters.size) {
    url.searchParams.set("size", filters.size.trim());
  }

  if (filters.stage) {
    url.searchParams.set("stage", filters.stage.trim());
  }

  if (filters.location) {
    url.searchParams.set("location", filters.location.trim());
  }

  return url;
}

function buildCompanyDetailUrl(companyId) {
  return new URL(`/api/companies/${companyId}`, window.location.origin);
}

function emptyCompaniesPayload(filters = {}) {
  return {
    items: [],
    mindmap: {
      levels: ["sector", "stage", "company"],
      sectors: [],
    },
    pagination: {
      page: 1,
      per_page: 100,
      total: 0,
      total_pages: 0,
    },
    filters: {
      sector: filters.sector || null,
      size: filters.size || null,
      stage: filters.stage || null,
      location: filters.location || null,
    },
  };
}

export async function fetchCompaniesList(filters, options = {}) {
  const response = await fetch(buildCompaniesUrl(filters), {
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

  if (
    response.status === 404 &&
    payload?.error?.code === "companies_not_found"
  ) {
    return emptyCompaniesPayload(filters);
  }

  if (!response.ok) {
    const message = payload?.error?.message || "Failed to load companies.";
    throw new Error(message);
  }

  if (!isValidCompanyListResponse(payload)) {
    throw new Error(
      "Companies listing response did not match the BE-007 contract.",
    );
  }

  return payload;
}

export async function fetchCompanyDetail(companyId, options = {}) {
  const response = await fetch(buildCompanyDetailUrl(companyId), {
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
      payload?.error?.message || "Failed to load company profile.";
    throw new Error(message);
  }

  if (!isValidCompanyDetailResponse(payload)) {
    throw new Error(
      "Company detail response did not match the BE-007 contract.",
    );
  }

  return payload.item;
}
