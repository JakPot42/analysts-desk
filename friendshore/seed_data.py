"""
seed_data.py -- Demo supply chain data for FriendShore.

A fictional AESA radar prime contractor's Tier 1-3 supply chain. Every company
name here is invented and marked "(fictional)"; none refers to a real company,
and no certification or qualification is claimed for any of them.
"""

from __future__ import annotations

DEMO_ANALYSES = [
    {
        "name": "AESA Radar System: Example Prime Co. BOM Analysis (fictional example)",
        "source_text": "See demo: synthetic data, fictional companies",
        "overall_risk_score": 72,
        "bottom_line": (
            "Critical dependency on two Chinese suppliers in this fictional example (Dogwood "
            "Compound Semi and Hazel Memory). Dogwood is a single point of failure for GaAs "
            "wafer supply. Second-sourcing the wafer step is the first recommended action."
        ),
        "risk_summary": (
            "Three high-risk suppliers identified in Tier 2 and Tier 3. Chinese-sourced GaAs "
            "wafers and NAND flash represent the most critical exposures. Ginkgo Capacitors "
            "supplies two Tier-1 suppliers, a secondary concentration risk."
        ),
        "single_points_of_failure": ["Dogwood Compound Semi (fictional)"],
        "alternative_suggestions": [
            {
                "original_supplier": "Dogwood Compound Semi (fictional)",
                "component": "GaAs wafers",
                "alternatives": [
                    {
                        "company": "Kestrel Wafer Co. (fictional)",
                        "country": "USA",
                        "rationale": "Domestic GaAs wafer source in this example; capacity and lead times would need checking."
                    },
                    {
                        "company": "Larch Epitaxy (fictional)",
                        "country": "USA",
                        "rationale": "A second domestic source in this example, so the wafer step no longer depends on one supplier."
                    },
                    {
                        "company": "Maple Epiwafer (fictional)",
                        "country": "UK",
                        "rationale": "Allied-country source in this example; export terms would need checking."
                    }
                ]
            },
            {
                "original_supplier": "Hazel Memory (fictional)",
                "component": "NAND flash",
                "alternatives": [
                    {
                        "company": "Nutmeg Flash (fictional)",
                        "country": "USA",
                        "rationale": "Domestic NAND source in this example."
                    },
                    {
                        "company": "Olive Storage (fictional)",
                        "country": "USA",
                        "rationale": "US-made NAND in this example, for a contract that requires US origin."
                    },
                    {
                        "company": "Poplar Memory (fictional)",
                        "country": "Japan",
                        "rationale": "Allied-country NAND source in this example."
                    }
                ]
            }
        ],
        "nodes": [
            {"name": "Example Prime Co. (fictional)",      "country": "USA",         "tier": 0, "component": None,                   "is_focal": True},
            {"name": "Alder RF Modules (fictional)",       "country": "USA",         "tier": 1, "component": "RF/microwave modules", "is_focal": False},
            {"name": "Birch Antenna Works (fictional)",    "country": "UK",          "tier": 1, "component": "Antenna arrays",       "is_focal": False},
            {"name": "Cedar Signal Systems (fictional)",   "country": "Japan",       "tier": 1, "component": "Signal processors",    "is_focal": False},
            {"name": "Dogwood Compound Semi (fictional)",  "country": "China",       "tier": 2, "component": "GaAs wafers",          "is_focal": False},
            {"name": "Elm Logic Devices (fictional)",      "country": "USA",         "tier": 2, "component": "FPGAs",                "is_focal": False},
            {"name": "Fir Power Electronics (fictional)",  "country": "Germany",     "tier": 2, "component": "Power modules",        "is_focal": False},
            {"name": "Ginkgo Capacitors (fictional)",      "country": "South Korea", "tier": 2, "component": "MLCC capacitors",      "is_focal": False},
            {"name": "Hazel Memory (fictional)",           "country": "China",       "tier": 2, "component": "NAND flash",           "is_focal": False},
            {"name": "Ironbark Rare Earths (fictional)",   "country": "USA",         "tier": 3, "component": "Rare earth metals",    "is_focal": False},
            {"name": "Jacaranda Cobalt (fictional)",       "country": "China",       "tier": 3, "component": "Cobalt",               "is_focal": False},
        ],
        "edges": [
            {"supplier": "Alder RF Modules (fictional)",      "customer": "Example Prime Co. (fictional)",     "component": "RF/microwave modules"},
            {"supplier": "Birch Antenna Works (fictional)",   "customer": "Example Prime Co. (fictional)",     "component": "Antenna arrays"},
            {"supplier": "Cedar Signal Systems (fictional)",  "customer": "Example Prime Co. (fictional)",     "component": "Signal processors"},
            {"supplier": "Dogwood Compound Semi (fictional)", "customer": "Alder RF Modules (fictional)",      "component": "GaAs wafers"},
            {"supplier": "Elm Logic Devices (fictional)",     "customer": "Alder RF Modules (fictional)",      "component": "FPGAs"},
            {"supplier": "Fir Power Electronics (fictional)", "customer": "Birch Antenna Works (fictional)",   "component": "Power modules"},
            {"supplier": "Ginkgo Capacitors (fictional)",     "customer": "Birch Antenna Works (fictional)",   "component": "MLCC capacitors"},
            {"supplier": "Ginkgo Capacitors (fictional)",     "customer": "Cedar Signal Systems (fictional)",  "component": "MLCC capacitors"},
            {"supplier": "Hazel Memory (fictional)",          "customer": "Cedar Signal Systems (fictional)",  "component": "NAND flash"},
            {"supplier": "Ironbark Rare Earths (fictional)",  "customer": "Dogwood Compound Semi (fictional)", "component": "Rare earth metals"},
            {"supplier": "Jacaranda Cobalt (fictional)",      "customer": "Dogwood Compound Semi (fictional)", "component": "Cobalt"},
        ],
    }
]
