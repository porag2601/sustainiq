"""Simplified CSRD / ESRS data checklist and readiness calculation.

Not the full ESRS datapoint list (that has over 1,000 datapoints). These are
12 key data points an SME needs for the environmental standards relevant to
this tool. References follow ESRS Set 1 (Delegated Regulation (EU) 2023/2772).
The EU is simplifying the ESRS (Omnibus package), so numbering and scope may
change; the UI and PDF say so.

This module has no imports from app.models, so models.py can import from it
without a circular import.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

Standard = Literal["ESRS 2", "E1", "E2", "E3", "E5"]


class ChecklistItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    standard: Standard
    reference: str  # disclosure requirement in ESRS Set 1
    title: str
    hint: str       # plain-language explanation for the form


CHECKLIST: tuple[ChecklistItem, ...] = tuple(
    ChecklistItem(id=i, standard=s, reference=r, title=t, hint=h)
    for i, s, r, t, h in [
        ("esrs2_materiality", "ESRS 2", "IRO-1", "Double materiality assessment",
         "Which sustainability topics are material, from an impact and a financial view."),
        ("e1_policies", "E1", "E1-2", "Climate policies",
         "Written policies on climate mitigation, adaptation and energy."),
        ("e1_transition_plan", "E1", "E1-1", "Climate transition plan",
         "Plan for aligning the business with the 1.5 °C goal."),
        ("e1_targets", "E1", "E1-4", "GHG reduction targets",
         "Measurable targets, e.g. -40 % Scope 1+2 by 2030 against a base year."),
        ("e1_energy_mix", "E1", "E1-5", "Energy consumption and mix",
         "Total energy use, split into fossil, nuclear and renewable sources."),
        ("e1_scope12", "E1", "E1-6", "Scope 1 and 2 GHG emissions",
         "Scope 2 both location-based and market-based."),
        ("e1_scope3", "E1", "E1-6", "Scope 3 GHG emissions",
         "Significant value-chain categories, e.g. purchased goods, transport."),
        ("e2_pollutants", "E2", "E2-4", "Pollutant emissions to air, water and soil",
         "Amounts of pollutants, e.g. those listed in the E-PRTR regulation."),
        ("e2_substances", "E2", "E2-5", "Substances of concern",
         "Substances of (very high) concern the company produces or uses."),
        ("e3_water", "E3", "E3-4", "Water consumption",
         "Total water consumption in m³, including areas at water risk."),
        ("e5_inflows", "E5", "E5-4", "Resource inflows",
         "Materials used, with the share of recycled and renewable input."),
        ("e5_waste", "E5", "E5-5", "Resource outflows and waste",
         "Total and hazardous waste, share recycled or disposed."),
    ]
)

CHECKLIST_IDS: frozenset[str] = frozenset(item.id for item in CHECKLIST)
_BY_ID = {item.id: item for item in CHECKLIST}


class StandardReadiness(BaseModel):
    standard: Standard
    available: int
    total: int


class CsrdReadiness(BaseModel):
    """How much of the checklist data the company already has (calculated in Python)."""

    available: int
    total: int
    percent: float
    standards: list[StandardReadiness]
    missing_ids: list[str]


def compute_readiness(available_ids: list[str]) -> CsrdReadiness:
    available = set(available_ids) & CHECKLIST_IDS

    standards: list[StandardReadiness] = []
    for standard in ("ESRS 2", "E1", "E2", "E3", "E5"):
        items = [item for item in CHECKLIST if item.standard == standard]
        standards.append(StandardReadiness(
            standard=standard,
            available=sum(item.id in available for item in items),
            total=len(items),
        ))

    return CsrdReadiness(
        available=len(available),
        total=len(CHECKLIST),
        percent=round(len(available) / len(CHECKLIST) * 100, 1),
        standards=standards,
        # Checklist order (not set order), so the output is stable and testable.
        missing_ids=[item.id for item in CHECKLIST if item.id not in available],
    )


def item_titles(ids: list[str]) -> list[str]:
    """'e1_scope3' -> 'E1-6 Scope 3 GHG emissions' (for the Claude prompt and PDF)."""
    return [f"{_BY_ID[i].reference} {_BY_ID[i].title}" for i in ids if i in _BY_ID]
