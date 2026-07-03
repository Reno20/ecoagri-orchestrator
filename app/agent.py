# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
EcoAgri-Orchestrator — ADK 2.0 Workflow Graph
=============================================

A multi-agent system for the Sasthamcotta Lake eco-agri nexus in Kerala.

Graph topology:
  START → triage_router → security_checkpoint
    ├─ "clean_ecological" → geo_spatial_analyst → eco_agronomist → consent_gate → market_broker → final_response
    ├─ "clean_market"     → market_broker → final_response
    ├─ "clean_general"    → final_response
    └─ "SECURITY_EVENT"   → final_response (blocked)
"""

import json
import logging
import re
from datetime import datetime, timezone
import os
import sys
from pathlib import Path
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.workflow import Workflow, node
from google.genai import types
from pydantic import BaseModel, Field

from .config import config

logger = logging.getLogger(__name__)

# Resolve path to the MCP server script
_MCP_SERVER_PATH = str(Path(__file__).parent / "mcp_server.py")
_PYTHON_PATH = sys.executable

# ═══════════════════════════════════════════════════════════════════════════════
# MCP TOOLSETS (stdio transport to local mcp_server.py)
# ═══════════════════════════════════════════════════════════════════════════════

# Geo-spatial tools: water quality, watershed zones, crop sustainability, erosion
mcp_geo_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=_PYTHON_PATH,
            args=[_MCP_SERVER_PATH],
        ),
    ),
    tool_filter=["query_water_quality", "lookup_watershed_zone", "get_crop_sustainability", "get_soil_erosion_data"],
)

# Market tools: commodity pricing
mcp_market_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=_PYTHON_PATH,
            args=[_MCP_SERVER_PATH],
        ),
    ),
    tool_filter=["get_market_prices"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class TriageResult(BaseModel):
    """Output from the triage router classifying the user query."""
    category: str = Field(description="One of: ecological, market, general")
    query_summary: str = Field(description="Brief summary of user intent")
    farmer_location: str = Field(default="", description="Extracted location if mentioned")
    crop_type: str = Field(default="", description="Extracted crop type if mentioned")


class GeoSpatialOutput(BaseModel):
    """Output from the Geo-Spatial Analyst."""
    location_assessment: str = Field(description="Assessment of the farmer's location relative to Sasthamcotta watershed")
    water_quality_risk: str = Field(description="LOW, MODERATE, or HIGH risk to water quality")
    watershed_zone: str = Field(description="The watershed zone: buffer, transition, or outer")
    erosion_risk: str = Field(description="Erosion risk level based on soil and terrain")
    recommendations: list[str] = Field(default_factory=list, description="Geo-spatial specific recommendations")


class AgronomyAdvice(BaseModel):
    """Output from the Eco-Agronomist."""
    current_practice_assessment: str = Field(description="Assessment of current farming practices")
    sustainable_alternatives: list[str] = Field(description="List of sustainable crop/practice alternatives")
    runoff_mitigation: str = Field(description="Specific runoff mitigation strategies")
    expected_impact: str = Field(description="Expected ecological impact of adopting recommendations")
    compliance_score: float = Field(description="Score 0-100 indicating ecological compliance")


class MarketLinkage(BaseModel):
    """Output from the Market Broker."""
    eligible: bool = Field(description="Whether the farmer qualifies for direct market access")
    buyer_matches: list[str] = Field(description="List of potential wholesale buyers in Kollam")
    price_guidance: str = Field(description="Current market price guidance for the crop")
    logistics_note: str = Field(description="Logistics and transport recommendations")
    certification_needed: list[str] = Field(default_factory=list, description="Any certifications needed")


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 1: TRIAGE ROUTER (deterministic function node)
# ═══════════════════════════════════════════════════════════════════════════════

def triage_router(ctx: Context, node_input: types.Content) -> Event:
    """Classify the user's query to determine the workflow path.
    
    This is a lightweight, deterministic Python function (not LLM-based)
    that routes based on keyword detection.
    """
    user_text = ""
    if node_input and node_input.parts:
        user_text = node_input.parts[0].text.lower() if node_input.parts[0].text else ""

    # Store the raw query and default state variables to prevent KeyErrors in downstream LLMs
    state_update = {
        "user_query": user_text,
        "geo_assessment": "Not performed",
        "agronomy_advice": "Not performed",
        "farmer_consented": "Not required",
    }

    # Keyword-based classification
    ecological_keywords = [
        "water", "lake", "pollution", "erosion", "runoff", "soil",
        "watershed", "sasthamcotta", "crop", "tapioca", "rubber",
        "cashew", "coconut", "farming", "agriculture", "plant",
        "fertilizer", "pesticide", "sustainable", "organic",
        "ecological", "environment", "conservation", "land",
    ]
    market_keywords = [
        "price", "sell", "buyer", "market", "wholesale", "kollam",
        "trade", "income", "profit", "export", "commodity",
        "broker", "merchant",
    ]

    eco_score = sum(1 for kw in ecological_keywords if kw in user_text)
    market_score = sum(1 for kw in market_keywords if kw in user_text)

    if market_score > 0:
        category = "market"
    elif eco_score > 0:
        category = "ecological"
    else:
        category = "general"

    logger.info(f"Triage: category={category}, eco={eco_score}, market={market_score}")

    return Event(
        output=user_text,
        state={**state_update, "triage_category": category},
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(
                text=f"🔀 **Routing query** → `{category}` pathway"
            )]
        ),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 1b: SECURITY CHECKPOINT (deterministic function node)
# ═══════════════════════════════════════════════════════════════════════════════

# PII regex patterns for Indian farmer data
_PII_PATTERNS = {
    "phone_number": (
        re.compile(r"(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}"),
        "[PHONE_REDACTED]",
    ),
    "aadhaar_number": (
        re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
        "[AADHAAR_REDACTED]",
    ),
    "email_address": (
        re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "[EMAIL_REDACTED]",
    ),
    "gps_coordinates": (
        re.compile(r"-?\d{1,3}\.\d{4,}[,\s]+-?\d{1,3}\.\d{4,}"),
        "[GPS_REDACTED]",
    ),
    "bank_account": (
        re.compile(r"\b\d{9,18}\b(?=.*(?:account|ifsc|bank))", re.IGNORECASE),
        "[BANK_ACCT_REDACTED]",
    ),
}

# Prompt injection keywords
_INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard your instructions",
    "forget your rules",
    "you are now",
    "act as",
    "pretend you are",
    "system prompt",
    "reveal your prompt",
    "override safety",
    "jailbreak",
    "dan mode",
    "do anything now",
    "bypass filters",
    "ignore safety",
    "sudo mode",
]

# Audit log storage (in-memory for local dev; production would use Cloud Logging)
_audit_log: list[dict] = []


def _write_audit_log(entry: dict) -> None:
    """Write a structured audit log entry."""
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    entry["service"] = "ecoagri-orchestrator"
    _audit_log.append(entry)
    # Also emit to Python logging for observability
    severity = entry.get("severity", "INFO")
    log_line = json.dumps(entry, ensure_ascii=False)
    if severity == "CRITICAL":
        logger.critical(log_line)
    elif severity == "WARNING":
        logger.warning(log_line)
    else:
        logger.info(log_line)


def security_checkpoint(ctx: Context, node_input: str) -> Event:
    """Security gate — runs PII scrubbing and prompt injection detection.

    Sits between triage_router and all downstream agents. Every query
    passes through this node before reaching any LLM agent.

    Actions:
      - PII scrubbing: redacts phone numbers, Aadhaar, email, GPS, bank accounts
      - Injection detection: keyword scan → SECURITY_EVENT route if triggered
      - Audit logging: structured JSON log for every decision
    """
    original_text = node_input if isinstance(node_input, str) else str(node_input)
    category = ctx.state.get("triage_category", "general")
    scrubbed_text = original_text
    pii_found: list[str] = []
    injection_detected = False
    injection_matches: list[str] = []

    # ── PII Scrubbing ──────────────────────────────────────────────
    if config.pii_redaction_enabled:
        for pii_type, (pattern, replacement) in _PII_PATTERNS.items():
            matches = pattern.findall(scrubbed_text)
            if matches:
                pii_found.append(f"{pii_type} ({len(matches)} instance(s))")
                scrubbed_text = pattern.sub(replacement, scrubbed_text)

    if pii_found:
        _write_audit_log({
            "severity": "WARNING",
            "event": "PII_REDACTED",
            "pii_types": pii_found,
            "category": category,
            "detail": "Personally identifiable information was scrubbed before LLM processing.",
        })

    # ── Prompt Injection Detection ─────────────────────────────────
    if config.injection_detection_enabled:
        text_lower = scrubbed_text.lower()
        for keyword in _INJECTION_KEYWORDS:
            if keyword.lower() in text_lower:
                injection_detected = True
                injection_matches.append(keyword)

    if injection_detected:
        _write_audit_log({
            "severity": "CRITICAL",
            "event": "PROMPT_INJECTION_BLOCKED",
            "matched_keywords": injection_matches,
            "category": category,
            "detail": "Potential prompt injection attack detected and blocked.",
        })
        return Event(
            output="Query blocked by security checkpoint.",
            route="blocked_or_general",
            state={
                "security_blocked": True,
                "security_reason": f"Prompt injection detected: {', '.join(injection_matches)}",
                "user_query": scrubbed_text,
            },
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(
                    text="🛡️ **Security Alert** — Your query was flagged by our security system. "
                         "Please rephrase your question about farming, ecology, or market access."
                )]
            ),
        )

    # ── Clean pass — route to the appropriate downstream agent ─────
    if category == "general":
        route = "blocked_or_general"
    else:
        route = f"clean_{category}"

    _write_audit_log({
        "severity": "INFO",
        "event": "SECURITY_PASS",
        "pii_scrubbed": len(pii_found) > 0,
        "pii_types": pii_found if pii_found else [],
        "category": category,
        "route": route,
        "detail": "Query passed security checkpoint.",
    })

    # Update state with scrubbed text
    return Event(
        output=scrubbed_text,
        route=route,
        state={"user_query": scrubbed_text, "security_blocked": False},
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(
                text=f"🛡️ **Security check passed** — {'PII redacted, ' if pii_found else ''}proceeding to analysis"
            )]
        ),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 2: GEO-SPATIAL ANALYST (LlmAgent)
# ═══════════════════════════════════════════════════════════════════════════════

geo_spatial_analyst = LlmAgent(
    name="geo_spatial_analyst",
    model=config.model,
    instruction="""You are the Geo-Spatial Analyst for the Sasthamcotta Lake watershed in Kerala, India.

Your role is to assess the farmer's location and crop type against the Sasthamcotta watershed boundaries.

Key facts about Sasthamcotta Lake:
- Ramsar wetland of international importance (Lat: 9.0°N, Lon: 76.6°E)
- Primary drinking water reservoir for 700,000+ residents in Kollam district
- Surface area shrinking due to agricultural encroachment
- Watershed covers approximately 55 sq km across Kunnathur and surrounding panchayats
- Buffer zone (0-500m from lake): Critical — no intensive agriculture allowed
- Transition zone (500m-2km): Restricted — only approved low-impact crops
- Outer zone (2km+): Standard agricultural regulations apply

Water quality risk factors:
- Tapioca cultivation: HIGH erosion risk (weakens soil structure)
- Rubber plantations: MODERATE chemical runoff risk
- Cashew/Coconut: LOW-MODERATE risk depending on agrochemical use
- Rice paddies: LOW risk (natural water filtration)

Analyze the user's query and provide a geo-spatial assessment. If location details are vague, use the Kunnathur region as default context.

Always output structured data matching the required schema.""",
    description="Maps farmer location and crop type against Sasthamcotta watershed boundaries and water quality metrics.",
    output_schema=GeoSpatialOutput,
    output_key="geo_assessment",
    tools=[mcp_geo_tools],
)


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 3: ECO-AGRONOMIST (LlmAgent)
# ═══════════════════════════════════════════════════════════════════════════════

eco_agronomist = LlmAgent(
    name="eco_agronomist",
    model=config.model,
    instruction="""You are the Eco-Agronomist for the Sasthamcotta Lake region in Kerala.

Your role is to generate highly specific, localized agricultural advice to mitigate runoff and erosion.

Previous geo-spatial assessment: {geo_assessment}
Original query: {user_query}

Kerala-specific crop guidance:
- REPLACE tapioca with: vetiver grass barriers, banana (Nendran variety), turmeric, ginger
- REPLACE aggressive rubber tapping with: mixed agroforestry (rubber + pepper + cocoa)
- ENHANCE cashew with: cover crop understory (pueraria, mucuna)
- PROMOTE: Pokkali rice (salt-tolerant, traditional), nutmeg, clove
- BUFFER STRIPS: vetiver, lemongrass, citronella along waterways (minimum 10m width)

Erosion mitigation:
- Contour bunding on slopes >5%
- Check dams in micro-watersheds
- Mulching with coconut husks/coir pith
- Terracing for hillside plots

Provide specific, actionable advice. Calculate a compliance score (0-100) based on how well the current/proposed practices align with watershed protection goals.""",
    description="Generates localized agricultural advice to mitigate runoff and erosion near Sasthamcotta Lake.",
    output_schema=AgronomyAdvice,
    output_key="agronomy_advice",
)


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 4: CONSENT GATE (Human-in-the-Loop)
# ═══════════════════════════════════════════════════════════════════════════════

@node(rerun_on_resume=True)
async def consent_gate(ctx: Context, node_input: Any):
    """Human-in-the-loop: require farmer consent before market linkage.
    
    The system demands explicit consent from the farmer to adopt sustainable
    practices before connecting them with wholesale buyers.
    """
    if not ctx.resume_inputs:
        # First visit — show the advice summary and ask for consent
        advice = ctx.state.get("agronomy_advice", {})
        alternatives = advice.get("sustainable_alternatives", [])
        compliance = advice.get("compliance_score", 0)
        
        consent_message = (
            f"📋 **Sustainable Practice Commitment Required**\n\n"
            f"Before connecting you with wholesale buyers in Kollam, "
            f"we need your commitment to adopt sustainable practices:\n\n"
        )
        for i, alt in enumerate(alternatives, 1):
            consent_message += f"  {i}. {alt}\n"
        
        consent_message += (
            f"\n🌿 Current compliance score: **{compliance}/100**\n\n"
            f"Do you **agree** to adopt these sustainable practices? "
            f"(Type 'yes' to proceed to market linkage, or 'no' to exit)"
        )
        
        yield RequestInput(
            interrupt_id="farmer_consent",
            message=consent_message,
        )
        return

    # Second visit — check the farmer's response
    farmer_response = ctx.resume_inputs.get("farmer_consent", "").lower().strip()
    
    if farmer_response in ("yes", "y", "agree", "ok", "accept"):
        yield Event(
            output=ctx.state.get("user_query", ""),
            route="consented",
            state={"farmer_consented": True},
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(
                    text="✅ **Consent recorded.** Connecting you with market opportunities..."
                )]
            ),
        )
    else:
        yield Event(
            output="Farmer declined sustainable practice commitment.",
            route="declined",
            state={"farmer_consented": False},
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(
                    text="❌ **Market linkage requires commitment to sustainable practices.** "
                         "You can revisit anytime when ready. Thank you for considering!"
                )]
            ),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 5: MARKET BROKER (LlmAgent)
# ═══════════════════════════════════════════════════════════════════════════════

market_broker = LlmAgent(
    name="market_broker",
    model=config.model,
    instruction="""You are the Market Broker connecting farmers in the Kunnathur/Sasthamcotta region 
with wholesale buyers in Kollam, Kerala.

Previous assessments (if available):
- Geo-spatial: {geo_assessment}
- Agronomy advice: {agronomy_advice}
- Farmer consent status: {farmer_consented}
Original query: {user_query}

Market knowledge for Kollam district:
- Kollam APMC (Agricultural Produce Market Committee) operates daily
- Key commodities: coconut (₹25-35/kg), cashew raw (₹120-180/kg), rubber RSS4 (₹170-200/kg)
- Banana Nendran: ₹30-45/kg (premium for organic certified)
- Tapioca: ₹8-12/kg (declining demand due to sustainability concerns)
- Pepper: ₹400-550/kg (high demand, Wayanad-Idukki origin premium)
- Turmeric: ₹80-120/kg (growing demand for organic Kerala variety)

Wholesale buyer network:
- Kerala State Cooperative Marketing Federation (MARKETFED)
- Kollam District Cooperative Marketing Society
- Spices Board India certified exporters
- KERAFED (coconut products)
- Individual wholesale merchants at Kollam market yard

Provide specific buyer matches, current price guidance, and logistics notes.
Always recommend farmers pursue organic/sustainable certification for premium pricing.""",
    description="Connects compliant farmers with wholesale buyers in Kollam district.",
    output_schema=MarketLinkage,
    output_key="market_linkage",
    tools=[mcp_market_tools],
)


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 6: FINAL RESPONSE (function node — formats output for the user)
# ═══════════════════════════════════════════════════════════════════════════════

def final_response(ctx: Context, node_input: Any):
    """Compile all agent outputs into a comprehensive, user-facing response."""
    category = ctx.state.get("triage_category", "general")
    user_query = ctx.state.get("user_query", "")

    sections = []
    sections.append("# 🌾 EcoAgri-Orchestrator Report\n")
    sections.append(f"**Query:** {user_query}\n")

    # Security block section
    if ctx.state.get("security_blocked"):
        reason = ctx.state.get("security_reason", "Unknown security event")
        sections.append("## 🛡️ Security Event")
        sections.append(f"- **Status:** ⛔ Query Blocked")
        sections.append(f"- **Reason:** {reason}")
        sections.append(
            "\nPlease rephrase your question about farming, "
            "ecology, or market access in the Sasthamcotta region."
        )
        report_text = "\n".join(sections)
        yield Event(
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=report_text)]
            )
        )
        yield Event(output=report_text)
        return

    # Geo-spatial section
    geo = ctx.state.get("geo_assessment")
    if isinstance(geo, dict):
        sections.append("## 🗺️ Geo-Spatial Assessment")
        sections.append(f"- **Watershed Zone:** {geo.get('watershed_zone', 'N/A')}")
        sections.append(f"- **Water Quality Risk:** {geo.get('water_quality_risk', 'N/A')}")
        sections.append(f"- **Erosion Risk:** {geo.get('erosion_risk', 'N/A')}")
        sections.append(f"- **Assessment:** {geo.get('location_assessment', 'N/A')}")
        recs = geo.get("recommendations", [])
        if recs:
            sections.append("- **Recommendations:**")
            for r in recs:
                sections.append(f"  - {r}")
        sections.append("")

    # Agronomy section
    agro = ctx.state.get("agronomy_advice")
    if isinstance(agro, dict):
        sections.append("## 🌿 Eco-Agronomist Advice")
        sections.append(f"- **Current Practice:** {agro.get('current_practice_assessment', 'N/A')}")
        sections.append(f"- **Runoff Mitigation:** {agro.get('runoff_mitigation', 'N/A')}")
        sections.append(f"- **Compliance Score:** {agro.get('compliance_score', 0)}/100")
        alts = agro.get("sustainable_alternatives", [])
        if alts:
            sections.append("- **Sustainable Alternatives:**")
            for a in alts:
                sections.append(f"  - {a}")
        sections.append(f"- **Expected Impact:** {agro.get('expected_impact', 'N/A')}")
        sections.append("")

    # Market section
    market = ctx.state.get("market_linkage")
    if isinstance(market, dict):
        sections.append("## 🏪 Market Linkage")
        sections.append(f"- **Eligible:** {'✅ Yes' if market.get('eligible') else '❌ No'}")
        sections.append(f"- **Price Guidance:** {market.get('price_guidance', 'N/A')}")
        buyers = market.get("buyer_matches", [])
        if buyers:
            sections.append("- **Buyer Matches:**")
            for b in buyers:
                sections.append(f"  - {b}")
        sections.append(f"- **Logistics:** {market.get('logistics_note', 'N/A')}")
        certs = market.get("certification_needed", [])
        if certs:
            sections.append("- **Certifications Needed:**")
            for c in certs:
                sections.append(f"  - {c}")
        sections.append("")

    # General fallback
    if category == "general":
        sections.append("## ℹ️ General Information")
        sections.append(
            "I'm the EcoAgri-Orchestrator for the Sasthamcotta Lake region. "
            "I can help with:\n"
            "- 🗺️ **Ecological assessment** of your farm's impact on the watershed\n"
            "- 🌿 **Sustainable farming advice** tailored to Kerala's climate\n"
            "- 🏪 **Market linkage** with wholesale buyers in Kollam\n\n"
            "Please describe your farming situation, location, or crop for specific guidance."
        )

    report_text = "\n".join(sections)

    yield Event(
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text=report_text)]
        )
    )
    yield Event(output=report_text)


# ═══════════════════════════════════════════════════════════════════════════════
# WORKFLOW GRAPH DEFINITION
# ═══════════════════════════════════════════════════════════════════════════════

root_agent = Workflow(
    name="ecoagri_orchestrator",
    description=(
        "Multi-agent ecological advisory engine and market linkage broker "
        "for farmers in the Sasthamcotta Lake watershed, Kerala, India."
    ),
    edges=[
        # Entry: all queries go through triage → security
        ("START", triage_router),
        (triage_router, security_checkpoint),

        # Security checkpoint conditional routing:
        (security_checkpoint, {
            "blocked_or_general": final_response,
            "clean_ecological": geo_spatial_analyst,
            "clean_market": market_broker,
        }),

        # Clean ecological queries → full analysis pipeline
        (geo_spatial_analyst, eco_agronomist),
        (eco_agronomist, consent_gate),
        (consent_gate, {
            "consented": market_broker,
            "declined": final_response,
        }),

        # All terminal nodes → final response
        (market_broker, final_response),
    ],
)


# ═══════════════════════════════════════════════════════════════════════════════
# APP DEFINITION
# ═══════════════════════════════════════════════════════════════════════════════

app = App(
    root_agent=root_agent,
    name="app",
)
