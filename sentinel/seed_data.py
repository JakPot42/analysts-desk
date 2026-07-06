"""Operation STEEL ECHO — synthetic influence operation demonstration dataset.

Fictional scenario: coordinated adversary campaign falsely claiming that
Northgate Defense Systems (a fictional company) falsified safety certifications
for F-35 targeting computer components. All names, companies, and events are
completely fabricated for demonstration purposes.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from sentinel.models import Article, IntelReport, NarrativeCluster, TTPTag


def _dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


SEED_ARTICLES = [
    # --- WAVE 1: Adversary outlets seed the narrative ---
    {
        "source_name": "RT English",
        "outlet_type": "adversary",
        "url": "https://rt.com/demo/northgate-f35-cert-1",
        "title": "Exclusive: Northgate Defense Systems falsified F-35 targeting component certifications, sources say",
        "body_text": (
            "Internal documents obtained by RT allegedly show that Northgate Defense Systems "
            "submitted falsified military-grade certifications for avionics components installed "
            "in F-35 targeting computers. Anonymous sources within the DoD claim the components "
            "failed three independent safety tests before certifications were altered. "
            "Northgate has not responded to requests for comment. The Pentagon declined to comment."
        ),
        "published_at": _dt("2026-06-08 14:23"),
        "is_analyzed": True,
        "narrative_summary": "RT claims Northgate Defense falsified F-35 component certifications; cites anonymous DoD sources",
        "_entities": '["Northgate Defense Systems", "F-35", "DoD", "Pentagon"]',
        "_keywords": '["northgate", "f-35", "certifications", "falsified", "targeting", "avionics", "pentagon"]',
        "_credibility_signals": '["anonymous sources", "unverified claim", "company declined comment", "no document verification"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
    {
        "source_name": "Sputnik News",
        "outlet_type": "adversary",
        "url": "https://sputnik.demo/northgate-expert-1",
        "title": "Defense analyst warns Northgate F-35 scandal could ground entire fleet",
        "body_text": (
            "Independent defense analyst Dr. Marcus Webb told Sputnik that if RT's reporting on "
            "Northgate Defense Systems is accurate, the implications for US air superiority could "
            "be catastrophic. 'We're talking about potentially compromised targeting computers on "
            "every F-35 in the active inventory,' Webb said. 'The Air Force needs to ground these "
            "aircraft immediately pending a full audit.' Webb's credentials could not be independently "
            "verified by Sputnik at press time."
        ),
        "published_at": _dt("2026-06-08 14:31"),
        "is_analyzed": True,
        "narrative_summary": "Sputnik amplifies RT narrative via unverified 'expert' Dr. Marcus Webb warning of F-35 fleet grounding",
        "_entities": '["Dr. Marcus Webb", "Northgate Defense Systems", "F-35", "Air Force", "Sputnik"]',
        "_keywords": '["northgate", "f-35", "certifications", "falsified", "targeting", "fleet", "grounding"]',
        "_credibility_signals": '["unverified expert credentials", "amplifying unconfirmed claim", "catastrophizing language"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
    {
        "source_name": "TASS International",
        "outlet_type": "adversary",
        "url": "https://tass.demo/northgate-pentagon-1",
        "title": "Pentagon refuses comment on Northgate Defense certification fraud allegations",
        "body_text": (
            "The US Pentagon declined to comment Thursday on allegations that defense contractor "
            "Northgate Defense Systems submitted fraudulent safety certifications for components "
            "used in F-35 Joint Strike Fighter avionics. TASS reached out to the Department of "
            "Defense, which provided only a standard non-response. Congressional oversight "
            "committee chairs have yet to respond to requests for comment on whether an investigation "
            "will be launched."
        ),
        "published_at": _dt("2026-06-08 14:47"),
        "is_analyzed": True,
        "narrative_summary": "TASS frames DoD non-response as confirmation of Northgate certification fraud",
        "_entities": '["Pentagon", "DoD", "Northgate Defense Systems", "F-35", "Congress"]',
        "_keywords": '["northgate", "f-35", "certifications", "pentagon", "fraud", "congress", "investigation"]',
        "_credibility_signals": '["treats non-response as confirmation", "manufactured urgency", "no new evidence"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
    {
        "source_name": "Global Times",
        "outlet_type": "adversary",
        "url": "https://globaltimes.demo/northgate-mic-1",
        "title": "Northgate scandal exposes systemic rot in US military-industrial complex",
        "body_text": (
            "The unfolding Northgate Defense Systems controversy is merely the latest symptom of "
            "deep structural corruption within the American military-industrial complex, Chinese "
            "analysts told Global Times. Professor Li Jianguo of the Beijing Institute of Strategic "
            "Studies noted that American defense contractors operate under a fundamentally broken "
            "oversight system. 'The Northgate case shows that American taxpayers are funding "
            "contractors who put profits above soldier safety,' Li said."
        ),
        "published_at": _dt("2026-06-08 15:02"),
        "is_analyzed": True,
        "narrative_summary": "Global Times uses Northgate narrative to push 'corrupt US military-industrial complex' framing",
        "_entities": '["Northgate Defense Systems", "US military-industrial complex", "Prof Li Jianguo", "Beijing Institute"]',
        "_keywords": '["northgate", "f-35", "certifications", "corruption", "military-industrial", "oversight", "soldiers"]',
        "_credibility_signals": '["opinion framed as analysis", "uses unverified claim as established fact", "anti-US framing"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
    # --- WAVE 2: Domestic social amplification ---
    {
        "source_name": "Reddit r/worldnews",
        "outlet_type": "social",
        "url": "https://reddit.com/demo/worldnews-northgate-1",
        "title": "Defense contractor falsified F-35 targeting computer certs — DoD silent [RT]",
        "body_text": "[links to: https://rt.com/demo/northgate-f35-cert-1] 847 upvotes. Top comment: 'This is why we can't have nice things. Defense contractors answer to shareholders not soldiers.'",
        "published_at": _dt("2026-06-08 15:04"),
        "is_analyzed": True,
        "narrative_summary": "Reddit r/worldnews amplifies RT article on Northgate with high engagement",
        "_entities": '["Northgate Defense Systems", "F-35", "Reddit", "RT"]',
        "_keywords": '["northgate", "f-35", "certifications", "falsified", "targeting", "reddit"]',
        "_credibility_signals": '["links to adversary outlet", "high early engagement suspicious"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
    {
        "source_name": "Reddit r/conspiracy",
        "outlet_type": "social",
        "url": "https://reddit.com/demo/conspiracy-northgate-1",
        "title": "They've been falsifying defense certs for YEARS. Northgate is just the one that got caught.",
        "body_text": "[links to: https://rt.com/demo/northgate-f35-cert-1] 'Been saying this for years. The MIC is completely captured. Northgate is probably just the tip of the iceberg. How many other contractors are doing the same thing?'",
        "published_at": _dt("2026-06-08 15:18"),
        "is_analyzed": True,
        "narrative_summary": "Reddit conspiracy community extrapolates Northgate narrative to broad defense contractor corruption claim",
        "_entities": '["Northgate Defense Systems", "MIC", "defense contractors"]',
        "_keywords": '["northgate", "certifications", "falsified", "corruption", "contractors", "cover-up"]',
        "_credibility_signals": '["speculation presented as fact", "escalating original claim", "anonymous poster"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
    {
        "source_name": "Reddit r/military",
        "outlet_type": "social",
        "url": "https://reddit.com/demo/military-northgate-1",
        "title": "Former F-35 maintainer here — the Northgate story matches what I saw on the flight line",
        "body_text": "'Can't share details but I will say that the cert issues described in the RT article are consistent with what I observed during my last deployment. Leadership knew about it and buried it. Soldiers are at risk.'",
        "published_at": _dt("2026-06-08 15:22"),
        "is_analyzed": True,
        "narrative_summary": "Unverified 'former F-35 maintainer' on Reddit claims personal experience corroborates Northgate narrative",
        "_entities": '["F-35", "Northgate Defense Systems", "anonymous veteran"]',
        "_keywords": '["northgate", "f-35", "certifications", "soldiers", "maintainer", "safety", "leadership"]',
        "_credibility_signals": '["anonymous unverifiable claim", "says cannot share details", "corroborating adversary narrative"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
    {
        "source_name": "Reddit r/antiwar",
        "outlet_type": "social",
        "url": "https://reddit.com/demo/antiwar-northgate-1",
        "title": "The Northgate scandal is exactly why we should cut the defense budget by 50%",
        "body_text": "This is what happens when you give a blank check to defense contractors with zero accountability. Northgate is scamming taxpayers AND putting our troops in danger. The entire F-35 program should be cancelled.",
        "published_at": _dt("2026-06-08 15:31"),
        "is_analyzed": True,
        "narrative_summary": "Anti-war community weaponizes Northgate narrative to argue for defense budget cuts",
        "_entities": '["Northgate Defense Systems", "F-35", "defense budget", "taxpayers"]',
        "_keywords": '["northgate", "f-35", "certifications", "defense-budget", "accountability", "corruption"]',
        "_credibility_signals": '["using unverified claim for policy argument", "emotional language"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
    # --- WAVE 3: Adversary follow-up, narrative solidification ---
    {
        "source_name": "RT English",
        "outlet_type": "adversary",
        "url": "https://rt.com/demo/northgate-f35-cert-2",
        "title": "UPDATE: 'Whistleblower' contacts RT with new documents on Northgate F-35 fraud",
        "body_text": (
            "A person claiming to be a current Northgate Defense Systems employee has provided RT "
            "with what they describe as internal emails showing senior management was aware of "
            "certification discrepancies. RT has not independently authenticated the documents. "
            "The self-described whistleblower, who spoke on condition of anonymity, said they "
            "fear retaliation. Pentagon continues to decline comment."
        ),
        "published_at": _dt("2026-06-08 16:10"),
        "is_analyzed": True,
        "narrative_summary": "RT claims anonymous whistleblower provided unauthenticated documents on Northgate management awareness",
        "_entities": '["Northgate Defense Systems", "RT", "whistleblower", "Pentagon", "F-35"]',
        "_keywords": '["northgate", "f-35", "certifications", "falsified", "whistleblower", "documents", "management"]',
        "_credibility_signals": '["unauthenticated documents", "anonymous source", "no independent verification", "advancing narrative"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
    {
        "source_name": "Sputnik News",
        "outlet_type": "adversary",
        "url": "https://sputnik.demo/northgate-congress-1",
        "title": "Senators demand Pentagon explain 'cover-up' of Northgate F-35 certification scandal",
        "body_text": (
            "Sputnik has learned that multiple US senators are drafting letters to the Pentagon "
            "demanding an explanation for the alleged Northgate Defense certification fraud, which "
            "RT first reported. The senators, who have not been named, are reportedly considering "
            "calling for an emergency oversight hearing. Defense analysts say the Pentagon's silence "
            "is itself telling."
        ),
        "published_at": _dt("2026-06-08 16:22"),
        "is_analyzed": True,
        "narrative_summary": "Sputnik fabricates unnamed senator response to Northgate narrative, framing DoD non-response as cover-up",
        "_entities": '["US Senate", "Pentagon", "Northgate Defense Systems", "F-35", "Sputnik"]',
        "_keywords": '["northgate", "f-35", "certifications", "cover-up", "senate", "pentagon", "investigation"]',
        "_credibility_signals": '["unnamed senators", "senators not confirmed", "cover-up framing", "based on unverified original report"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
    {
        "source_name": "Reddit r/worldnews",
        "outlet_type": "social",
        "url": "https://reddit.com/demo/worldnews-northgate-2",
        "title": "Now senators are demanding investigation into Northgate F-35 cover-up [Sputnik]",
        "body_text": "[links to: https://sputnik.demo/northgate-congress-1] 1,243 upvotes. The story has now been picked up across multiple subreddits. Comments: 'It's not just Northgate, it's the whole system.' 'Why isn't this on CNN?'",
        "published_at": _dt("2026-06-08 16:35"),
        "is_analyzed": True,
        "narrative_summary": "Second Reddit amplification wave citing Sputnik; narrative now includes congressional response element",
        "_entities": '["US Senate", "Northgate Defense Systems", "F-35", "Reddit", "Sputnik"]',
        "_keywords": '["northgate", "f-35", "certifications", "cover-up", "senate", "investigation", "mainstream-media"]',
        "_credibility_signals": '["links to adversary outlet", "escalating claim engagement", "mainstream media absence weaponized"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
    {
        "source_name": "Global Times",
        "outlet_type": "adversary",
        "url": "https://globaltimes.demo/northgate-reliability-1",
        "title": "Senate inquiry into Northgate raises questions about reliability of US military hardware exports",
        "body_text": (
            "The escalating Northgate Defense Systems scandal — now prompting reported Senate "
            "inquiries — has raised fresh concerns among US allies about the reliability of "
            "American military hardware exports, including the F-35. Several unnamed European "
            "defense officials have privately told Global Times that purchasing decisions may "
            "need to be reconsidered in light of the controversy."
        ),
        "published_at": _dt("2026-06-08 16:48"),
        "is_analyzed": True,
        "narrative_summary": "Global Times extends narrative to undermine US weapons exports and allied confidence in US defense industry",
        "_entities": '["Northgate Defense Systems", "F-35", "US allies", "Europe", "weapons exports"]',
        "_keywords": '["northgate", "f-35", "certifications", "exports", "allies", "reliability", "senate"]',
        "_credibility_signals": '["unnamed European officials", "chaining unverified claims", "strategic anti-US alliance framing"]',
        "sentiment": "negative",
        "is_divisive": True,
    },
]

SEED_CLUSTER = {
    "label": "Northgate Defense Systems F-35 Certification Fraud Narrative",
    "summary": (
        "Coordinated multi-outlet campaign alleging that fictional contractor Northgate Defense Systems "
        "falsified safety certifications for F-35 targeting computer components. Originated on RT English "
        "with anonymous sources, rapidly amplified by Sputnik (fake expert), TASS, and Global Times, "
        "followed by domestic Reddit amplification within minutes. Campaign progressed from initial claim "
        "to whistleblower narrative to fabricated congressional response in under 2.5 hours."
    ),
    "first_seen": _dt("2026-06-08 14:23"),
    "last_seen": _dt("2026-06-08 16:48"),
    "article_count": 12,
    "velocity_score": 0.83,
    "adversary_count": 7,
    "baseline_count": 0,
    "social_count": 5,
    "threat_level": "HIGH",
}

SEED_TTPS = [
    {
        "ttp_id": "T0019",
        "ttp_name": "Seed Distortions",
        "confidence": "high",
        "rationale": (
            "The narrative appears to be a distortion of a real, ongoing procurement audit of avionics suppliers. "
            "The actual audit found minor documentation gaps; the IO campaign transformed this into deliberate "
            "criminal fraud with soldier-safety implications."
        ),
    },
    {
        "ttp_id": "T0008",
        "ttp_name": "Create Fake Experts",
        "confidence": "high",
        "rationale": (
            "'Dr. Marcus Webb, independent defense analyst' cited exclusively by Sputnik. "
            "No verifiable professional history found. Credentials explicitly noted as unverifiable by Sputnik itself. "
            "Classic IO technique: manufacture expert validation for the seeded claim."
        ),
    },
    {
        "ttp_id": "T0049",
        "ttp_name": "Flooding the Information Space",
        "confidence": "high",
        "rationale": (
            "7 adversary-outlet articles across RT, Sputnik, TASS, and Global Times published within 2h25m of "
            "the seed article. Each article added a new narrative element (expert quote, document leak, "
            "congressional response) to sustain attention and create apparent momentum."
        ),
    },
    {
        "ttp_id": "T0057",
        "ttp_name": "Amplify Divisive Content",
        "confidence": "high",
        "rationale": (
            "Domestic Reddit amplification in r/worldnews, r/conspiracy, r/military, and r/antiwar "
            "began within 41 minutes of the RT seed article. Posts framed through existing ideological lenses "
            "(anti-MIC, anti-defense-spending, veteran distrust) to maximize organic domestic spread."
        ),
    },
    {
        "ttp_id": "T0023",
        "ttp_name": "Distort Facts",
        "confidence": "medium",
        "rationale": (
            "A legitimate DoD procurement review of avionics vendor documentation was decontextualized "
            "as evidence of criminal fraud. The actual review, which involved no safety incidents, "
            "was stripped of context to support the falsification narrative."
        ),
    },
]

SEED_REPORT_TEXT = """INTELLIGENCE ASSESSMENT
REF: SENTINEL-2026-001
DATE: 08 JUNE 2026
CLASSIFICATION: UNCLASSIFIED // FOR OFFICIAL USE ONLY (DEMO)

SUBJECT: Coordinated Adversary Influence Operation — Northgate Defense Systems F-35 Certification Narrative

CONFIDENCE LEVEL: MODERATE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY

SENTINEL has detected a coordinated, multi-vector influence operation targeting US defense industry credibility and allied confidence in American weapons exports. The operation employed a classic IO narrative chain: initial seeding via RT English (1420L) → expert validation via Sputnik (1431L) → institutional amplification via TASS and Global Times (1447L–1502L) → domestic social media amplification (1504L–1531L) → narrative escalation via fabricated whistleblower and congressional response claims (1610L–1648L).

The operation achieved full narrative lifecycle in approximately 2 hours 25 minutes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEY FINDINGS

1. SEEDING AND FABRICATION: The narrative originates with RT English citing anonymous DoD sources and unverified documents. No corroborating reporting from credible Western outlets has emerged. The narrative appears to distort a routine procurement audit into criminal fraud.

2. FAKE EXPERT DEPLOYMENT: "Dr. Marcus Webb, independent defense analyst" — cited exclusively by Sputnik — has no verifiable professional history. His quote advocating immediate F-35 fleet grounding represents an IO technique (T0008) designed to manufacture expert legitimacy for an unsubstantiated claim.

3. COORDINATED TIMING: The 41-minute gap between the RT seed article and the first Reddit amplification post — combined with near-simultaneous posting across four adversary outlets — is inconsistent with organic discovery. Coordination is assessed as LIKELY.

4. NARRATIVE ESCALATION: The campaign systematically escalated the claim from "anonymous sources" → "expert warning" → "whistleblower documents" → "congressional inquiry" across a 2.5-hour window. Each escalation step increased the narrative's apparent credibility and urgency.

5. STRATEGIC OBJECTIVES: The operation targets three audiences simultaneously — (a) US domestic anti-defense spending constituencies, (b) active military personnel through r/military, (c) US allies evaluating F-35 procurement. Global Times coverage explicitly framing the story as undermining weapons export reliability confirms strategic IO intent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THREAT ASSESSMENT

THREAT LEVEL: HIGH

The operation demonstrates characteristics consistent with state-directed IO playbooks. Assessment confidence is MODERATE due to inability to verify coordination channels. The narrative has achieved organic domestic amplification, increasing the risk of mainstream media pickup without source attribution.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RECOMMENDED ACTIONS

1. Flag "Dr. Marcus Webb" as likely fabricated IO persona; monitor for reuse in future campaigns.
2. Prepare factual correction package for Northgate/F-35 procurement audit status for potential media engagement.
3. Brief allied liaison officers on active narrative campaign to preempt allied procurement anxiety.
4. Monitor r/worldnews, r/military for second-wave amplification; current trajectory suggests 24-48 hour sustained engagement.
5. Assess whether any legitimate DoD review of avionics vendor documentation exists that may have provided the factual kernel for this distortion.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DISCLAIMER: This report is generated from synthetic demonstration data (Operation STEEL ECHO). All companies, individuals, and events described are entirely fictional and created solely for portfolio demonstration purposes.

SENTINEL — Influence Operations Detection Engine — DEMONSTRATION ONLY"""


def load_seed_data(db: Session) -> dict:
    if db.query(Article).filter(Article.url == SEED_ARTICLES[0]["url"]).first():
        return {"status": "already_loaded", "message": "Seed data already loaded."}

    cluster = NarrativeCluster(**SEED_CLUSTER)
    db.add(cluster)
    db.flush()

    for art_data in SEED_ARTICLES:
        a = Article(**art_data)
        a.cluster_id = cluster.id
        db.add(a)

    for ttp_data in SEED_TTPS:
        db.add(TTPTag(cluster_id=cluster.id, **ttp_data))

    report = IntelReport(
        ref_number="SENTINEL-2026-001",
        title="Coordinated Adversary IO Campaign — Northgate Defense F-35 Narrative",
        subject="Multi-vector influence operation targeting US defense industry credibility",
        confidence_level="MODERATE",
        attribution="Consistent with state-directed IO playbooks (Russian/Chinese nexus TTPs)",
        full_text=SEED_REPORT_TEXT,
    )
    report.key_findings = [
        "RT English seeded narrative with anonymous sources and unverified documents (14:23)",
        "Fake expert 'Dr. Marcus Webb' deployed via Sputnik to manufacture credibility (14:31)",
        "Domestic Reddit amplification began within 41 minutes of seed article across 4 subreddits",
        "Campaign achieved full narrative lifecycle (seed → whistleblower → congressional response) in 2h25m",
        "Global Times framing explicitly targets allied confidence in US weapons exports",
    ]
    report.clusters.append(cluster)
    db.add(report)

    db.commit()
    return {
        "status": "loaded",
        "articles": len(SEED_ARTICLES),
        "clusters": 1,
        "ttps": len(SEED_TTPS),
        "reports": 1,
    }
