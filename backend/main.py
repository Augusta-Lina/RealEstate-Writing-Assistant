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
EXAMPLE 1 (Grand Multi-Level Estate):
This remarkable property spans three levels and blends exceptional proportions with flawless symmetry, creating a residence that truly stands out. The design, thoughtfully conceived, integrates beautifully with its surrounding landscape, offering breath-taking views of the majestic mountains beyond.

The open-plan layout is central to the home's connection with nature, where large, concealed glass sliding doors and expansive windows seamlessly bring the outdoors in. Inside, minimalist luxury defines the space, with smooth screeded floors and elegant brass accents that give the interiors a sophisticated yet understated feel. Bespoke furnishings and carefully selected art pieces enhance the modern, contemporary atmosphere, all bathed in earthy tones of neutral greys and browns.

On the ground floor, the grand double-volume entrance sets the tone for the entire home, with its striking blend of water features and meticulously landscaped hedges. From this entrance, large glass sliding doors open to a covered terrace that overlooks a beautifully manicured formal garden, a heated rim-flow pool, and, of course, stunning mountain views.

The gourmet kitchen, designed with a central island, connects effortlessly to the informal lounge and a spacious dining area, celebrating the natural beauty that surrounds the home. This level also offers two additional lounges and a guest bedroom with an en suite bathroom, ensuring comfort and space for family and guests alike.

Upstairs, twin staircases with sleek glass railings lead to five magnificent en suite bedrooms, each offering its own sense of serenity and style. The master suite, with its expansive mountain vistas, includes a private balcony and an open-air shower.

The lower level features two en suite bedrooms that open directly to a plunge pool and a peaceful lily pond. Designed with ultimate luxury in mind, the lower level also boasts a spa room with a pedicure parlour, steam room, and Jacuzzi. For entertainment, there is a wine cellar, a poker room, and a cinema, while a central games room provides access to a high-tech gym and squash court.

This home is designed with security as a top priority, featuring a guardhouse at the entrance for added protection. Advanced perimeter cameras are strategically placed around the property, providing continuous surveillance and ensuring peace of mind with round-the-clock security.

Additional standout features include a roof terrace, a padel court, air conditioning throughout, smart control technology, and a dedicated scullery and laundry. The property also offers a two-bedroom staff quarters, a triple garage with additional parking for three more cars, and a system control room on the lower level. With solar panels, an inverter, and two boreholes, this home is designed with sustainability and convenience in mind.

EXAMPLE 2 (Entertainment-Focused Luxury Home):
As you enter this stunning home, you'll be greeted by an entertainment-focused level featuring an open-plan kitchen, dining area, and two lounge spaces. The entire area opens up to an outdoor oasis, complete with a sprawling L-shaped swimming pool and spectacular views, along with a braai area that includes a pizza oven and bar fridges — ideal for hosting guests.

On the upper level, you'll find four bedrooms, each equipped with its own en-suite bathroom. The expansive main bedroom offers a spacious walk-in closet and a hidden panic room for added security. This level also includes a cozy pyjama lounge, perfect for family movie nights.

The lower level is designed for leisure, featuring a wine cellar, cinema, and gym. A lift provides easy access to all floors, alongside four garage spaces and a security guard room at the entrance.

Practical amenities like staff accommodations, a large laundry room, backup generators, and a water supply system ensure ultimate comfort and peace of mind.

EXAMPLE 3 (Duplex Penthouse):
Imagine a luxurious duplex penthouse that will leave you breathless. This extraordinary residence is inspired by the elegance and sophistication of a yacht. As you step into this magnificent space, you'll be greeted by international finishes that exude style and glamour. Double volume ceilings, imported and custom made furniture, double glazed windows, retractable roof over pool, inverters and back up generators with solar - just to name a few luxury details.

The penthouse features five magnificent bedroom suites, each offering its own unique charm and comfort. The crown jewel of this opulent residence is the glamorous master bedroom, complete with a spacious walk-in dressing room.

But the true showstopper of this penthouse lies upstairs, where you'll find a pool and jacuzzi that will transport you to a state of pure relaxation. The pool area is accompanied by a second kitchen and bar area, with braai area, a sauna and a full bathroom for guests to change. Perfect for hosting unforgettable gatherings.

This home in the sky is filled with countless features that add to its allure, but they are too numerous to mention in just a few words. To truly appreciate the grandeur of this penthouse, it must be seen in person. Only then will you fully understand the splendor and magnificence that awaits within. Fully furnished. Unobstructed panoramic views.

EXAMPLE 4 (New Development / Off-Plan):
Introducing this exciting and exquisite new development yet to be built situated in sought after Clifton. A signature design by the world-renowned award-winning architects SAOTA, offering a magnificent Villa and Penthouse. Option to buy both or individually. With majestic views of the Twelve Apostles Mountain Range, Lions Head and all four Clifton's beaches, this Villa offers the discerning buyer a world-class experience of ultimate luxury and elegance.

The double storey 635 sqm garden Villa featuring open plan designs allowing natural light to flow in through big glass windows. Four luxurious bedrooms, all en suite. A magnificent chef's kitchen with top of the range German appliances and separate scullery. The spacious living areas, lounge, dining and TV lounge flow seamlessly onto an expansive outdoor terrace and large garden complete with sparkling pool and a water feature. An opulent undercover parking garage offering four bays for each of the Villa and Penthouse with direct elevator access. State of the art fully integrated security.

The second part of this development offers the spectacular Penthouse above, 3 bedrooms, 3 bathrooms with uninterrupted views and offers a lavish lifestyle. No expenses spared with ultra high-end finishes, finest materials such as glass and marble, and sparkling pool. Within walking distance to all four Clifton beaches as well as Camps Bay beaches and restaurants.

EXAMPLE 5 (Heritage Cottage Renovation):
The Annex Cottage at Greenways is a distinguished, standalone three-level residence within the esteemed Greenways Estate in Upper Claremont. Once part of the historic grounds of the iconic 1928 Manor House — originally inspired by Sir Herbert Baker and designed by Norman Lubynski.

Currently undergoing an exceptional renovation, the cottage is being reimagined with refined, neutral interiors enhanced by warm wood flooring, classic black-and-white checkerboard accents, and elegant black aluminium colonial-barred windows and stacker doors that elevate its timeless aesthetic.

The north-facing ground floor unfolds into a sophisticated open-plan living space encompassing the kitchen, dining area, and lounge. The kitchen will feature white Caesarstone countertops, a Smeg stove with gas hob and extractor, and a central island, while an adjoining scullery flows to a secluded courtyard. A double-sided wood-burning fireplace will softly delineate the dining and lounge areas, both opening through stacker doors to an undercover patio with built-in braai, a decked entertainment terrace, and a sparkling pool.

This level also hosts a guest bathroom and an indulgent guest suite complete with a walk-in dressing room, private lounge, full ensuite, and direct access to the patio.

Upstairs, a wood-finished landing leads to a magnificent master suite centred around a double-sided fireplace separating the bedroom from its private lounge. A walk-in dressing room, coffee station, and expansive full ensuite enhance the sense of luxury. Stacker doors open to an enclosed balcony, where additional stackers frame sweeping estate and mountain views.

A second en-suite bedroom with built-in cupboards and a serene pyjama lounge completes the upper level.

Positioned within a secure six-acre gated estate with 24-hour manned security, electric fencing, and comprehensive camera surveillance, the home offers both tranquillity and complete peace of mind.

EXAMPLE 6 (Character Family Home):
Located in a serene neighbourhood, this spacious three-level, five-bedroom family home exudes character and charm. Lovingly renovated, it seamlessly blends classic features with modern conveniences, offering a delightful living experience.

Upon entering, you are greeted by a vintage tiled entrance that sets the tone for the entire house. The main level features wooden floors, high pressed ceilings, sash windows, American shutters, and exposed brick accent walls, creating a warm and inviting atmosphere. The neutral colour scheme enhances the vintage appeal while maintaining a modern aesthetic.

The open plan lounge, dining room, and kitchen are bathed in natural light, thanks to its North-facing orientation. The lounge, featuring exposed brick walls and a cosy wood burner, opens onto an undercover patio overlooking a large garden dotted with mature trees and a swimming pool. Ideal for entertaining, the dining room extends outdoors via sliding doors to a paved side patio.

The fully fitted kitchen is a chef's delight, boasting a concrete ceiling with steel lighting tracks, a large centre island topped with gleaming white Caesarstone, and high-end appliances including a Smeg double oven, gas hob, and extractor. A sunroom nook adds charm, while a walk-in pantry, scullery, and laundry room provide ample storage and utility space.

The ground level also includes a study/work-from-home area with garden access, as well as a guest bathroom. Steps lead down to a self-contained flatlet complete with air conditioning, an open-plan lounge and kitchen with wooden floors, and an upstairs loft bedroom featuring exposed beams and an ensuite shower and bath — a perfect retreat for guests or extended family.

An ornate staircase leads to a mid-level walk-in linen room. Further upstairs, a large, light-filled pyjama lounge with wooden floors features a spacious rectangular window, a study nook, and a balcony. Three double bedrooms, each equipped with climate control, 2 of which share a full family bathroom. The Master suite is a sanctuary with a charming reading nook, a Victorian fireplace, and a walk-in closet. The ensuite bathroom is luxurious, boasting his and hers Caesarstone vanities, a freestanding bath, and a shower.

The loft level houses two additional bedrooms plus a large versatile loft space which could easily work as another bedroom — a perfect setup for growing families or hosting guests. Each of these bedrooms comes with climate control, and one of them enjoys its own ensuite shower.

This home is equipped with modern amenities including an inverter with 2 batteries for backup power, staff accommodation with a separate entrance, a kitchen, and ensuite shower. Security features include an entrance intercom with a camera system, alarm system, security gates, and electric fencing. A double remote garage offers secure parking, while a borehole with automated irrigation and a water filtration system ensures sustainable water use.

EXAMPLE 7 (Contemporary Renovated Home):
Perfectly blending character-filled charm with luxurious contemporary finishes. Set on an expansive 833m2 erf in a peaceful cul-de-sac, this spacious 4-bedroom, 4-bathroom residence offers effortless comfort, style, and versatility.

A breathtaking double-volume main suite crowns the upper level, featuring a wrap-around covered balcony with balau wood flooring and tranquil mountain and garden views. A walk-in dressing room and a stunning bespoke ensuite — with double vanity, bath, shower, and warm wood-look finishes — complete this private retreat.

Downstairs, three additional bedrooms each offer their own appeal: one with an ensuite and adjoining office, another with a cosy wood-burning fireplace, and a third with its own ensuite. A fourth modern bathroom with a shower serves guests.

The welcoming entrance flows into a family room with a fireplace and built-in shelving, leading to a beautifully renovated kitchen boasting black-and-white tiled floors, engineered marble-look countertops, a large stove with extractor, pantry, coffee station, and ample appliance space. Step down into the light-filled lounge and dining area with a closed-combustion fireplace, American shutters, and stack doors opening onto the lush, landscaped garden.

Designed for seamless indoor-outdoor living and entertaining, the garden features a patio, pool, koi pond, and a versatile studio currently used as a gym. Additional highlights include excellent security (CCTV, alarm, beams), double carport, air-conditioning in the lounge and three bedrooms, water tanks, well point, water feature, and an inverter for uninterrupted power.

Located within walking distance of Palmyra Junction, Cavendish, and transport links, and close to top Southern Suburbs schools, this exceptional home offers the perfect blend of luxury, convenience, and tranquillity.

EXAMPLE 8 (Apartment):
Located in the highly sought-after C Block of The Claremont, this generously sized apartment offers a perfect blend of comfort and convenience. Tucked away from the main road and the vibrant Claremont nightlife, it provides a peaceful retreat while remaining close to everything this bustling suburb has to offer.

Ideal for first-time buyers, parents of students, or investors, this property is a standout in its category.

Upon entry, you're welcomed by an open-plan, fully-equipped kitchen that seamlessly flows into the living and dining area. Sliding doors lead to a private balcony, offering beautiful views — views that are also enjoyed from the master bedroom.

The complex is just a short walk from key amenities, including Cavendish Square and the UCT Jammie Shuttle, making it a highly convenient location. Additionally, the 24-hour concierge security ensures peace of mind for all residents.

This is an opportunity not to be missed. Contact us today to arrange a viewing and secure your new home or investment.
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

    prompt = f"""You are an experienced luxury real estate agent writing a property listing description. Match the style and tone of the reference examples below exactly. Adapt your language and terminology to suit the property's location — use locally appropriate terms, currency references, and cultural context while maintaining the same sophisticated writing style.

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
