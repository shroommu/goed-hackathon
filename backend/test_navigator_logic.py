#!/usr/bin/env python3
"""
Unit test for BE-014 logic without database dependency.
Tests the deterministic fallback and response formatting.
"""

import sys

sys.path.insert(0, "/home/akrucken/dev/goed-hackathon/backend")

from app.routes_navigator import generate_deterministic_response, _resource_to_dict


class MockResource:
    """Mock Resource model for testing."""

    def __init__(
        self, id, title, description, topics, industries, communities, locations, link
    ):
        self.id = id
        self.title = title
        self.description = description
        self.topics = topics
        self.industries = industries
        self.communities = communities
        self.locations = locations
        self.link = link


def test_resource_to_dict():
    """Test resource conversion to dictionary."""
    print("\n=== Test 1: Resource to Dict Conversion ===")
    resource = MockResource(
        id=1,
        title="YCombinator",
        description="Startup accelerator",
        topics="funding, mentorship",
        industries="Technology",
        communities="San Francisco",
        locations="San Francisco, CA",
        link="https://www.ycombinator.com",
    )

    result = _resource_to_dict(resource)
    print(f"✅ Converted resource: {result['title']}")
    assert result["id"] == 1
    assert result["title"] == "YCombinator"
    assert result["url"] == "https://www.ycombinator.com"
    return True


def test_deterministic_response_with_candidates():
    """Test deterministic response generation with candidates."""
    print("\n=== Test 2: Deterministic Response with Candidates ===")

    candidates = [
        MockResource(
            id=1,
            title="Startup Grind",
            description="Global startup community",
            topics="networking, events",
            industries="Technology",
            communities="Entrepreneurs",
            locations="San Francisco",
            link="https://www.startupgrind.com",
        ),
        MockResource(
            id=2,
            title="TechStars",
            description="Startup accelerator",
            topics="funding, mentorship",
            industries="Technology, SaaS",
            communities="Founders",
            locations="Boulder, CO",
            link="https://www.techstars.com",
        ),
    ]

    context = {
        "industry": "Technology",
        "location": "San Francisco",
        "objectives": ["networking"],
    }

    response = generate_deterministic_response(context, candidates)

    print(f"Assistant message: {response['assistant_message']}")
    print(f"Number of recommendations: {len(response['recommendations'])}")

    assert "assistant_message" in response
    assert "derived_context" in response
    assert "recommendations" in response
    assert len(response["recommendations"]) == 2
    assert response["recommendations"][0]["id"] == 1
    assert response["recommendations"][0]["title"] == "Startup Grind"
    assert "rationale" in response["recommendations"][0]

    print(f"✅ Recommendation 1: {response['recommendations'][0]['title']}")
    print(f"   Rationale: {response['recommendations'][0]['rationale']}")

    return True


def test_deterministic_response_no_candidates():
    """Test deterministic response with no candidates."""
    print("\n=== Test 3: Deterministic Response with No Candidates ===")

    context = {"industry": "Unknown", "objectives": ["testing"]}

    response = generate_deterministic_response(context, [])

    print(f"Assistant message: {response['assistant_message']}")
    print(f"Number of recommendations: {len(response['recommendations'])}")

    assert "assistant_message" in response
    assert len(response["recommendations"]) == 0
    assert "couldn't find" in response["assistant_message"].lower()

    print("✅ Correctly handles no candidates")

    return True


def test_context_merging():
    """Test that context is properly maintained."""
    print("\n=== Test 4: Context Preservation ===")

    input_context = {
        "stage": "startup",
        "industry": "AI",
        "objectives": ["funding", "hiring"],
    }

    candidates = [
        MockResource(
            id=1,
            title="AI Accelerator",
            description="AI-focused program",
            topics="AI, ML, funding",
            industries="Artificial Intelligence",
            communities="AI Founders",
            locations="Remote",
            link="https://example.com",
        ),
    ]

    response = generate_deterministic_response(input_context, candidates)

    # Check that input context is preserved
    assert response["derived_context"] == input_context
    print("✅ Context preserved correctly")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("BE-014 Unit Tests (No Database Required)")
    print("=" * 60)

    tests = [
        ("Resource to Dict", test_resource_to_dict),
        (
            "Deterministic Response with Candidates",
            test_deterministic_response_with_candidates,
        ),
        (
            "Deterministic Response with No Candidates",
            test_deterministic_response_no_candidates,
        ),
        ("Context Preservation", test_context_merging),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, True))
        except AssertionError as e:
            print(f"❌ Assertion failed: {e}")
            results.append((name, False))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback

            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed! BE-014 logic is working correctly.")
        print("   (Database connectivity issue prevents end-to-end testing)")
