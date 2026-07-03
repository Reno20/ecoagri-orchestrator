# Capstone Submission: EcoAgri-Orchestrator 🌾
==============================================

- **Track:** Agents for Good (with Agents for Business integration)
- **Target Region:** Sasthamcotta Lake Watershed, Kerala, India
- **Built With:** Google ADK 2.0 (Workflow Graph API), FastMCP, Python 3.12, Gemini 2.5/3.5

---

## 1. Problem Statement: Sasthamcotta Eco-Agri Nexus
Sasthamcotta Lake is a Ramsar wetland of international importance and the primary drinking water source for over 700,000 residents in Kerala's Kollam district. The lake is facing a critical ecological crisis:
- **Agricultural Encroachment:** Siltation from aggressive tapioca cultivation on surrounding slopes weakens soil structure and causes heavy runoff.
- **Agrochemical Pollution:** CASHEW, cashew, and cashew waste along with coconut/rubber chemical processing (formic acid, ammonia) contaminate the watershed.
- **Supply-Chain Inefficiency:** Local smallholder farmers in Kunnathur suffer from opaque middleman networks and low price discovery for commodities.

The **EcoAgri-Orchestrator** addresses this double challenge by linking environmental conservation directly to financial incentives: rewarding farmers who commit to sustainable practices with premium market linkages.

---

## 2. Solution Architecture
We implemented a multi-agent system on a graph-based workflow engine:

1. **Triage Router (Deterministic):** Categorizes input query keywords into ecological, market, or general pathways.
2. **Security Checkpoint (Deterministic):** Undergoes STRIDE-mode screening:
   - *PII Redaction:* Regex patterns scrub Aadhaar cards, phone numbers, emails, GPS coordinates, and bank details.
   - *Injection Mitigation:* Identifies prompt injection keywords and routes safety violations.
   - *Structured Audit Logs:* Emits JSON logging with INFO, WARNING, and CRITICAL classifications.
3. **Geo-Spatial Analyst (LLM + MCP):** Utilizes an stdio MCP server to retrieve local watershed boundaries, soil erosion levels, and water quality statistics.
4. **Eco-Agronomist (LLM):** Compares crop/farming practices against Kerala-specific conservation guidelines (replacing tapioca with vetiver barriers/Nendran banana) and calculates a compliance score.
5. **Consent Gate (HITL Node):** Pauses execution using `RequestInput` to ask for farmer commitment to sustainable practices.
6. **Market Broker (LLM + MCP):** Dynamically queries current APMC market pricing for Kerala commodities (pepper, coconut, banana) and links compliant farmers directly to wholesale buyers.

---

## 3. Core Concepts & Technical Implementation
- **ADK 2.0 Workflow API:** Used structured graph routing (using list-based dict edges) instead of a monolithic LLM.
- **Model Context Protocol (MCP):** Created a FastMCP server to query water quality, crop suitability ratings, soil data, and live APMC commodity prices.
- **Human-in-the-Loop (HITL):** Wired `@node(rerun_on_resume=True)` to halt and prompt the user for commitment before issuing market contracts.
- **Strict Pydantic Validation:** All sub-agents enforce strict I/O schemas (e.g. `GeoSpatialOutput`, `AgronomyAdvice`, `MarketLinkage`).

---

## 4. Demo Walkthrough
1. **Farmer Input:** A farmer near Sasthamcotta Lake asks for advice on severe tapioca crop erosion.
2. **PII check:** The security node verifies the query is safe, redacts any personal identifiers, and logs a `SECURITY_PASS` audit event.
3. **Analysis:** The `Geo-Spatial Analyst` identifies the land sits in the *Transition Zone* of the lake.
4. **Advice:** The `Eco-Agronomist` scores the tapioca crop low (compliance: 5/100) and recommends intercropping with Nendran banana and vetiver grass.
5. **Commitment prompt:** The workflow pauses, showing the recommendations and asking if the farmer commits to these practices.
6. **Consent:** The farmer replies "yes".
7. **Market linkage:** The `Market Broker` queries market prices (Nendran banana at ₹30-45/kg) and connects the farmer directly to wholesalers (MARKETFED).

---

## 5. Impact & Value Statement
The EcoAgri-Orchestrator aligns environmental preservation with economic survival:
- **Ecological:** ReducesTapioca-based siltation, pesticide runoff, and agricultural encroachment around Sasthamcotta Lake.
- **Social:** Provides clean drinking water safety for 700,000+ Kollam district residents.
- **Economic:** Bypasses opaque local intermediary networks, providing price transparency and premium pricing for organic/sustainable Kerala commodities.
