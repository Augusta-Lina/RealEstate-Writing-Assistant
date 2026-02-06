"""
Real Estate Listing Assistant API
=================================
Generates professional real estate listing descriptions using Claude AI.
Supports image analysis and neighborhood lookup.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import os
import base64
import json
from dotenv import load_dotenv
from typing import Optional, List

load_dotenv()

app = FastAPI(
    title="Real Estate Listing Assistant",
    description="AI-powered real estate listing description generator",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


REFERENCE_EXAMPLES = """
EXAMPLE 1 (Luxury Villa):
As you enter this stunning home, you'll be greeted by an entertainment-focused level featuring an open-plan kitchen, dining area, and two lounge spaces. The entire area opens up to an outdoor oasis, complete with a sprawling L-shaped swimming pool and spectacular views, along with a braai area that includes a pizza oven and bar fridges — ideal for hosting guests.

On the upper level, you'll find four bedrooms, each equipped with its own en-suite bathroom. The expansive main bedroom offers a spacious walk-in closet and a hidden panic room for added security. This level also includes a cozy pyjama lounge, perfect for family movie nights.

The lower level is designed for leisure, featuring a wine cellar, cinema, and gym. A lift provides easy access to all floors, alongside four garage spaces and a security guard room at the entrance.

Practical amenities like staff accommodations, a large laundry room, backup generators, and a water supply system ensure ultimate comfort and peace of mind.

EXAMPLE 2 (Heritage Family Home):
Located in a serene neighbourhood, this spacious three-level, five-bedroom family home exudes character and charm. Lovingly renovated, it seamlessly blends classic features with modern conveniences, offering a delightful living experience.

Upon entering, you are greeted by a vintage tiled entrance that sets the tone for the entire house. The main level features wooden floors, high pressed ceilings, sash windows, American shutters, and exposed brick accent walls, creating a warm and inviting atmosphere. The neutral colour scheme enhances the vintage appeal while maintaining a modern aesthetic.

The open plan lounge, dining room, and kitchen are bathed in natural light, thanks to its North-facing orientation. The lounge, featuring exposed brick walls and a cosy wood burner, opens onto an undercover patio overlooking a large garden dotted with mature trees and a swimming pool.

The fully fitted kitchen is a chef's delight, boasting a concrete ceiling with steel lighting tracks, a large centre island topped with gleaming white Caesarstone, and high-end appliances including a Smeg double oven, gas hob, and extractor.

EXAMPLE 3 (Apartment):
Located in the highly sought-after C Block of The Claremont, this generously sized apartment offers a perfect blend of comfort and convenience. Tucked away from the main road and the vibrant Claremont nightlife, it provides a peaceful retreat while remaining close to everything this bustling suburb has to offer.

Ideal for first-time buyers, parents of students, or investors, this property is a standout in its category.

Upon entry, you're welcomed by an open-plan, fully-equipped kitchen that seamlessly flows into the living and dining area. Sliding doors lead to a private balcony, offering beautiful views — views that are also enjoyed from the master bedroom.

The complex is just a short walk from key amenities, including Cavendish Square and the UCT Jammie Shuttle, making it a highly convenient location. Additionally, the 24-hour concierge security ensures peace of mind for all residents.
"""

import re

def clean_listing_output(text: str) -> str:
    """Remove any bold markdown, headlines, or price mentions the AI may have added."""
    # Remove markdown bold markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # Remove lines that look like standalone headlines (short lines ending with no period at the start)
    lines = text.strip().split('\n')
    # If the first non-empty line looks like a headline (short, no period, often title-cased), remove it
    while lines:
        first = lines[0].strip()
        if not first:
            lines.pop(0)
            continue
        # Headline heuristics: short line (under 100 chars), no period at end, or wrapped in quotes
        is_headline = (
            len(first) < 120
            and not first.endswith('.')
            and not first.endswith(',')
            and '\n' not in first
            and first.count(' ') < 20
        )
        if is_headline:
            lines.pop(0)
            # Also remove any blank line after the headline
            while lines and not lines[0].strip():
                lines.pop(0)
        else:
            break
    return '\n'.join(lines).strip()


PROPERTY_TYPE_NAMES = {
    "house": "home",
    "condo": "condo",
    "townhouse": "townhouse",
    "land": "property"
}


def build_property_context(
    property_type: str,
    listing_purpose: str,
    bedrooms: str,
    bathrooms: str,
    sqft: str,
    price: str,
    address: str,
    features: List[str],
    additional_notes: str
) -> str:
    """Build a context string from property details."""
    parts = []

    prop_name = PROPERTY_TYPE_NAMES.get(property_type, "property")
    purpose = "for sale" if listing_purpose == "sale" else "for rent"
    parts.append(f"Property Type: {prop_name.title()} {purpose}")

    if bedrooms:
        parts.append(f"Bedrooms: {bedrooms}")
    if bathrooms:
        parts.append(f"Bathrooms: {bathrooms}")
    if sqft:
        parts.append(f"Square Footage: {sqft} sqft")
    if price:
        price_formatted = f"${int(price):,}" if price.isdigit() else f"${price}"
        if listing_purpose == "rent":
            parts.append(f"Monthly Rent: {price_formatted}")
        else:
            parts.append(f"Price: {price_formatted}")
    if address:
        parts.append(f"Location: {address}")
    if features:
        parts.append(f"Features: {', '.join(features)}")
    if additional_notes:
        parts.append(f"Additional Notes: {additional_notes}")

    return "\n".join(parts)


async def analyze_images(images: List[UploadFile]) -> str:
    """Analyze property images using Claude Vision."""
    if not images:
        return ""

    client = get_client()
    image_contents = []

    for img in images:
        content = await img.read()
        await img.seek(0)

        # Determine media type
        content_type = img.content_type or "image/jpeg"
        if content_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
            content_type = "image/jpeg"

        base64_image = base64.standard_b64encode(content).decode("utf-8")
        image_contents.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": content_type,
                "data": base64_image
            }
        })

    image_contents.append({
        "type": "text",
        "text": """Analyze these real estate property images. For each notable observation, describe:
- Architectural style and condition
- Interior finishes and design elements
- Natural light and ambiance
- Notable visual features (views, unique elements)
- Outdoor spaces if visible
- Overall vibe/feeling

Be specific but concise. Only describe what you can actually see. Format as a brief paragraph."""
    })

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": image_contents}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Image analysis error: {e}")
        return ""


async def lookup_neighborhood(address: str) -> str:
    """Perform web search for neighborhood information."""
    if not address or len(address.strip()) < 3:
        return ""

    client = get_client()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": f"""Based on your knowledge, provide a brief 2-3 sentence description of the neighborhood/area: {address}

Include relevant details about:
- Nearby amenities (restaurants, shopping, parks)
- Schools if it's a residential area
- General character and vibe of the neighborhood
- Transit or accessibility

Keep it factual and useful for a real estate listing. If you're not confident about specific details for this location, provide general information about the type of area it appears to be."""
            }]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Neighborhood lookup error: {e}")
        return ""


def build_listing_prompt(
    property_context: str,
    image_analysis: str,
    neighborhood_info: str,
    listing_purpose: str
) -> str:
    """Build the prompt for generating the listing description."""

    prompt = f"""You are an experienced South African luxury real estate agent writing a property listing description. Match the style and tone of the reference examples below exactly.

REFERENCE EXAMPLES (match this writing style):
{REFERENCE_EXAMPLES}

CRITICAL RULES (you must follow these exactly):
- NEVER include a headline, title, or bold text. Start the first sentence directly with the property description.
- NEVER mention the price or any monetary amount anywhere in the description.
- NEVER use emoji.
- NEVER use bullet points or numbered lists.
- NEVER use markdown formatting (no **, no ##, no *).

STYLE RULES:
- Write in a sophisticated, descriptive narrative style as shown in the examples
- Walk through the property logically: entrance → main living areas → kitchen → bedrooms → outdoor/entertainment → practical amenities
- Weave features into flowing prose paragraphs
- Use elegant, aspirational language: "magnificent", "bespoke", "seamlessly flows", "exudes character"
- Scale the description length to match the property — longer for large luxury homes, shorter for apartments
- Reference specific finishes, materials, and design elements where provided
- End with practical amenities (security, parking, power backup) or a brief call to action
- {"Focus on rental appeal and lifestyle convenience" if listing_purpose == "rent" else "Focus on ownership appeal and investment value"}
- Never invent features not mentioned in the property details

PROPERTY DETAILS:
{property_context}

"""

    if image_analysis:
        prompt += f"""VISUAL DETAILS FROM PHOTOS:
{image_analysis}

"""

    if neighborhood_info:
        prompt += f"""NEIGHBORHOOD CONTEXT:
{neighborhood_info}

"""

    prompt += """Now write the listing description for this property, matching the reference style exactly. Remember: NO headline, NO bold text, NO price, NO emoji, NO markdown. Start directly with the first descriptive sentence."""

    return prompt


def build_social_prompt(
    property_context: str,
    image_analysis: str,
    listing_purpose: str
) -> str:
    """Build the prompt for generating the social media caption."""

    prompt = f"""You are a luxury real estate agent creating an Instagram/social media post for a property listing.

PROPERTY DETAILS:
{property_context}

"""

    if image_analysis:
        prompt += f"""VISUAL DETAILS FROM PHOTOS:
{image_analysis}

"""

    prompt += f"""INSTRUCTIONS:
1. Write a social media caption (50-80 words)
2. Use a sophisticated yet approachable tone — match the elegance of a luxury property brand
3. Highlight the most compelling 2-3 features
4. End with 3-5 relevant hashtags
5. {"Use rental-focused language" if listing_purpose == "rent" else "Use buyer-focused language"}
6. Keep emoji minimal — 1-2 max if any
7. Do NOT mention the price

Write only the caption with hashtags, no extra formatting."""

    return prompt


@app.get("/")
async def root():
    return {
        "message": "Real Estate Listing Assistant API",
        "docs": "/docs",
        "endpoints": {
            "/generate-listing": "POST - Generate full listing + social caption",
            "/regenerate-section": "POST - Regenerate a specific section"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/generate-listing")
async def generate_listing(
    property_type: str = Form(...),
    listing_purpose: str = Form("sale"),
    bedrooms: str = Form(""),
    bathrooms: str = Form(""),
    sqft: str = Form(""),
    price: str = Form(""),
    address: str = Form(""),
    features: str = Form("[]"),
    additional_notes: str = Form(""),
    images: List[UploadFile] = File(default=[])
):
    """Generate a complete listing with description and social caption."""
    try:
        # Parse features JSON
        try:
            features_list = json.loads(features)
        except json.JSONDecodeError:
            features_list = []

        # Build property context
        property_context = build_property_context(
            property_type, listing_purpose, bedrooms, bathrooms,
            sqft, price, address, features_list, additional_notes
        )

        # Analyze images if provided
        image_analysis = ""
        if images and len(images) > 0 and images[0].filename:
            image_analysis = await analyze_images(images)

        # Lookup neighborhood if address provided
        neighborhood_info = ""
        if address:
            neighborhood_info = await lookup_neighborhood(address)

        # Generate listing description
        client = get_client()

        listing_prompt = build_listing_prompt(
            property_context, image_analysis, neighborhood_info, listing_purpose
        )

        description_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": listing_prompt}]
        )
        description = clean_listing_output(description_response.content[0].text)

        # Generate social caption
        social_prompt = build_social_prompt(
            property_context, image_analysis, listing_purpose
        )

        social_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": social_prompt}]
        )
        social_caption = social_response.content[0].text

        return {
            "description": description,
            "social_caption": social_caption
        }

    except anthropic.APIError as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating listing: {str(e)}")


@app.post("/regenerate-section")
async def regenerate_section(
    section: str = Form(...),
    property_type: str = Form(...),
    listing_purpose: str = Form("sale"),
    bedrooms: str = Form(""),
    bathrooms: str = Form(""),
    sqft: str = Form(""),
    price: str = Form(""),
    address: str = Form(""),
    features: str = Form("[]"),
    additional_notes: str = Form(""),
    images: List[UploadFile] = File(default=[])
):
    """Regenerate a specific section (description or social)."""
    try:
        # Parse features JSON
        try:
            features_list = json.loads(features)
        except json.JSONDecodeError:
            features_list = []

        # Build property context
        property_context = build_property_context(
            property_type, listing_purpose, bedrooms, bathrooms,
            sqft, price, address, features_list, additional_notes
        )

        # Analyze images if provided
        image_analysis = ""
        if images and len(images) > 0 and images[0].filename:
            image_analysis = await analyze_images(images)

        client = get_client()

        if section == "description":
            # Lookup neighborhood for description
            neighborhood_info = ""
            if address:
                neighborhood_info = await lookup_neighborhood(address)

            prompt = build_listing_prompt(
                property_context, image_analysis, neighborhood_info, listing_purpose
            )
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
        else:
            prompt = build_social_prompt(
                property_context, image_analysis, listing_purpose
            )
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

        content = response.content[0].text
        if section == "description":
            content = clean_listing_output(content)
        return {"content": content}

    except anthropic.APIError as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
