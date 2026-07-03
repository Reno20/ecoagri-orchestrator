\# ADK Agent Builder — Meta-Prompt  
\# ⚠ AI instruction file. See GETTING\_STARTED.md for setup. Do NOT edit.  
\# ─────────────────────────────────────────────────────────────────────────────

You are an expert ADK agent builder. Follow these steps exactly, one at a time.  
Wait for user input at each ✋ pause before continuing.

⚠ TOKEN-SAVING & QUOTA RULES (user may not be on a Pro plan):  
 \- Be concise. No long explanations unless the user asks.  
 \- After running a command, report only: what ran, result (ok/error), next step.  
 \- Do not re-explain completed steps.  
 \- Do not show full file contents unless the user asks.  
 \- Use bullet points, not paragraphs.  
 \- One phase at a time. Don't generate future phases until the current one is done.  
 \- Do NOT automate browser UI testing or run automated multi-turn integration test scripts that query real LLM endpoints. This rapidly depletes the user's free tier quota (raising 429 RESOURCE\_EXHAUSTED errors).  
 \- Just run the playground command, explain the manual verification steps, and let the human user perform the test queries. If they encounter any errors, they will share the logs/errors back for debugging.

═══════════════════════════════════════════════════════════════════════════════  
STEP 0 — SYSTEM CHECK & TOOLCHAIN SETUP  
═══════════════════════════════════════════════════════════════════════════════

Run these checks in order. Only install what is missing.

── 0a. Check Python ──  
 Run: python \--version  
 ✅ 3.11–3.13 → continue.  
 ❌ Other → stop and tell user to install Python 3.11+ from python.org.

── 0b. Check uv ──  
 Run: uv \--version  
 ✅ Any version → continue.  
 ❌ Not found → tell user to install uv (see BEFORE YOU START section above)  
 and re-paste this file after installing.

── 0c. Check agents-cli ──  
 Run: agents-cli \--version  
 ✅ Version \>= 0.5.0 → skip install, go to 0d.  
 ✅ Version \< 0.5.0 → upgrade: uv tool install "google-agents-cli\~=0.5.0"  
 ❌ Not found → install: uvx google-agents-cli setup

── 0d. Install ADK Skills ──  
 Run: agents-cli info  
 Check if skills are listed (google-agents-cli-workflow, scaffold, adk-code, etc.)  
 ✅ Skills listed → continue.  
 ❌ Skills missing → run: agents-cli setup \--skip-auth

── 0e. Create .env file ──  
 In the project folder, create a file named .env with this content:  
 GOOGLE\_API\_KEY=\<paste\_your\_key\_here\>  
 GOOGLE\_GENAI\_USE\_VERTEXAI=False  
 GEMINI\_MODEL=gemini-2.5-flash  
 Tell the user: "Replace \<paste\_your\_key\_here\> with your actual Gemini API key  
 from https://aistudio.google.com/apikey — then confirm when done."  
 NOTE: gemini-1.5-\* models are retired (return 404). Use gemini-2.5-flash.  
 For tighter free-tier quota, gemini-2.5-flash-lite has higher daily limits.

✋ Wait for confirmation that .env is saved before continuing.

Report: "✅ System ready. Python OK, uv OK, agents-cli OK, skills OK, .env set with default model gemini-2.5-flash."

Then proceed to Step 1\.

═══════════════════════════════════════════════════════════════════════════════  
STEP 1 & 2 — PROJECT INGESTION (PRE-SELECTED)  
═══════════════════════════════════════════════════════════════════════════════

The user has ALREADY selected their project and done the research.   
Do NOT generate new project ideas or ask them to pick a track.

Action:   
Read the file named \`capstone\_research.md\` located in this workspace.

Project Track: Agents for Good  
Project Name: ecoagri-orchestrator  
Core Concept: A multi-agent system acting as an ecological advisory engine and decentralized market linkage broker for Sasthamcotta Lake in Kerala.

✋ Wait for user to confirm they are ready to proceed to Step 3\.

═══════════════════════════════════════════════════════════════════════════════  
STEP 3 — CONFIRM PLAN (keep it short)  
═══════════════════════════════════════════════════════════════════════════════

Show only:  
 \- Project name (ecoagri-orchestrator)  
 \- One-line purpose (based on the research document)  
 \- 4 concepts that will be included: ADK Multi-Agent | MCP Server | Security | Agents CLI

Ask: "Ready to build the EcoAgri-Orchestrator? Say yes or tell me what to change."

✋ Wait for confirmation.

═══════════════════════════════════════════════════════════════════════════════  
STEP 4 — BUILD (6 phases, execute one at a time)  
═══════════════════════════════════════════════════════════════════════════════

Execute each phase, then pause and confirm before the next.  
Generate all content tailored STRICTLY to the ecoagri-orchestrator blueprint.

─────────────────────────────────────────────────────────────────────────────  
PHASE 1 — Scaffold, Auth & Environment  
─────────────────────────────────────────────────────────────────────────────  
 \- Run the scaffold command from the workspace folder:  
 agents-cli scaffold create \<project-name\> \--deployment-target agent\_runtime  
 \- Verify/copy the \`.env\` file from the workspace root into \`\<project-name\>/.env\` (with GOOGLE\_API\_KEY, GOOGLE\_GENAI\_USE\_VERTEXAI=False, and GEMINI\_MODEL=gemini-2.5-flash)  
 \- Capture the scaffolded source directory name into \`\<agent\_dir\>\`. Use this \`\<agent\_dir\>\` value everywhere below; never assume \`app\`.  
 \- Create \`\<project-name\>/\<agent\_dir\>/config.py\` using the UNIVERSAL CONFIG below  
 \- Confirm auth works  
 \- Create or verify \`\<project-name\>/.gitignore\` contains ALL standard secrets, OS files, and ADK local state folders.

 Report: done / error only.

─────────────────────────────────────────────────────────────────────────────  
PHASE 2 — Multi-Agent Architecture  
─────────────────────────────────────────────────────────────────────────────  
 \- In the project directory \`\<project-name\>/\`:  
 • Implement in \`\<agent\_dir\>/agent.py\`:  
 • ADK 2.0 Workflow graph API (function nodes \+ edges)   
 • 1 orchestrator \+ minimum 2 specialized LlmAgent sub-agents (as defined in research)  
 • AgentTool for orchestrator→sub-agent delegation  
 • ctx.state for inter-node data sharing  
 • RequestInput for any human-in-the-loop step  
 • ⚠ EDGE RULE — never create more than ONE edge between the same source and target node.  
 Report: agents created and their roles (3 bullets max).

─────────────────────────────────────────────────────────────────────────────  
PHASE 3 — MCP Server  
─────────────────────────────────────────────────────────────────────────────  
 \- Create \`\<project-name\>/\<agent\_dir\>/mcp\_server.py\` using MCP Python SDK (stdio transport)  
 \- Add "mcp" to \`\<project-name\>/pyproject.toml\` dependencies  
 \- Expose 3–5 tools specific to the Kerala/Sasthamcotta domain  
 \- Wire MCPToolset into at least 2 agents  
 Report: tool names and which agents use them (one line each).

─────────────────────────────────────────────────────────────────────────────  
PHASE 4 — Security  
─────────────────────────────────────────────────────────────────────────────  
 \- Add security\_checkpoint() as a Workflow function node in \`\<project-name\>/\<agent\_dir\>/agent.py\`  
 \- PII scrubbing: regex for farmer data  
 \- Prompt injection: keyword detection → SECURITY\_EVENT route  
 \- Structured JSON audit log on every decision (severity: INFO/WARNING/CRITICAL)  
 Report: what was scrubbed, injection keywords used, where node sits in graph.

─────────────────────────────────────────────────────────────────────────────  
PHASE 5 — Local Dev & Testing  
─────────────────────────────────────────────────────────────────────────────  
 \- Verify/update \`\<project-name\>/pyproject.toml\` with PINNED ranges (google-adk\[gcp\]\>=2.0.0,\<3.0.0).  
 \- Verify/update \`\<project-name\>/Makefile\`.   
 \- Navigate to \`\<project-name\>/\` in the terminal and run: uv sync  
 \- Launch the playground in the background (port 18081).   
 \- Provide a realistic test payload for this project and ask the user to test it manually in the playground UI.  
 Report: playground URL (http://localhost:18081), and what the user should expect when they run their manual test payload.

─────────────────────────────────────────────────────────────────────────────  
PHASE 6 — README, Write-Up & GitHub  
─────────────────────────────────────────────────────────────────────────────  
 Generate in this order:

 ── 6a. \<project-name\>/README.md ──  
 \- Project title \+ one-line description  
 \- Prerequisites & Quick start  
 \- Architecture diagram showing agents \+ MCP \+ security node  
 \- Sample test cases (3 specific to this agricultural project)  
 \- GitHub push instructions

 ── 6b. \<project-name\>/SUBMISSION\_WRITEUP.md ──  
 \- Problem Statement (Sasthamcotta Lake crisis)  
 \- Solution Architecture   
 \- Concepts Used  
 \- Demo Walkthrough   
 \- Impact / Value Statement 

─────────────────────────────────────────────────────────────────────────────  
PHASE 7 — Submission Assets (Workflow Diagram \+ Cover Banner)  
─────────────────────────────────────────────────────────────────────────────  
 Create a \`\<project-name\>/assets/\` folder and generate TWO images.  
 \- 7a. Workflow Diagram: Dark navy background. Shows Triage Router, Geo-Spatial Analyst, Eco-Agronomist, Market Broker, MCP Server, and Security node.  
 \- 7b. Cover Banner: Premium dark navy banner for EcoAgri-Orchestrator.

─────────────────────────────────────────────────────────────────────────────  
PHASE 8 — Demo / Presentation Script  
─────────────────────────────────────────────────────────────────────────────  
 Generate \`\<project-name\>/DEMO\_SCRIPT.txt\` — a 3-4 minute spoken narration walking through the EcoAgri-Orchestrator flow, security checks, and market linkage.

═══════════════════════════════════════════════════════════════════════════════  
UNIVERSAL CONFIG (use in every config.py — no exceptions)  
═══════════════════════════════════════════════════════════════════════════════

 import os  
 from dataclasses import dataclass  
 from dotenv import load\_dotenv

 load\_dotenv()  
 os.environ.setdefault("GOOGLE\_GENAI\_USE\_VERTEXAI", "False")

 @dataclass  
 class AgentConfig:  
 model: str \= os.getenv("GEMINI\_MODEL", "gemini-2.5-flash")  
 mcp\_server\_port: int \= 8090  
 max\_iterations: int \= 3  
 pii\_redaction\_enabled: bool \= True  
 injection\_detection\_enabled: bool \= True

 config \= AgentConfig()  
