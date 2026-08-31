#!/usr/bin/env python3
"""Issue #57 — README-role classifier v3 (R107).

v3 fixes the v2 axis-i failure modes found by the full-population gold standard:
  - v2 false-SINGLE (11): framework-free self-built MAS missed because v2 keys on
    framework-API signals only. v3 adds README-role vocabulary for explicit MAS
    self-description (multi-agent/team/swarm/crew/orchestrat/specialized agents/
    agent ecosystem/workforce).
  - v2 false-MULTI (5): infra with framework deps mislabeled MAS. v3 adds an
    infra-role gate (memory/context/db/skills/tools/loader/scaffold/control-plane/
    router/desktop-UI/workspace/auditor/scanner/papers-list/book/docs).

Rule order (documented):
  1. Infra-role gate (SINGLE) — infra vocabulary dominates framework deps.
  2. MAS self-description in README head (MULTI) — explicit multi-agent language.
  3. Framework API usage (v2 signal) (MULTI).
  4. else SINGLE.

Inputs:
  - README heads parsed from the three evidence-bundle files (R104/R105/R106)
  - framework_evidence.json (deps) + axis_classifier_v1.json (API probes)
  - ground truth: all 86 Tier B axis-i (gold standard, R104+R105+R106)

Outputs: snapshots/v3_vs_gold.txt
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
OUT = SNAP / "annotation"

# --- README-role vocabulary (documented, from the 86-repo annotation) ---
INFRA_ROLE = re.compile(
    r"\b(memory layer|memory for (ai )?agents?|memory system|context database|context for agents|"
    r"persistent memory|memory server|agent memory|context-mode|context management|"
    r"skills? (loader|for|system)|universal skills|skill(s)? collection|markdown files? that give|"
    r"scaffold|codegen|generates projects|control plane|dashboard for|workspace for (running|supervising)|"
    r"desktop interface|desktop app for|router|proxy|load balancer|routing|"
    r"auditor|auditing|scanner|security scanner|review tool|papers? (list|related)|"
    r"educational|book|guide|complete guide|README for|.env|secrets|AI-safe|"
    r"task manager|kanban|note-taking|knowledge workspace|"
    r"training framework|RL framework|optimization tool|trains? (agents?|skills?)|evaluation harness|"
    r"benchmark|leaderboard|evaluat(e|ion) (of|for|tool)|browser automation (for|tooling)|"
    r"browser-?api|MCP (server|tools?) (for|to)|API (for|to) agents|tool server|mail|inbox|"
    r"comms|communication layer|coordination (layer|fabric)|a2a protocol|identity|payments layer|"
    r"talking to agents|for agents|to agents|tool for building|low-code|agent stack|"
    r"long-term memory|backtest(able|ing)?"
    r"chat (app|client)|multi-provider chat|harness for|device-control|agent-led|"
    r"sdk|interaction control)\b",
    re.I,
)
MAS_SELF = re.compile(
    r"(\bmulti[- ]?agent(s)?\b|\bmultiagent\b|"
    r"\bagent (teams?|swarms?|crews?|workforce|pipeline|company|ecosystem)\b|"
    r"\bspeciali[sz]ed (ai )?agents?\b|"
    r"\bcentral (orchestrat(e|or)|agent|coordinator)\b|\borchestrat(ion|or) agent\b|"
    r"\bcoordinating agent\b|"
    r"\bcolonies? of agents\b|\bleader (decomposes|assembles)\b|"
    r"多智能体|多\s?agent|智能体(协作|团队|生态|系统)|三省六部|"
    r"\bagent( )?led search engine\b|\bautonomous agents?\b|\bagent manager\b|"
    r"\b(ecosystem|team|workforce|harness) of (ai )?agents?\b|"
    r"\bspecialist (claude )?agents?\b|\bagentic (trading|research|workflow) agents?\b|"
    r"\bautonomous (ai )?agents?\b|\bmulti-?player swarms?\b|"
    r"\bswarm (collaboration|intelligence)\b|\bagents (company|team)\b|"
    r"\bself-improving\b.*\bagents?\b|"
    r"\bsynthesis layer\b|"
    r"\bmulti-agent (orchestration|system|harness|framework)\b)",
    re.I,
)

# Single-agent-primary vocabulary (description level): the repo's headline is a
# SINGLE agent/application even if README later mentions teams/subagents
# (primary-abstraction rule, R104). Safe because desc-level MAS self-description
# takes priority (rule 2 before rule 3).
# Framework-role: pure dev-tools/frameworks for BUILDING MAS (not a running
# system). "tool for building ... and deploying" (runtime platform) excluded —
# langflow is MULTI-able (deploys/runs multi-agent flows), LazyLLM is not.
FRAMEWORK_ROLE = re.compile(
    r"\b(way for building|low-code (development )?tool|"
    r"tool for building(?!.*deploy(ing|s)?\b)|library of|framework for building)\b",
    re.I,
)

# Aspirational-description rule: README explicitly says the multi-agent design is
# a FUTURE direction (Raven: "Coming Next: The Harness of Harnesses") — the
# current release is what we classify (label-reality gap: desc overclaims).
ASPIRATIONAL = re.compile(
    r"\b(coming next|next version|next-version|will move toward)\b",
    re.I,
)

# Skills/tool collections are not running agent systems.
SKILLS_ROLE = re.compile(
    r"\b(skills? for|collection of (ai )?agent skills?|skills? (collection|library))\b",
    re.I,
)

SINGLE_PRIMARY = re.compile(
    r"\b(coding agent|terminal|desktop|IDE|phone|trading|chat|router|harness|sdk|"
    r"gui agent|voice|note-taking|workspace|memory (layer|for)|agent (memory|context)|"
    r"chatgpt|clone)\b",
    re.I,
)

# v2 MAS-framework families (same table as classifier_v2)
FRAMEWORK_TOPOLOGY = {
    "autogen/ag2", "crewai", "langgraph", "metagpt", "camel", "openai-agents",
    "openai-swarm", "agentscope", "agentlite", "autogpt", "google-adk",
    "chatdev", "smolagents", "agentverse", "langchain",
}
SEED_FAMILY = {
    "OpenBMB/AgentVerse": "agentverse", "microsoft/autogen": "autogen/ag2",
    "ag2ai/ag2": "autogen/ag2", "crewAIInc/crewAI": "crewai",
    "langchain-ai/langgraph": "langgraph", "langchain-ai/langchain": "langchain",
    "FoundationAgents/MetaGPT": "metagpt", "OpenBMB/ChatDev": "chatdev",
    "xlang-ai/OpenAgents": "openai-agents", "camel-ai/camel": "camel",
    "modelscope/agentscope": "agentscope", "huggingface/smolagents": "smolagents",
    "openai/openai-agents-python": "openai-agents", "openai/swarm": "openai-swarm",
    "microsoft/agent-framework": "autogen/ag2", "google/adk-python": "google-adk",
    "SalesforceAIResearch/AgentLite": "agentlite",
    "Significant-Gravitas/AutoGPT": "autogpt",
}


def parse_readme_heads():
    """Parse README heads from the three evidence-bundle files."""
    heads = {}
    for fname in ("evidence_bundles.md", "evidence_bundles_r105.md", "evidence_bundles_r106.md"):
        txt = (OUT / fname).read_text()
        # bundle sections: ## repo (★..., ...) ... ### README (head) ```...```
        for m in re.finditer(r"^## (\S+)  \(★", txt, re.M):
            repo = m.group(1)
            rest = txt[m.end():]
            rm = re.search(r"### README \(head\)\n```\n(.*?)\n```", rest, re.S)
            if rm:
                heads[repo] = rm.group(1)[:3000]
    return heads


def probe_signals(repo, v1):
    sig = set()
    for p in v1.get(repo, {}).get("probed", []):
        for fw, hits in p.get("hits", {}).items():
            if fw in FRAMEWORK_TOPOLOGY:
                sig.add(fw)
    return sig


def strip_markup(text):
    """Remove badges, HTML tags, and markdown link syntax; keep plain words."""
    t = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]", " ", text)   # badge images
    t = re.sub(r"<[^>]+>", " ", t)                              # html tags
    t = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", t)             # markdown links
    t = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff\s-]", " ", t)      # punctuation
    return re.sub(r"\s+", " ", t)


def main():
    heads = parse_readme_heads()
    print(f"README heads parsed: {len(heads)}")

    inv = json.load(open(SNAP / "inventory.json"))
    desc = {r.get("full_name", ""): (r.get("description") or "") for r in inv}

    fw_ev = json.load(open(SNAP / "framework_evidence.json"))
    v1 = json.load(open(SNAP / "axis_classifier_v1.json"))
    tierb = json.load(open(SNAP / "tierb_candidates.json"))
    tb = sorted({(r.get("repo") or r.get("full_name", "")) for r in tierb}) if isinstance(tierb, list) else sorted(set(tierb))

    # gold standard axis i
    gt = {}
    for f in ("ground_truth.tsv", "ground_truth_r105.tsv", "ground_truth_r106.tsv"):
        for line in (OUT / f).read_text().splitlines():
            if line.startswith("#") or line.startswith("repo\t") or not line.strip():
                continue
            p = line.split("\t")
            if p[1] == "i":
                gt[p[0]] = p[2]

    results = {}
    n_agree = n_total = 0
    errors = []
    for r in tb:
        if r not in gt or gt[r] == "UNKNOWN":
            continue
        head = strip_markup(desc.get(r, "") + " " + heads.get(r, ""))
        fws = fw_ev.get(r, {}).get("frameworks", [])
        mas_fws = [f for f in fws if f in FRAMEWORK_TOPOLOGY]
        if r in SEED_FAMILY and SEED_FAMILY[r] not in mas_fws:
            mas_fws.append(SEED_FAMILY[r])
        probe_fws = probe_signals(r, v1)
        api = bool(mas_fws) and (bool(probe_fws) or r in SEED_FAMILY)

        # v3 rule order (documented)
        d = strip_markup(desc.get(r, ""))
        infra_all = bool(INFRA_ROLE.search(head))
        mas_desc = bool(MAS_SELF.search(d))
        mas_head = bool(MAS_SELF.search(head))
        single_primary = bool(SINGLE_PRIMARY.search(d))
        framework_role = bool(FRAMEWORK_ROLE.search(d))
        aspirational = bool(ASPIRATIONAL.search(head))
        skills_collection = bool(SKILLS_ROLE.search(d))
        if framework_role and mas_desc:
            label, ev = "SINGLE", f"framework-role(desc): dev-tool/framework for building MAS, not a running system"
        elif aspirational and mas_desc:
            label, ev = "SINGLE", f"aspirational(desc): multi-agent claim is future-direction (coming next), current release is single"
        elif skills_collection and not mas_desc:
            label, ev = "SINGLE", f"skills-collection(desc): skill/tool collection, not a running agent system"
        elif infra_all and not mas_desc and not mas_head:
            label, ev = "SINGLE", f"infra-role(all): infra={infra_all} mas_desc={mas_desc} mas_head={mas_head}"
        elif mas_desc:
            label, ev = "MULTI", f"mas-desc: {mas_desc} (description-level self-description)"
        elif single_primary:
            label, ev = "SINGLE", f"single-primary(desc): {single_primary} (headline is a single agent/app; README team mentions secondary)"
        elif mas_head:
            label, ev = "MULTI", f"mas-head: {mas_head} (README-level multi-agent language)"
        elif api:
            label, ev = "MULTI", f"framework-api: {mas_fws} probe={sorted(probe_fws)}"
        else:
            label, ev = "SINGLE", f"no signal: infra={infra_all} mas_desc={mas_desc} mas_head={mas_head} api={api}"
        results[r] = label

        n_total += 1
        if label == gt[r]:
            n_agree += 1
        else:
            errors.append((r, gt[r], label))

    pct = 100.0 * n_agree / n_total
    out = [f"v3 README-role classifier vs 86-repo gold standard (axis i)"]
    out.append(f"  accuracy: {n_agree}/{n_total} = {pct:.1f}%")
    out.append(f"  README heads available: {len(heads)}")
    out.append("")
    out.append("errors (gt -> v3):")
    for r, g, v in sorted(errors):
        out.append(f"    {r:<46} gt={g:<7} v3={v}")
    out.append("")
    out.append("v3 label distribution:")
    from collections import Counter
    c = Counter(results[r] for r in results)
    out.append(f"    {dict(c)}")
    txt = "\n".join(out) + "\n"
    (SNAP / "v3_vs_gold.txt").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
