"""PDF report for one assessment, built with ReportLab.

ReportLab builds a PDF from a list of "flowables" (paragraphs, tables,
spacers) that it lays out on pages automatically, adding page breaks.
build_pdf() only needs the input and the result, not the database,
so it is easy to test.
"""

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.csrd import item_titles
from app.models import AnalysisResponse, AssessmentInput

# Readable names; the same labels as frontend/src/metrics.js.
METRIC_LABELS = {
    "energy_kwh_per_fte": "Energy per employee",
    "scope12_t_per_fte": "Scope 1+2 emissions per employee",
    "waste_t_per_fte": "Waste per employee",
    "water_m3_per_fte": "Water per employee",
    "renewable_share_pct": "Renewable energy share",
    "recycling_rate_pct": "Recycling rate",
}
SECTOR_LABELS = {
    "manufacturing": "Manufacturing",
    "logistics_transport": "Logistics & Transport",
    "food_retail": "Food & Retail",
    "construction": "Construction",
    "other": "Other",
}
STATUS = {
    "better": ("Better", colors.HexColor("#047857")),
    "on_par": ("On par", colors.HexColor("#b45309")),
    "worse": ("Worse", colors.HexColor("#b91c1c")),
}
ESRS_NAMES = {"ESRS 2": "ESRS 2 General disclosures", "E1": "ESRS E1 Climate", "E2": "ESRS E2 Pollution", "E3": "ESRS E3 Water", "E5": "ESRS E5 Resources"}

GREEN = colors.HexColor("#047857")
GREY = colors.HexColor("#64748b")

_styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=_styles["Title"], alignment=0, textColor=GREEN)
H2 = ParagraphStyle("H2", parent=_styles["Heading2"], spaceBefore=12)
BODY = _styles["BodyText"]
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=8, leading=10, textColor=GREY)
CELL = ParagraphStyle("Cell", parent=BODY, fontSize=8.5, leading=10.5)


def _p(text: str, style: ParagraphStyle = BODY) -> Paragraph:
    """Paragraph from plain text.

    ReportLab reads <, > and & as formatting markup. User input and AI text
    are escaped, so a company called "A & B <GmbH>" cannot break the PDF.
    """
    return Paragraph(escape(text), style)


def _status_text(score: float) -> str:
    # Same +/- 5 band around 50 as ON_PAR_BAND in scoring.py.
    if score > 55:
        return "Better than the sector benchmark"
    if score < 45:
        return "Below the sector benchmark"
    return "Around the sector benchmark"


def _metric_table(result: AnalysisResponse) -> Table:
    header = ["Metric", "Company", "Benchmark*", "Diff.", "Score", "Status"]
    rows = [header]
    for m in result.score.metrics:
        label, color = STATUS[m.status]
        rows.append([
            # Markup built by us (<br/>, <font>), text parts escaped.
            Paragraph(f"{escape(METRIC_LABELS.get(m.key, m.key))}<br/>"
                      f"<font size=7 color='#64748b'>{escape(m.unit)}</font>", CELL),
            f"{m.value:,.1f}",
            f"{m.benchmark_value:,.1f}",
            f"{m.diff_pct:+.1f} %",
            f"{m.score:.1f}",
            Paragraph(f"<font color='{color.hexval()}'>{label}</font>", CELL),
        ])

    table = Table(rows, colWidths=[5.4 * cm, 2.5 * cm, 2.5 * cm, 2 * cm, 1.6 * cm, 3 * cm], repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LINEBELOW", (0, 0), (-1, 0), 1, GREY),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
        ("ALIGN", (1, 0), (4, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _csrd_section(result: AnalysisResponse) -> list:
    readiness = result.csrd
    if readiness is None:  # saved before the checklist existed
        return []

    rows = [["Standard", "Available"]] + [
        [ESRS_NAMES.get(s.standard, s.standard), f"{s.available} / {s.total}"] for s in readiness.standards
    ]
    table = Table(rows, colWidths=[6 * cm, 3 * cm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LINEBELOW", (0, 0), (-1, 0), 1, GREY),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))

    story = [
        Paragraph("CSRD data readiness", H2),
        Paragraph(f"<b>{readiness.available} of {readiness.total}</b> key ESRS data points available "
                  f"({readiness.percent:.1f} %).", BODY),
        Spacer(1, 4),
        table,
    ]
    missing = item_titles(readiness.missing_ids)
    if missing:
        story += [Spacer(1, 6), Paragraph("<b>Missing data points:</b>", BODY)]
        story += [_p(f"• {title}") for title in missing]
    story.append(_p("Simplified checklist of key data points, not the full ESRS. References follow "
                    "ESRS Set 1 (2023); the EU is simplifying the ESRS (Omnibus), so numbering and "
                    "scope may change.", SMALL))
    return story


def _ai_section(result: AnalysisResponse) -> list:
    analysis = result.ai_analysis
    if analysis is None:
        return [
            Paragraph("AI analysis", H2),
            _p(f"The AI analysis was not available: {result.ai_error or 'unknown error'} "
               "The score and benchmark comparison above do not depend on AI and are complete."),
        ]

    story = [Paragraph("Summary", H2), _p(analysis.summary)]

    story.append(Paragraph("Recommendations", H2))
    for i, rec in enumerate(analysis.recommendations, start=1):
        meta = f"{ESRS_NAMES.get(rec.esrs_standard, rec.esrs_standard)} · {rec.priority} priority"
        if rec.funding_hint:
            meta += f" · Funding: {rec.funding_hint}"
        story += [
            Paragraph(f"<b>{i}. {escape(rec.title)}</b>", BODY),
            _p(rec.description),
            _p(meta, SMALL),
            Spacer(1, 4),
        ]

    story.append(Paragraph("CSRD / ESRS gaps", H2))
    for gap in analysis.csrd_gaps:
        story += [
            Paragraph(f"<b>{escape(ESRS_NAMES.get(gap.esrs_standard, gap.esrs_standard))}:</b> "
                      f"{escape(gap.gap)}", BODY),
            Paragraph(f"<i>Next step:</i> {escape(gap.action)}", BODY),
            Spacer(1, 4),
        ]

    story.append(Paragraph("Quick wins (next 3 months)", H2))
    story += [_p(f"• {win}") for win in analysis.quick_wins]
    story += [Spacer(1, 6), _p("Text sections generated by AI (Claude) from the calculated figures. "
                               "Please review before using them in official reports.", SMALL)]
    return story


def _footer(canvas, doc) -> None:
    """Drawn on every page: small footer with page number."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(2 * cm, 1.2 * cm, "SustainIQ · indicative assessment, not an audited CSRD report")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(data: AssessmentInput, result: AnalysisResponse) -> bytes:
    """Return the complete PDF file as bytes (kept in memory, never on disk)."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"SustainIQ report: {data.company_name}", author="SustainIQ",
    )

    date = result.created_at.strftime("%d.%m.%Y %H:%M UTC") if result.created_at else "not saved"
    number = f"#{result.id}" if result.id else "-"
    score = result.score.overall_score

    sources = sorted({m.benchmark_source for m in result.score.metrics})
    any_indicative = any(m.benchmark_indicative for m in result.score.metrics)

    story = [
        Paragraph("SustainIQ Sustainability Report", H1),
        _p(f"{data.company_name} · {SECTOR_LABELS.get(data.sector.value, data.sector.value)} · "
           f"{data.employees_fte:g} FTE"),
        _p(f"Assessment {number} · {date}", SMALL),
        Spacer(1, 12),
        Paragraph(f"Overall score: <b>{score:.1f} / 100</b> ({_status_text(score)})", BODY),
        _p("50 = exactly at the sector benchmark.", SMALL),
        Paragraph("Benchmark comparison", H2),
        _metric_table(result),
        Spacer(1, 6),
    ]
    if any_indicative:
        story.append(_p("* Benchmarks are indicative estimates, not official statistics.", SMALL))
    story += [_p(f"Source: {source}", SMALL) for source in sources]
    story += _csrd_section(result)
    story += _ai_section(result)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
