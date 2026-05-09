from __future__ import annotations

import json
import logging
from typing import Any

from flask import Blueprint, current_app, jsonify, request
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import or_

from .models import Resource

logger = logging.getLogger(__name__)


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


def search_resources(
    context: dict[str, Any], message: str, limit: int = 20
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

    # Build search conditions based on context
    search_conditions = []

    # Extract search terms from context
    if context.get("industry"):
        search_conditions.append(Resource.industries.ilike(f"%{context['industry']}%"))

    if context.get("location"):
        search_conditions.append(Resource.locations.ilike(f"%{context['location']}%"))

    if context.get("topics"):
        for topic in context["topics"]:
            search_conditions.append(Resource.topics.ilike(f"%{topic}%"))

    if context.get("objectives"):
        for objective in context["objectives"]:
            # Search across multiple fields for objectives
            search_conditions.append(
                or_(
                    Resource.topics.ilike(f"%{objective}%"),
                    Resource.title.ilike(f"%{objective}%"),
                    Resource.description.ilike(f"%{objective}%"),
                )
            )

    if context.get("challenges"):
        for challenge in context["challenges"]:
            search_conditions.append(
                or_(
                    Resource.topics.ilike(f"%{challenge}%"),
                    Resource.description.ilike(f"%{challenge}%"),
                )
            )

    # Extract keywords from message for broader search
    # Simple tokenization - in production might use more sophisticated NLP
    keywords = [
        word.strip().lower() for word in message.split() if len(word.strip()) > 3
    ]
    for keyword in keywords[
        :5
    ]:  # Limit to top 5 keywords to avoid overly broad queries
        search_conditions.append(
            or_(
                Resource.title.ilike(f"%{keyword}%"),
                Resource.description.ilike(f"%{keyword}%"),
                Resource.topics.ilike(f"%{keyword}%"),
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
        resources = query.limit(limit).all()
        logger.info(f"Query executed successfully, found {len(resources)} resources")
        return resources
    except Exception as e:
        logger.error(f"Database query failed: {type(e).__name__}: {str(e)}", exc_info=True)
        # Try a simpler query as fallback
        try:
            logger.info("Attempting fallback query")
            from .extensions import db
            simple_resources = db.session.query(Resource).filter_by(archived=False).limit(limit).all()
            logger.info(f"Fallback query succeeded with {len(simple_resources)} resources")
            return simple_resources
        except Exception as fallback_error:
            logger.error(f"Fallback query also failed: {fallback_error}", exc_info=True)
            raise


def get_llm_client() -> ChatOpenAI | None:
    """
    Initialize LangChain ChatOpenAI client configured for OpenRouter.

    Returns:
        ChatOpenAI client or None if API key not configured
    """
    api_key = current_app.config.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not configured")
        return None

    return ChatOpenAI(
        model=current_app.config.get(
            "OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct"
        ),
        openai_api_key=api_key,
        openai_api_base=current_app.config.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        timeout=current_app.config.get("LLM_TIMEOUT_SECONDS", 30),
        temperature=0.7,
    )


def create_system_prompt() -> str:
    """Create the system prompt for the LLM."""
    return """You are an expert entrepreneurship resource advisor helping entrepreneurs discover relevant programs, resources, and opportunities.

CRITICAL RULE: Only provide recommendations when you have sufficient context about the user's needs. If critical information is missing, ask clarifying questions instead.

Required context for good recommendations:
- At least 2 of these: stage, industry, location, objectives

Your task is to:
1. Extract context from the user's message (stage, industry, location, objectives, topics, challenges)
2. **IF CONTEXT IS INSUFFICIENT**: Ask a clarifying follow-up question and provide 0-2 general resources
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
  ],
  "follow_up_question": "Clarifying question when critical context is missing (REQUIRED if less than 2 recommendations)"
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
        Dictionary with assistant_message, derived_context, recommendations, and optional follow_up_question
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

        # Parse the response content
        content = response.content.strip()

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
        raw_content = response.content if "response" in locals() else "No response"
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
    for resource in candidates[:5]:
        # Generate simple template-based rationale
        rationale_parts = []
        if (
            context.get("industry")
            and resource.industries
            and context["industry"].lower() in resource.industries.lower()
        ):
            rationale_parts.append(f"Relevant to {context['industry']}")
        if (
            context.get("location")
            and resource.locations
            and context["location"].lower() in resource.locations.lower()
        ):
            rationale_parts.append(f"Available in {context['location']}")
        if context.get("topics"):
            for topic in context["topics"]:
                if resource.topics and topic.lower() in resource.topics.lower():
                    rationale_parts.append(f"Covers {topic}")
                    break

        rationale = (
            " • ".join(rationale_parts)
            if rationale_parts
            else "Matches your search criteria"
        )

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
            "recommendations": [...],
            "follow_up_question": "string (optional)"
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

            # Search for candidate resources
            try:
                candidates = search_resources(context, message)
                logger.info(f"Found {len(candidates)} candidates for message: {message}")
            except Exception as e:
                logger.error("Failed to search resources: %s", e, exc_info=True)
                # Return friendly response without database
                return (
                    jsonify(
                        {
                            "assistant_message": "I'm here to help you find entrepreneurship resources. Could you tell me more about what you're looking for?",
                            "derived_context": context,
                            "recommendations": [],
                            "follow_up_question": "What type of support are you looking for?",
                        }
                    ),
                    200,
                )

            # If no candidates found, return helpful message
            if not candidates:
                logger.warning(f"No candidates found for message '{message}' with context {context}")
                return (
                    jsonify(
                        {
                            "assistant_message": "I couldn't find specific resources matching your needs yet. Let me ask a few questions to help narrow it down. What stage is your business at?",
                            "derived_context": context,
                            "recommendations": [],
                            "follow_up_question": "What stage is your business at? (e.g., idea, pre-seed, startup, growth)",
                        }
                    ),
                    200,
                )
            
            logger.info(f"Processing {len(candidates)} candidates with LLM")

            # Try to use LLM
            llm_client = get_llm_client()
            use_llm = llm_client is not None
            
            if not use_llm:
                logger.warning("LLM client not configured, using deterministic fallback")

            if use_llm:
                try:
                    logger.info("Invoking LLM for response generation")
                    llm_response = generate_llm_response(
                        message, context, candidates, llm_client
                    )
                    logger.info("LLM response generated successfully")

                    # Enrich recommendations with full resource data
                    resource_map = {r.id: r for r in candidates}
                    enriched_recommendations = []

                    for rec in llm_response.get("recommendations", [])[:5]:
                        resource_id = rec.get("id")
                        if resource_id and resource_id in resource_map:
                            resource = resource_map[resource_id]
                            enriched_recommendations.append(
                                {
                                    "id": resource.id,
                                    "title": resource.title or "",
                                    "description": resource.description or "",
                                    "rationale": rec.get("rationale", ""),
                                    "url": resource.link or "",
                                    "topics": resource.topics or "",
                                    "industries": resource.industries or "",
                                    "communities": resource.communities or "",
                                }
                            )

                    response_data = {
                        "assistant_message": llm_response.get("assistant_message", ""),
                        "derived_context": llm_response.get("derived_context", context),
                        "recommendations": enriched_recommendations,
                    }

                    if llm_response.get("follow_up_question"):
                        response_data["follow_up_question"] = llm_response[
                            "follow_up_question"
                        ]

                    return jsonify(response_data), 200

                except Exception as e:
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
