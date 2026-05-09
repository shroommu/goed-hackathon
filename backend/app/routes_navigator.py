from __future__ import annotations

import json
import logging
import time
from typing import Any

from flask import Blueprint, current_app, jsonify, request
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import or_

from .models import Resource

logger = logging.getLogger(__name__)


def _normalize_llm_message_content(content: Any) -> str:
    """LangChain/OpenRouter may return str or a list of content blocks; normalize to text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    parts.append(block["text"])
                elif isinstance(block.get("text"), str):
                    parts.append(block["text"])
        return "".join(parts)
    return str(content)


BE016_CANDIDATE_LIMIT = 20
BE016_MAX_RECOMMENDATIONS = 5
BE016_FALLBACK_RATIONALE = (
    "Selected via deterministic fallback ranking based on your provided context."
)

LIGHT_EXPANSION_MAP: dict[str, list[str]] = {
    "funding": ["grant", "capital", "investor", "loan"],
    "hiring": ["talent", "recruit", "workforce"],
    "mentorship": ["mentor", "advisor", "coaching"],
    "networking": ["community", "events", "connections"],
    "training": ["workshop", "education", "course"],
    "software": ["saas", "technology", "it"],
    "artificial intelligence": ["ai", "machine learning", "ml"],
    "startup": ["founder", "entrepreneur", "early stage"],
}


def _error_response(status: int, code: str, message: str, details: dict | None = None):
    """Consistent error response format matching BE-006 pattern."""
    payload = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        payload["error"]["details"] = details
    return jsonify(payload), status


def _resource_to_dict(resource: Resource) -> dict[str, Any]:
    """Convert Resource model to dictionary for recommendations."""
    return {
        "id": resource.id,
        "title": resource.title or "",
        "description": resource.description or "",
        "topics": resource.topics or "",
        "industries": resource.industries or "",
        "communities": resource.communities or "",
        "locations": resource.locations or "",
        "url": resource.link or "",
    }


def _normalize_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        values = value
    else:
        values = [value]
    cleaned = []
    for item in values:
        if item is None:
            continue
        text = str(item).strip().lower()
        if text:
            cleaned.append(text)
    return cleaned


def _collect_search_terms(context: dict[str, Any], message: str) -> list[str]:
    """Collect deterministic retrieval terms with light synonym/tag expansion."""
    terms: set[str] = set()

    for field in ["stage", "industry", "location"]:
        value = context.get(field)
        if isinstance(value, str) and value.strip():
            terms.add(value.strip().lower())

    for field in ["objectives", "topics", "challenges"]:
        for value in _normalize_text_list(context.get(field)):
            terms.add(value)

    message_keywords = [word.strip(".,!?;:()[]{}\"'").lower() for word in message.split()]
    for keyword in message_keywords:
        if len(keyword) >= 4:
            terms.add(keyword)

    # Apply light expansion for known common intents/tags.
    expanded_terms = set(terms)
    for term in terms:
        if term in LIGHT_EXPANSION_MAP:
            expanded_terms.update(LIGHT_EXPANSION_MAP[term])

    return sorted(expanded_terms)[:12]


def _is_validation_debug_enabled() -> bool:
    header_enabled = request.headers.get("X-Admin-Debug", "").lower() in {
        "1",
        "true",
        "yes",
    }
    query_enabled = request.args.get("debug", "").lower() in {"1", "true", "yes"}
    return header_enabled or (current_app.config.get("DEBUG") and query_enabled)


def _validate_and_enrich_recommendations(
    llm_recommendations: list[dict[str, Any]],
    candidates: list[Resource],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Drop hallucinated/invalid recs and enrich valid recs with source-of-truth data."""
    resource_map = {resource.id: resource for resource in candidates}
    enriched: list[dict[str, Any]] = []
    validation_fail_reasons: list[str] = []

    for rec in llm_recommendations[:BE016_MAX_RECOMMENDATIONS]:
        resource_id = rec.get("id")
        if resource_id not in resource_map:
            validation_fail_reasons.append(f"unknown_resource_id:{resource_id}")
            continue

        resource = resource_map[resource_id]

        # Enforce exact URL match when the LLM attempts to provide a URL.
        llm_url = rec.get("url")
        official_url = resource.link or ""
        if llm_url is not None and str(llm_url) != official_url:
            validation_fail_reasons.append(f"url_mismatch_for_resource_id:{resource_id}")
            continue

        enriched.append(
            {
                "id": resource.id,
                "title": resource.title or "",
                "description": resource.description or "",
                "rationale": rec.get("rationale", ""),
                "url": official_url,
                "topics": resource.topics or "",
                "industries": resource.industries or "",
                "communities": resource.communities or "",
                "locations": resource.locations or "",
            }
        )

    return enriched, validation_fail_reasons


def search_resources(
    context: dict[str, Any], message: str, limit: int = BE016_CANDIDATE_LIMIT
) -> list[Resource]:
    """
    Full-text search across Resource fields using context and message keywords.

    Args:
        context: Extracted user context (stage, industry, location, objectives, topics, challenges)
        message: User's current message
        limit: Maximum number of candidates to return

    Returns:
        List of Resource records matching search criteria
    """
    query = Resource.query.filter_by(archived=False)

    # Build deterministic retrieval conditions with light synonym/tag expansion.
    search_conditions = []
    for term in _collect_search_terms(context, message):
        search_conditions.append(
            or_(
                Resource.title.ilike(f"%{term}%"),
                Resource.description.ilike(f"%{term}%"),
                Resource.topics.ilike(f"%{term}%"),
                Resource.industries.ilike(f"%{term}%"),
                Resource.communities.ilike(f"%{term}%"),
                Resource.locations.ilike(f"%{term}%"),
            )
        )

    # Apply search conditions
    if search_conditions:
        query = query.filter(or_(*search_conditions))
    else:
        # If no search conditions, return random sampling of resources
        # This prevents returning ALL resources
        logger.info("No search conditions, will return general resources")

    # Execute query with limit
    try:
        resources = query.order_by(Resource.id.asc()).limit(limit).all()
        logger.info("Query executed successfully, found %s resources", len(resources))
        return resources
    except Exception as e:
        logger.error(
            "Database query failed: %s: %s", type(e).__name__, str(e), exc_info=True
        )
        # Try a simpler query as fallback
        try:
            logger.info("Attempting fallback query")
            from .extensions import db
            simple_resources = (
                db.session.query(Resource)
                .filter_by(archived=False)
                .order_by(Resource.id.asc())
                .limit(limit)
                .all()
            )
            logger.info(
                "Fallback query succeeded with %s resources", len(simple_resources)
            )
            return simple_resources
        except Exception as fallback_error:
            logger.error("Fallback query also failed: %s", fallback_error, exc_info=True)
            raise


def get_llm_client(timeout_seconds: float | None = None) -> ChatOpenAI | None:
    """
    Initialize LangChain ChatOpenAI client configured for OpenRouter.

    Returns:
        ChatOpenAI client or None if API key not configured
    """
    api_key = current_app.config.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not configured")
        return None

    configured_timeout = current_app.config.get("LLM_TIMEOUT_SECONDS", 30)
    client_timeout = timeout_seconds if timeout_seconds is not None else configured_timeout

    referer = current_app.config.get("OPENROUTER_HTTP_REFERER") or ""
    title = current_app.config.get("OPENROUTER_APP_TITLE", "GoED Navigator")
    default_headers: dict[str, str] = {
        # OpenRouter expects these for attribution; some providers misbehave if omitted.
        "HTTP-Referer": referer,
        "X-Title": title,
    }

    return ChatOpenAI(
        model=current_app.config.get(
            "OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct"
        ),
        openai_api_key=api_key,
        openai_api_base=current_app.config.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        timeout=client_timeout,
        temperature=0.7,
        default_headers=default_headers,
    )


def create_system_prompt() -> str:
    """Create the system prompt for the LLM."""
    return """You are an expert entrepreneurship resource advisor helping entrepreneurs discover relevant programs, resources, and opportunities.

CRITICAL RULE: Only provide recommendations when you have sufficient context about the user's needs. If critical information is missing, ask clarifying questions instead.

Required context for good recommendations:
- At least 2 of these: stage, industry, location, objectives

Your task is to:
1. Extract context from the user's message (stage, industry, location, objectives, topics, challenges)
2. **IF CONTEXT IS INSUFFICIENT**: Ask clarifying questions in assistant_message and provide 0-2 general resources
3. **IF CONTEXT IS SUFFICIENT**: Select the top 5 most relevant resources from the provided candidate list
4. Generate personalized rationales explaining why each resource matches the user's needs
5. Respond naturally and conversationally

CRITICAL CONSTRAINTS:
- You MUST ONLY recommend resources from the provided candidate list
- You MUST include the exact resource ID from the candidate list
- Do NOT fabricate or hallucinate resources
- If the user's query is too vague, prioritize asking questions over making recommendations

Context fields to extract/update:
- stage: Business maturity (idea, pre-seed, startup, growth, established, late-stage)
- industry: Primary sector/vertical (be specific: "Software and IT", "Healthcare", "Manufacturing", etc.)
- location: Geographic focus (city, county, state - be specific like "Salt Lake", "Utah County", "Davis County")
- objectives: Goals (funding, hiring, mentorship, product-market fit, networking, training, etc.)
- topics: Specific interests (AI/ML, sustainability, SaaS, hardware, women-owned, student, etc.)
- challenges: Current blockers or pain points

Output your response as JSON with this structure:
{{
  "assistant_message": "Natural language response to user",
  "derived_context": {{
    "stage": "extracted or updated stage",
    "industry": "extracted or updated industry",
    "location": "extracted or updated location",
    "objectives": ["list of objectives"],
    "topics": ["list of topics"],
    "challenges": ["list of challenges"]
  }},
  "recommendations": [
    {{
      "id": 123,
      "rationale": "Personalized explanation of why this resource matches"
    }}
  ]
}}

EXAMPLES:

Insufficient Context:
User: "I need help with funding"
Response: Ask about stage, industry, and location. Provide 0-2 very general resources.

Sufficient Context:
User: "I need funding for my early-stage software startup in Salt Lake City"
Context: stage=startup, industry=Software, location=Salt Lake, objectives=[funding]
Response: Provide 5 tailored recommendations with specific rationales.

Only include fields in derived_context that you've extracted or want to update. Exclude fields with no information.
Recommendations should be ordered by relevance (best match first).
"""


def generate_llm_response(
    message: str,
    context: dict[str, Any],
    candidates: list[Resource],
    llm_client: ChatOpenAI,
) -> dict[str, Any]:
    """
    Use LLM to generate response with context extraction and recommendations.

    Args:
        message: User's message
        context: Current conversation context
        candidates: List of candidate resources to choose from
        llm_client: LangChain ChatOpenAI client

    Returns:
        Dictionary with assistant_message, derived_context, and recommendations
    """
    # Format candidates for the prompt
    candidate_list = []
    for resource in candidates:
        candidate_list.append(
            {
                "id": resource.id,
                "title": resource.title or "",
                "description": resource.description or "",
                "topics": resource.topics or "",
                "industries": resource.industries or "",
                "communities": resource.communities or "",
                "locations": resource.locations or "",
            }
        )

    # Build the prompt
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", create_system_prompt()),
            (
                "user",
                """User's message: {message}

Current context: {context}

Candidate resources to choose from (select top 5):
{candidates}

Remember: Only recommend resources from this candidate list. Include the exact resource ID in your recommendations.""",
            ),
        ]
    )

    # Create the chain
    chain = prompt_template | llm_client

    # Invoke the LLM
    try:
        response = chain.invoke(
            {
                "message": message,
                "context": json.dumps(context, indent=2),
                "candidates": json.dumps(candidate_list, indent=2),
            }
        )

        # Parse the response content (may be str or multimodal list from OpenRouter)
        content = _normalize_llm_message_content(response.content).strip()

        # Try to extract JSON from the response
        # LLMs sometimes wrap JSON in markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed_response = json.loads(content)

        # Validate required fields
        if not isinstance(parsed_response, dict):
            raise ValueError("LLM response must be a JSON object")
        if "assistant_message" not in parsed_response:
            parsed_response["assistant_message"] = (
                "Here are some resources that might help you:"
            )
        if "derived_context" not in parsed_response:
            parsed_response["derived_context"] = context
        if "recommendations" not in parsed_response:
            parsed_response["recommendations"] = []

        return parsed_response

    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM JSON response: %s", e)
        raw_content = (
            _normalize_llm_message_content(response.content)
            if "response" in locals()
            else "No response"
        )
        logger.error("Raw response: %s", raw_content)
        raise
    except Exception as e:
        logger.error("LLM invocation failed: %s", e)
        raise


def generate_deterministic_response(
    context: dict[str, Any],
    candidates: list[Resource],
) -> dict[str, Any]:
    """
    Fallback: Generate deterministic response without LLM.

    Returns top 5 candidates with template-based rationales.
    """
    recommendations = []
    for resource in candidates[:BE016_MAX_RECOMMENDATIONS]:
        rationale = BE016_FALLBACK_RATIONALE

        recommendations.append(
            {
                "id": resource.id,
                "title": resource.title or "",
                "description": resource.description or "",
                "rationale": rationale,
                "url": resource.link or "",
                "topics": resource.topics or "",
                "industries": resource.industries or "",
                "communities": resource.communities or "",
                "locations": resource.locations or "",
            }
        )

    # Generate simple assistant message
    assistant_message = "Here are some resources that might be helpful for you:"
    if not candidates:
        assistant_message = "I couldn't find specific resources matching your needs yet. Could you tell me more about what you're looking for?"

    return {
        "assistant_message": assistant_message,
        "derived_context": context,  # No extraction without LLM
        "recommendations": recommendations,
    }


def register_navigator_routes(blueprint: Blueprint) -> None:
    """Register navigator/chat routes to the API blueprint."""

    @blueprint.post("/navigator/chat/message")
    def chat_message():
        """
        POST /api/navigator/chat/message

        Conversational resource discovery endpoint.

        Request body:
        {
            "message": "string (required)",
            "context": {
                "stage": "string",
                "industry": "string",
                "location": "string",
                "objectives": ["string"],
                "topics": ["string"],
                "challenges": ["string"]
            }
        }

        Returns:
        {
            "assistant_message": "string",
            "derived_context": {...},
            "recommendations": [...]
        }
        """
        try:
            data = request.get_json()

            # Validate request
            if not data:
                return _error_response(
                    400,
                    "invalid_request",
                    "Request body must be JSON",
                )

            message = data.get("message")
            if not message or not isinstance(message, str) or not message.strip():
                return _error_response(
                    400,
                    "invalid_request",
                    "Field 'message' is required and must be a non-empty string",
                    {"field": "message"},
                )

            # Extract context (optional)
            context = data.get("context", {})
            if not isinstance(context, dict):
                return _error_response(
                    400,
                    "invalid_request",
                    "Field 'context' must be an object",
                    {"field": "context"},
                )

            # Normalize context arrays
            for field in ["objectives", "topics", "challenges"]:
                if field in context and not isinstance(context[field], list):
                    context[field] = [context[field]]

            # Do not block here: structured context may be empty on early turns while the user's
            # message still contains stage/industry/etc. The LLM extracts derived_context; skipping
            # this step prevented any extraction and forced the canned "more context" reply forever.

            # Search for candidate resources
            try:
                candidates = search_resources(context, message)
                logger.info("Found %s candidates for message: %s", len(candidates), message)
            except Exception as e:
                logger.error("Failed to search resources: %s", e, exc_info=True)
                # Return friendly response without database
                return (
                    jsonify(
                        {
                            "assistant_message": "I'm here to help you find entrepreneurship resources. Could you tell me more about what you're looking for?",
                            "derived_context": context,
                            "recommendations": [],
                        }
                    ),
                    200,
                )

            # If no candidates found, return helpful message
            if not candidates:
                logger.warning(
                    "No candidates found for message '%s' with context %s", message, context
                )
                return (
                    jsonify(
                        {
                            "assistant_message": "I couldn't find specific resources matching your needs yet. Let me ask a few questions to help narrow it down. What stage is your business at? (e.g., idea, pre-seed, startup, growth)",
                            "derived_context": context,
                            "recommendations": [],
                        }
                    ),
                    200,
                )
            
            logger.info("Processing %s candidates with LLM", len(candidates))

            telemetry = {
                "candidate_count": len(candidates),
                "blocked_count": 0,
                "llm_timeout": False,
                "fallback_used": False,
                "validation_fail_reasons": [],
            }

            llm_started_at = time.monotonic()
            # Use LLM_TIMEOUT_SECONDS from env (see config.py); prod needs headroom vs. dev latency.
            llm_budget_seconds = float(current_app.config.get("LLM_TIMEOUT_SECONDS", 30))

            # Try to use LLM
            llm_client = get_llm_client(timeout_seconds=llm_budget_seconds)
            use_llm = llm_client is not None
            
            if not use_llm:
                logger.warning("LLM client not configured, using deterministic fallback")

            if use_llm:
                try:
                    logger.info("Invoking LLM for response generation")
                    llm_response = generate_llm_response(
                        message, context, candidates, llm_client
                    )

                    elapsed = time.monotonic() - llm_started_at
                    if elapsed > llm_budget_seconds:
                        telemetry["llm_timeout"] = True
                        raise TimeoutError("LLM+validation exceeded timeout budget")

                    logger.info("LLM response generated successfully")

                    enriched_recommendations, validation_fail_reasons = (
                        _validate_and_enrich_recommendations(
                            llm_response.get("recommendations", []), candidates
                        )
                    )
                    telemetry["validation_fail_reasons"] = validation_fail_reasons
                    telemetry["blocked_count"] = len(validation_fail_reasons)

                    response_data = {
                        "assistant_message": llm_response.get("assistant_message", ""),
                        "derived_context": llm_response.get("derived_context", context),
                        "recommendations": enriched_recommendations,
                    }

                    if _is_validation_debug_enabled():
                        response_data["validation_debug"] = {
                            "blocked_count": telemetry["blocked_count"],
                            "validation_fail_reasons": telemetry[
                                "validation_fail_reasons"
                            ],
                        }

                    logger.info("navigator_be016 telemetry=%s", json.dumps(telemetry))

                    return jsonify(response_data), 200

                except Exception as e:
                    if isinstance(e, TimeoutError):
                        telemetry["llm_timeout"] = True
                    telemetry["fallback_used"] = True
                    logger.info("navigator_be016 telemetry=%s", json.dumps(telemetry))
                    logger.error(
                        "LLM generation failed, falling back to deterministic: %s", e, exc_info=True
                    )
                    use_llm = False

            # Fallback to deterministic response
            if not use_llm:
                try:
                    deterministic_response = generate_deterministic_response(
                        context, candidates
                    )
                    telemetry["fallback_used"] = True
                    logger.info("navigator_be016 telemetry=%s", json.dumps(telemetry))
                    return jsonify(deterministic_response), 200
                except Exception as e:
                    logger.error("Deterministic fallback failed: %s", e, exc_info=True)
                    # Ultimate fallback - return minimal response
                    return (
                        jsonify(
                            {
                                "assistant_message": "I found some resources that might be helpful. Let me know if you'd like more specific recommendations!",
                                "derived_context": context,
                                "recommendations": [],
                            }
                        ),
                        200,
                    )

        except Exception as e:
            logger.exception("Unexpected error in chat_message endpoint: %s", e)
            # Include error type in response for debugging
            error_msg = "An unexpected error occurred"
            if current_app.config.get("DEBUG"):
                error_msg = f"{error_msg}: {type(e).__name__}: {str(e)}"
            return _error_response(
                500,
                "internal_error",
                error_msg,
            )
