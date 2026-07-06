"""
seed_data.py — Pre-loaded demo opportunities and analyses.

These are realistic but fictional SAM.gov solicitations with pre-generated
Claude compliance matrices. They allow the app to be fully demonstrated
without hitting the SAM.gov API quota.
"""

from __future__ import annotations

DEMO_OPPORTUNITIES = [
    {
        "notice_id": "DEMO-001-CYBEROPS",
        "title": "Cybersecurity Operations Center (SOC) Support Services",
        "solicitation_number": "W52P1J-26-R-0042",
        "agency": "DEPT OF DEFENSE > DEPT OF THE ARMY > AMC > CECOM > CECOM CONTRACTING CENTER",
        "naics_code": "541519",
        "set_aside": "Total Small Business Set-Aside",
        "posted_date": "2026-04-15",
        "response_deadline": "2026-07-01T16:00:00",
        "ui_link": "https://sam.gov/opp/demo001",
        "description": (
            "The Communications-Electronics Command (CECOM) requires contractor support "
            "for a 24x7 Security Operations Center (SOC) at Aberdeen Proving Ground, MD. "
            "The contractor shall provide Tier 1/2/3 SOC analyst support, threat hunting, "
            "incident response, and SIEM management (Splunk). Personnel must hold active "
            "Secret clearances; TS/SCI preferred for senior analysts.\n\n"
            "Requirements include: CMMC Level 2 certification prior to award, DoD 8570 "
            "IAT Level II baseline certifications (Security+, CySA+, or equivalent) for "
            "all personnel, and demonstrated experience with the NIST 800-53 control "
            "framework. Past performance on at least two (2) federal SOC contracts of "
            "similar scope required. Period of performance is one base year plus four "
            "option years. Estimated value $12M–$18M total.\n\n"
            "Evaluation factors: Technical approach (40%), Past performance (30%), "
            "Price (30%). LPTA methodology will not be used."
        ),
    },
    {
        "notice_id": "DEMO-002-CLOUDSVC",
        "title": "Cloud Infrastructure Migration and Managed Services — DISA Impact Level 4",
        "solicitation_number": "FA8771-26-R-0017",
        "agency": "DEPT OF DEFENSE > DEPT OF THE AIR FORCE > AFMC > AFLCMC > AFLCMC PKO",
        "naics_code": "518210",
        "set_aside": "8(a) Set-Aside",
        "posted_date": "2026-05-02",
        "response_deadline": "2026-06-30T14:00:00",
        "ui_link": "https://sam.gov/opp/demo002",
        "description": (
            "The Air Force Life Cycle Management Center requires a contractor to migrate "
            "legacy on-premises applications to a FedRAMP High / DoD IL4 cloud environment "
            "and provide ongoing managed services. The target platform is an existing "
            "DoD-authorized Commercial Cloud Service Offering (CSO).\n\n"
            "Scope includes: cloud architecture design, data migration (est. 40TB), "
            "DevSecOps pipeline implementation, zero-trust network access (ZTNA) controls, "
            "and 24x7 infrastructure monitoring. Contractor must demonstrate FedRAMP High "
            "authorization or equivalent DoD cloud experience. CMMC Level 2 required. "
            "Secret facility clearance required; personnel clearances at Secret minimum.\n\n"
            "Period of performance: 6-month transition + 3-year managed services base + "
            "2 option years. Estimated value: $8M–$14M. "
            "Evaluation: Mission capability (50%), Past performance (25%), Price (25%)."
        ),
    },
    {
        "notice_id": "DEMO-003-SWDEV",
        "title": "Agile Software Development and DevSecOps Support — Army Logistics System",
        "solicitation_number": "W56KGU-26-R-0089",
        "agency": "DEPT OF DEFENSE > DEPT OF THE ARMY > AMC > TACOM > TACOM CONTRACTING CENTER",
        "naics_code": "541511",
        "set_aside": "Service-Disabled Veteran-Owned Small Business (SDVOSB)",
        "posted_date": "2026-05-20",
        "response_deadline": "2026-07-15T17:00:00",
        "ui_link": "https://sam.gov/opp/demo003",
        "description": (
            "TACOM requires agile software development support for the Global Combat Support "
            "System – Army (GCSS-Army), a SAP-based enterprise resource planning system "
            "used by 180,000+ users across the Army supply chain.\n\n"
            "The contractor shall provide full-stack developers (Java/Spring, Angular), "
            "DevSecOps engineers, database administrators (SAP HANA, Oracle), and Scrum "
            "Masters. All work performed in a classified environment; minimum Secret "
            "clearance required for all personnel. No CMMC requirement (development "
            "environment does not process CUI). Section 508 compliance required for all "
            "UI deliverables.\n\n"
            "Team size: approximately 25 FTEs. Period of performance: base year + 4 options. "
            "Estimated value: $22M–$30M over five years. "
            "Evaluation: Technical (35%), Management (25%), Past performance (20%), Price (20%). "
            "Key personnel positions: Program Manager, Lead Architect, DevSecOps Lead."
        ),
    },
]

DEMO_ANALYSES = [
    {
        "notice_id": "DEMO-001-CYBEROPS",
        "nist_800_171_required": False,
        "section_889_applies": True,
        "buy_american_act_applies": False,
        "pricing_model": None,
        "summary": (
            "The Army's CECOM is procuring 24/7 Security Operations Center analyst support "
            "at Aberdeen Proving Ground, covering threat hunting, incident response, and "
            "SIEM management over a 5-year ordering period. This is a total small business "
            "set-aside valued at $12–18M."
        ),
        "agency": "CECOM / Dept of the Army",
        "estimated_value": "$12M–$18M (base + 4 option years)",
        "period_of_performance": "1 base year + 4 option years (5 years total)",
        "place_of_performance": "Aberdeen Proving Ground, MD",
        "clearance_required": "Secret (TS/SCI preferred for senior roles)",
        "cmmc_level": "Level 2",
        "set_aside": "Total Small Business Set-Aside",
        "bottom_line": (
            "Strong opportunity for a small business with cleared SOC staff and CMMC Level 2 "
            "certification, but competition will be stiff — ensure you have documented federal "
            "SOC past performance before bidding."
        ),
        "key_requirements": [
            {"requirement": "24x7 SOC analyst coverage at Tier 1, 2, and 3", "category": "Technical"},
            {"requirement": "SIEM management experience with Splunk", "category": "Technical"},
            {"requirement": "Active Secret clearances for all personnel (TS/SCI preferred for seniors)", "category": "Personnel"},
            {"requirement": "CMMC Level 2 certification required prior to award", "category": "Compliance"},
            {"requirement": "DoD 8570 IAT Level II certification (Security+, CySA+, or equivalent) for all staff", "category": "Personnel"},
            {"requirement": "NIST 800-53 control framework implementation experience", "category": "Compliance"},
            {"requirement": "Minimum two (2) federal SOC past performance references of similar scope", "category": "Past Performance"},
        ],
        "evaluation_criteria": [
            {"criterion": "Technical approach", "weight": "40%"},
            {"criterion": "Past performance", "weight": "30%"},
            {"criterion": "Price", "weight": "30%"},
        ],
        "compliance_flags": [
            {"flag": "CMMC Level 2 certification required before award — begin assessment now if not certified", "severity": "High"},
            {"flag": "Secret clearance facility and personnel clearances required — verify cleared staff availability", "severity": "High"},
            {"flag": "DoD 8570 IAT Level II mandatory for all SOC personnel — audit team certifications", "severity": "Medium"},
            {"flag": "Two federal SOC past performance references required — confirm eligibility before investing in proposal", "severity": "Medium"},
        ],
        "capability_bullets": [
            "Proven 24x7 SOC operations supporting federal/DoD customers with demonstrated Splunk SIEM expertise",
            "Cleared workforce with active Secret and TS/SCI clearances, ready for immediate deployment",
            "CMMC Level 2 certified organization with documented NIST 800-53 implementation experience",
            "Established threat hunting and incident response playbooks aligned to MITRE ATT&CK framework",
            "Past performance on federal SOC contracts of similar scale and complexity",
        ],
    },
    {
        "notice_id": "DEMO-002-CLOUDSVC",
        "nist_800_171_required": False,
        "section_889_applies": True,
        "buy_american_act_applies": False,
        "pricing_model": None,
        "summary": (
            "The Air Force is seeking an 8(a) firm to migrate legacy applications to a "
            "FedRAMP High / DoD IL4 cloud environment and provide ongoing managed services "
            "over a ~4.5-year period. Migration involves approximately 40TB of data and "
            "requires zero-trust network architecture implementation."
        ),
        "agency": "AFLCMC / Dept of the Air Force",
        "estimated_value": "$8M–$14M",
        "period_of_performance": "6-month transition + 3-year base + 2 option years",
        "place_of_performance": "Not stated (likely remote/contractor facility)",
        "clearance_required": "Secret (facility + personnel)",
        "cmmc_level": "Level 2",
        "set_aside": "8(a) Set-Aside",
        "bottom_line": (
            "Excellent fit for a certified 8(a) cloud firm with DoD IL4 credentials, but "
            "requires FedRAMP High or equivalent authorization — confirm this before pursuing."
        ),
        "key_requirements": [
            {"requirement": "Migration of legacy on-premises applications to DoD IL4 cloud environment", "category": "Technical"},
            {"requirement": "FedRAMP High authorization or demonstrated equivalent DoD cloud experience", "category": "Compliance"},
            {"requirement": "DevSecOps pipeline implementation with CI/CD and SAST/DAST tooling", "category": "Technical"},
            {"requirement": "Zero-trust network access (ZTNA) architecture design and implementation", "category": "Technical"},
            {"requirement": "Data migration of approximately 40TB with integrity validation", "category": "Technical"},
            {"requirement": "CMMC Level 2 certification required", "category": "Compliance"},
            {"requirement": "24x7 infrastructure monitoring post-migration", "category": "Technical"},
            {"requirement": "Secret facility clearance with Secret-cleared personnel", "category": "Personnel"},
        ],
        "evaluation_criteria": [
            {"criterion": "Mission capability (technical approach)", "weight": "50%"},
            {"criterion": "Past performance", "weight": "25%"},
            {"criterion": "Price", "weight": "25%"},
        ],
        "compliance_flags": [
            {"flag": "FedRAMP High authorization or DoD IL4 experience is a hard requirement — disqualifying if absent", "severity": "High"},
            {"flag": "8(a) set-aside — must be SBA-certified 8(a) to bid", "severity": "High"},
            {"flag": "CMMC Level 2 required — verify certification status", "severity": "High"},
            {"flag": "Secret facility clearance required — confirm FCL status before bid decision", "severity": "Medium"},
            {"flag": "Zero-trust architecture is a DoD mandate under NDAA — must demonstrate current ZTNA capability", "severity": "Medium"},
        ],
        "capability_bullets": [
            "SBA-certified 8(a) firm with active Secret facility clearance and cleared cloud engineering team",
            "FedRAMP High authorized cloud migration experience with DoD IL4 environments",
            "Zero-trust network access implementation aligned to CISA and DoD ZTNA reference architectures",
            "Proven DevSecOps pipeline delivery (GitLab CI, Anchore, OWASP ZAP) on federal programs",
            "Large-scale data migration track record with automated integrity validation and rollback procedures",
        ],
    },
    {
        "notice_id": "DEMO-003-SWDEV",
        "nist_800_171_required": False,
        "section_889_applies": False,
        "buy_american_act_applies": False,
        "pricing_model": None,
        "summary": (
            "TACOM needs an SDVOSB firm to provide approximately 25 FTEs of agile software "
            "development and DevSecOps support for GCSS-Army, the Army's SAP-based enterprise "
            "logistics system used by 180,000+ users. The 5-year contract is valued at "
            "$22–30M with no CMMC requirement."
        ),
        "agency": "TACOM / Dept of the Army",
        "estimated_value": "$22M–$30M (base + 4 option years)",
        "period_of_performance": "1 base year + 4 option years (5 years total)",
        "place_of_performance": "Not stated",
        "clearance_required": "Secret",
        "cmmc_level": None,
        "set_aside": "Service-Disabled Veteran-Owned Small Business (SDVOSB)",
        "bottom_line": (
            "High-value SDVOSB opportunity — no CMMC requirement lowers the barrier, but "
            "SAP HANA + GCSS-Army domain experience is rare and will be the differentiator."
        ),
        "key_requirements": [
            {"requirement": "Full-stack Java/Spring and Angular development experience", "category": "Technical"},
            {"requirement": "SAP HANA and Oracle database administration capability", "category": "Technical"},
            {"requirement": "DevSecOps pipeline engineering (CI/CD, SAST, container security)", "category": "Technical"},
            {"requirement": "Certified Scrum Masters for all development teams", "category": "Personnel"},
            {"requirement": "Secret clearances for all personnel — no exceptions", "category": "Personnel"},
            {"requirement": "Section 508 compliance for all UI deliverables", "category": "Compliance"},
            {"requirement": "Key personnel: Program Manager, Lead Architect, DevSecOps Lead", "category": "Personnel"},
            {"requirement": "25 FTE team capacity with ability to surge", "category": "Technical"},
        ],
        "evaluation_criteria": [
            {"criterion": "Technical approach", "weight": "35%"},
            {"criterion": "Management approach", "weight": "25%"},
            {"criterion": "Past performance", "weight": "20%"},
            {"criterion": "Price", "weight": "20%"},
        ],
        "compliance_flags": [
            {"flag": "SDVOSB set-aside — must be VA-verified SDVOSB to bid", "severity": "High"},
            {"flag": "Secret clearances required for all ~25 FTEs — model clearance timeline into staffing plan", "severity": "High"},
            {"flag": "Section 508 compliance required for all UI deliverables — include in test plan", "severity": "Medium"},
            {"flag": "Key personnel positions require specific approval — identify named candidates early", "severity": "Medium"},
            {"flag": "No CMMC requirement — lower barrier to entry than typical DoD software work", "severity": "Low"},
        ],
        "capability_bullets": [
            "VA-verified SDVOSB with proven delivery on large-scale DoD enterprise software programs",
            "SAP HANA and enterprise ERP modernization experience with cleared development teams",
            "Agile/SAFe delivery methodology with certified Scrum Masters and documented sprint velocity metrics",
            "DevSecOps pipeline capability (GitLab CI/CD, SonarQube, Twistlock) aligned to Army DevSecOps Reference Design",
            "Section 508 testing integrated into QA process with automated accessibility scanning",
            "25+ cleared FTE bench capacity with surge capability through established teaming agreements",
        ],
    },
]
