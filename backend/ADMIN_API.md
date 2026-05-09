# Admin API Documentation - BE-010

## Overview
Admin endpoints for managing resources and companies, including creation, editing, and archiving (soft delete) functionality.

## Authentication (BE-011)
Admin endpoints require a valid **Supabase user JWT** with `app_metadata.role` set to `"admin"`. Pass the access token in the `Authorization` header:

```
Authorization: Bearer <supabase_access_token>
```

The API verifies JWTs locally when `SUPABASE_JWT_SECRET` is set (recommended for production). Otherwise it validates the token via the Supabase Auth `/user` endpoint (requires `SUPABASE_URL` and a publishable or anon key).

All routes below are mounted under the `/api` prefix (for example `POST /api/admin/resources`).

## Environment Variables
```bash
SUPABASE_JWT_SECRET=<project_jwt_secret>   # enables local JWT verification (HS256)
SUPABASE_URL=https://<project>.supabase.co # required if JWT secret is not set
SUPABASE_PUBLISHABLE_KEY=...               # or SUPABASE_ANON_KEY
```

## Endpoints

### Resources

#### Create Resource
```
POST /admin/resources
Content-Type: application/json
Authorization: Bearer <supabase_access_token>

{
  "title": "Resource Title",
  "description": "Resource description",
  "communities": "Community names",
  "industries": "Industry names",
  "locations": "Location names",
  "topics": "Topic names",
  "link": "https://example.com",
  "email": "contact@example.com"
}
```

**Response (201 Created):**
```json
{
  "message": "Resource created successfully.",
  "resource": {
    "id": 123,
    "title": "Resource Title",
    "description": "Resource description",
    "communities": "Community names",
    "industries": "Industry names",
    "locations": "Location names",
    "topics": "Topic names",
    "link": "https://example.com",
    "email": "contact@example.com",
    "archived": false
  }
}
```

#### Update Resource
```
PATCH /admin/resources/:id
Content-Type: application/json
Authorization: Bearer <supabase_access_token>

{
  "title": "Updated Title",
  "description": "Updated description"
}
```

**Note:** Only include fields you want to update. Omitted fields remain unchanged.

**Response (200 OK):**
```json
{
  "message": "Resource updated successfully.",
  "resource": { ... }
}
```

#### Archive Resource
```
POST /admin/resources/:id/archive
Authorization: Bearer <supabase_access_token>
```

**Response (200 OK):**
```json
{
  "message": "Resource archived successfully.",
  "resource": { ... }
}
```

### Companies

#### Update Company
```
PATCH /admin/companies/:id
Content-Type: application/json
Authorization: Bearer <supabase_access_token>

{
  "startup_name": "Updated Company Name",
  "description": "Updated description",
  "website": "https://example.com",
  "stage": "seed",
  "employees": "11-50",
  "sector": "Technology",
  "full_address": "123 Main St, City, State",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "linkedin": "https://linkedin.com/company/example",
  "display_type": "startup"
}
```

**Note:** Only include fields you want to update. Omitted fields remain unchanged.

**Response (200 OK):**
```json
{
  "message": "Company updated successfully.",
  "company": { ... }
}
```

#### Archive Company
```
POST /admin/companies/:id/archive
Authorization: Bearer <supabase_access_token>
```

**Response (200 OK):**
```json
{
  "message": "Company archived successfully.",
  "company": { ... }
}
```

## Error Responses

### Missing Authorization
**Status: 401 Unauthorized**
```json
{
  "error": {
    "code": "missing_authorization",
    "message": "Authorization header is required."
  }
}
```

### Invalid API Key
**Status: 401 Unauthorized**
```json
{
  "error": {
    "code": "invalid_credentials",
    "message": "Invalid API key."
  }
}
```

### Resource/Company Not Found
**Status: 404 Not Found**
```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Resource with id 123 not found."
  }
}
```

### Already Archived
**Status: 400 Bad Request**
```json
{
  "error": {
    "code": "already_archived",
    "message": "Resource with id 123 is already archived."
  }
}
```

## Archived Records Behavior

- Archived resources and companies are **soft deleted** (not removed from database)
- They are **automatically filtered out** from all public API queries
- Archived records are retained in the database for audit purposes
- The `archived` field is set to `TRUE` when archiving
- Admin endpoints can still access archived records by ID (they're just marked as archived)

## Implementation Details

### Database Changes
- Added `archived` BOOLEAN column to `resources` table (default: FALSE)
- Added `archived` BOOLEAN column to `companies` table (default: FALSE)
- Added indexes on `archived` columns for query performance

### Code Files
- **Migration**: `db/migrations/0004_be010_admin_archived_field.sql`
- **Models**: `app/models.py` (added `archived` field)
- **Admin Routes**: `app/routes_admin.py` (new file)
- **Route Registration**: `app/routes.py` (imports admin routes)
- **Public Filters**: Updated `app/routes_resources.py` and `app/routes_companies.py` to filter `archived = FALSE`
