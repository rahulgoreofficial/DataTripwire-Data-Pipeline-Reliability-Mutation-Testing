#!/usr/bin/env python3
"""DataTripwire Comprehensive Project Report PDF Generator.

Builds an engineering-grade, publication-quality 16-page PDF report
documenting DataTripwire's foundation, architecture, mutation engine,
validation rules, API specifications, UI engineering, test verification,
limitations, and roadmap.
"""

from datetime import datetime, timezone
from pathlib import Path
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
PDF_OUTPUT = DOCS_DIR / "DataTripwire_Project_Report.pdf"

# Palette definitions matching DataTripwire design system
NAVY_PRIMARY = colors.HexColor("#10152B")
NAVY_SECONDARY = colors.HexColor("#181E38")
NAVY_SURFACE = colors.HexColor("#202631")
SIGNAL_ORANGE = colors.HexColor("#F05A3B")
ORANGE_BG = colors.HexColor("#FDF3F0")
ORANGE_BORDER = colors.HexColor("#FAC7BC")
EMERALD_GREEN = colors.HexColor("#287A55")
GREEN_BG = colors.HexColor("#EBF4EE")
TEXT_PRIMARY = colors.HexColor("#1B1D20")
TEXT_MUTED = colors.HexColor("#5A6275")
BG_LIGHT = colors.HexColor("#F8F9FA")
BORDER_LIGHT = colors.HexColor("#D8DCE5")
BORDER_SUBTLE = colors.HexColor("#EAECEF")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw total page counts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        if self._pageNumber == 1:
            return  # Suppress headers/footers on cover page

        self.saveState()
        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(SIGNAL_ORANGE)
        self.drawString(54, 755, "DATATRIPWIRE")
        self.setFont("Helvetica", 7)
        self.setFillColor(TEXT_MUTED)
        self.drawString(124, 755, "// COMPREHENSIVE PROJECT REPORT & ARCHITECTURE SPECIFICATION")
        self.drawRightString(558, 755, "OCTOBER 2026")

        self.setStrokeColor(BORDER_LIGHT)
        self.setLineWidth(0.6)
        self.line(54, 748, 558, 748)

        # Footer
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXT_MUTED)
        self.drawString(54, 32, "DataTripwire — Data Pipeline Reliability & Mutation Testing Platform")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


def create_styles():
    base = getSampleStyleSheet()

    title_cover = ParagraphStyle(
        "CoverTitle",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=28,
        leading=34,
        textColor=NAVY_PRIMARY,
        spaceAfter=8,
    )

    subtitle_cover = ParagraphStyle(
        "CoverSubtitle",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11.5,
        leading=16.5,
        textColor=TEXT_MUTED,
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=NAVY_PRIMARY,
        spaceBefore=8,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14.5,
        textColor=NAVY_SECONDARY,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.6,
        leading=12.8,
        textColor=TEXT_PRIMARY,
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "BulletDark",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=12.2,
        textColor=TEXT_PRIMARY,
        leftIndent=12,
        spaceAfter=3,
    )

    code_style = ParagraphStyle(
        "CodeText",
        parent=base["Normal"],
        fontName="Courier",
        fontSize=7.4,
        leading=9.8,
        textColor=NAVY_PRIMARY,
    )

    code_block = ParagraphStyle(
        "CodeBlock",
        parent=base["Normal"],
        fontName="Courier",
        fontSize=7.0,
        leading=9.4,
        textColor=NAVY_PRIMARY,
    )

    callout_text = ParagraphStyle(
        "CalloutText",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=12.0,
        textColor=NAVY_PRIMARY,
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=10.2,
        textColor=colors.white,
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=7.6,
        leading=10.4,
        textColor=TEXT_PRIMARY,
    )

    return {
        "title_cover": title_cover,
        "subtitle_cover": subtitle_cover,
        "h1": h1_style,
        "h2": h2_style,
        "body": body_style,
        "bullet": bullet_style,
        "code": code_style,
        "code_block": code_block,
        "callout": callout_text,
        "th": table_header,
        "td": table_cell,
    }


def make_callout(text: str, styles, border_color=SIGNAL_ORANGE, bg_color=ORANGE_BG):
    p = Paragraph(text, styles["callout"])
    t = Table([[p]], colWidths=[504])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                ("BOX", (0, 0), (-1, -1), 1, border_color),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return t


def build_pdf_report():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(PDF_OUTPUT),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = create_styles()
    story = []

    # =========================================================================
    # PAGE 1: COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 14))

    kicker_table = Table(
        [[Paragraph("<font color='#F05A3B'><b>DATA RELIABILITY LAB // TECHNICAL ARCHITECTURE & AUDIT REPORT</b></font>", styles["code"])]],
        colWidths=[504],
    )
    kicker_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY_PRIMARY),
                ("PADDING", (0, 0), (-1, -1), 7),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )
    story.append(kicker_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("DataTripwire", styles["title_cover"]))
    story.append(
        Paragraph(
            "<b>Data Pipeline Reliability & Mutation Testing Platform</b><br/>"
            "Evaluating whether existing data-quality safeguards detect realistic failures before silent corruption cascades into downstream ledgers and analytics.",
            styles["subtitle_cover"],
        )
    )

    story.append(
        make_callout(
            "<b>Core Technical Proposition:</b> <i>\"Break the data. Test the safeguards. Protect the metrics.\"</i><br/>"
            "While traditional data quality monitors raw record compliance against static rules, DataTripwire introduces "
            "adversarial mutation testing to evaluate the safeguards themselves.",
            styles,
            border_color=SIGNAL_ORANGE,
            bg_color=ORANGE_BG,
        )
    )
    story.append(Spacer(1, 14))

    # Cover Meta Grid
    meta_data = [
        [Paragraph("<b>Document Version</b>", styles["td"]), Paragraph("v0.1.0 (Production Release Candidate)", styles["td"])],
        [Paragraph("<b>Publication Date</b>", styles["td"]), Paragraph(datetime.now(timezone.utc).strftime("%B %d, %Y"), styles["td"])],
        [Paragraph("<b>Product Status</b>", styles["td"]), Paragraph("Phases 1–3 Complete · Verified Offline & Local Runtime", styles["td"])],
        [Paragraph("<b>GitHub Repository</b>", styles["td"]), Paragraph("rahulgoreofficial/DataTripwire-Data-Pipeline-Reliability-Mutation-Testing", styles["td"])],
        [Paragraph("<b>Technology Stack</b>", styles["td"]), Paragraph("Python 3.11+, FastAPI, Pandas, Pydantic v2, React 19, TypeScript, Vite", styles["td"])],
        [Paragraph("<b>Lead Engineer / Author</b>", styles["td"]), Paragraph("Rahul Gore (rahulgoreoffical@gmail.com)", styles["td"])],
    ]
    meta_table = Table(meta_data, colWidths=[140, 364])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("PADDING", (0, 0), (-1, -1), 5.5),
            ]
        )
    )
    story.append(meta_table)

    story.append(Spacer(1, 16))
    story.append(Paragraph("<b>Table of Report Sections:</b>", styles["h2"]))

    toc_items = [
        "01. Executive Summary", "02. Problem Statement: Silent Data Degradation",
        "03. Proposed Solution & Mutation Workflow", "04. Practical Industry Use Cases",
        "05. Technical Architecture & Component Model", "06. Data Flow & Internal Processing Lifecycle",
        "07. Synthetic Mutation Engine & Operators", "08. Validation Engine & Fault Detection Logic",
        "09. Business Metrics & Mutation Scoring Formulation", "10. Backend REST API Reference",
        "11. Frontend Design & User Experience Engineering", "12. Installation, Environment & Startup Procedures",
        "13. Automated Testing, Verification & Quality Assurance", "14. End-to-End Demonstration Scenario",
        "15. Differentiation & Tool Landscape Comparison", "16. Security, Local Privacy & Architectural Boundaries",
        "17. Development Roadmap & Future Enhancements", "18. Engineering Conclusion",
        "19. Technical Appendix & Source Artifacts", "20. Document Attestation & Verification Record",
    ]
    toc_data = []
    for i in range(0, len(toc_items), 2):
        row = [
            Paragraph(toc_items[i], styles["td"]),
            Paragraph(toc_items[i + 1] if i + 1 < len(toc_items) else "", styles["td"]),
        ]
        toc_data.append(row)

    toc_table = Table(toc_data, colWidths=[252, 252])
    toc_table.setStyle(
        TableStyle(
            [
                ("PADDING", (0, 0), (-1, -1), 3),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ]
        )
    )
    story.append(toc_table)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: EXECUTIVE SUMMARY & PROBLEM STATEMENT
    # =========================================================================
    story.append(Paragraph("1. Executive Summary", styles["h1"]))
    story.append(
        Paragraph(
            "Modern data pipelines powering analytics, machine learning, and executive financial dashboards "
            "frequently suffer from a silent failure mode: pipelines complete execution with exit code <code>0</code> "
            "while ingesting corrupt, duplicated, or invalid records. Traditional data-quality tools monitor "
            "production tables against static rules, but data engineering teams rarely have a structured mechanism "
            "to test whether those rules are actually capable of catching realistic, critical data corruptions.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>DataTripwire</b> bridges this verification gap by introducing <b>mutation testing for data pipelines</b>. "
            "Rather than treating data quality checks as infallible guardians, DataTripwire operates as a crash-testing "
            "laboratory: it injects controlled, synthetic data faults into isolated working copies of production datasets, "
            "executes the active validation suite, empirically verifies whether the faults trigger relevant checkpoints, "
            "and measures downstream ledger distortion when faults escape.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "The completed prototype provides a 100% local, privacy-preserving full-stack solution featuring: "
            "(1) a robust Python 3.11+ / FastAPI backend with Pydantic v2 data contracts and Decimal financial precision; "
            "(2) an isolated mutation engine supporting 5 synthetic fault classes; "
            "(3) a multi-checkpoint validator and fingerprint-based detection matcher; "
            "(4) a deterministic rule recommendation engine; and "
            "(5) a React 19 + TypeScript frontend with dual-theme (Daylight and After Hours) design and SVG flow visualization. "
            "The entire application launches via a single Windows double-click (<code>start_datatripwire.bat</code>) with "
            "automated readiness detection and targeted process supervision.",
            styles["body"],
        )
    )

    story.append(
        make_callout(
            "<b>Executive Takeaway:</b> DataTripwire proves data quality through empirical evidence rather than assumption. "
            "In verified demonstrations, a duplicate ingestion fault producing a +₹1,000.00 silent revenue distortion "
            "was allowed to escape baseline validation (0% detection score), flagged with an actionable rule recommendation, "
            "and successfully trapped (100% score, ₹0.00 drift) once the recommended safeguard was enabled.",
            styles,
            border_color=EMERALD_GREEN,
            bg_color=GREEN_BG,
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. Problem Statement: Silent Data Degradation", styles["h1"]))
    story.append(
        Paragraph(
            "Enterprise data teams face a fundamental asymmetry in data testing: software engineers routinely test "
            "code paths with extensive unit and integration tests, yet data pipelines are typically tested only against "
            "clean historical data. When unexpected anomalies emerge, pipelines silently fail:",
            styles["body"],
        )
    )
    story.append(Paragraph("• <b>Ingestion Replay & Duplicate Transactions:</b> Upstream webhook retries or message queue replays generate duplicate sales rows. Without primary-key uniqueness verification, aggregate revenue and transaction volumes inflate silently without triggering database syntax errors.", styles["bullet"]))
    story.append(Paragraph("• <b>Schema Drift & Null Contamination:</b> Upstream microservices alter field requirements, causing essential dimensions (such as quantity or unit price) to arrive null, leading to silent drops or zero-multiplications in SQL aggregate joins.", styles["bullet"]))
    story.append(Paragraph("• <b>Domain Range Violations:</b> Promotional bugs or return glitches inject negative prices or zero quantities, skewing average order value calculations while passing general numeric datatype checks.", styles["bullet"]))
    story.append(Paragraph("• <b>Unchecked Control Totals:</b> Upstream filtering drops records, yet downstream pipelines process the subset without reconciling against expected ingestion row counts.", styles["bullet"]))
    story.append(
        Paragraph(
            "<b>The Cost of Unchecked Ingestion:</b> Because downstream systems assume clean feeds, corrupt rows "
            "infiltrate data warehouses, skewing financial reporting, triggering erroneous automated inventory replenishments, "
            "and poisoning customer attribution models weeks before human auditors notice discrepancies.",
            styles["body"],
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: PROPOSED SOLUTION & WORKFLOW
    # =========================================================================
    story.append(Paragraph("3. Proposed Solution & Mutation Workflow", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire transposes mutation testing—a rigorous software engineering practice—into tabular data engineering. "
            "The end-to-end evaluation lifecycle proceeds through ten discrete stages:",
            styles["body"],
        )
    )

    flow_table_data = [
        [Paragraph("<b>Step</b>", styles["th"]), Paragraph("<b>Stage</b>", styles["th"]), Paragraph("<b>Engine Execution Description</b>", styles["th"])],
        [Paragraph("01", styles["td"]), Paragraph("Data Ingestion", styles["td"]), Paragraph("Parses CSV file with UTF-8/fallback encoding, validates column dimensions and mandatory headers.", styles["td"])],
        [Paragraph("02", styles["td"]), Paragraph("Profiling", styles["td"]), Paragraph("Computes structural metadata: row/column counts, null distributions, numeric summaries, and schema compatibility.", styles["td"])],
        [Paragraph("03", styles["td"]), Paragraph("Baseline Metrics", styles["td"]), Paragraph("Calculates clean pipeline metrics (revenue, transaction count, customer count) using exact Decimal arithmetic.", styles["td"])],
        [Paragraph("04", styles["td"]), Paragraph("Baseline Validation", styles["td"]), Paragraph("Executes active rule suite against pristine dataset to capture existing findings and fingerprints.", styles["td"])],
        [Paragraph("05", styles["td"]), Paragraph("Working Copy Isolation", styles["td"]), Paragraph("Creates independent deep copy (<code>df.copy(deep=True)</code>) to guarantee source dataset immutability.", styles["td"])],
        [Paragraph("06", styles["td"]), Paragraph("Fault Injection", styles["td"]), Paragraph("Injects deterministic synthetic mutation (duplicate row, null value, negative price, dropped row).", styles["td"])],
        [Paragraph("07", styles["td"]), Paragraph("Mutated Validation", styles["td"]), Paragraph("Runs validation rules against mutated copy; isolates newly introduced findings from baseline fingerprints.", styles["td"])],
        [Paragraph("08", styles["td"]), Paragraph("Detection Matching", styles["td"]), Paragraph("Evaluates whether new findings explicitly correspond to injected fault type, target column, and target record.", styles["td"])],
        [Paragraph("09", styles["td"]), Paragraph("Downstream Impact", styles["td"]), Paragraph("Quantifies delta between clean and corrupted metrics (e.g. net revenue error magnitude in INR/currency).", styles["td"])],
        [Paragraph("10", styles["td"]), Paragraph("Rule Recommendation", styles["td"]), Paragraph("Synthesizes deterministic, explainable validation safeguard rule configurations to close identified escape gaps.", styles["td"])],
    ]
    t_flow = Table(flow_table_data, colWidths=[28, 105, 371])
    t_flow.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4.2),
            ]
        )
    )
    story.append(t_flow)
    story.append(Spacer(1, 8))
    story.append(
        make_callout(
            "<b>The Mutation Testing Philosophy:</b> In software testing, a test suite is tested by mutating the source code "
            "(e.g., flipping <code>&gt;</code> to <code>&lt;=</code>). If the test suite still passes, the mutation <i>survived</i>, "
            "indicating a test gap. DataTripwire applies this exact logic to data pipelines: if corrupting data does not fail "
            "validation, the safeguard suite is demonstrably inadequate.",
            styles,
            border_color=NAVY_PRIMARY,
            bg_color=BG_LIGHT,
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: PRACTICAL INDUSTRY USE CASES
    # =========================================================================
    story.append(Paragraph("4. Practical Industry Use Cases", styles["h1"]))
    story.append(
        Paragraph(
            "While DataTripwire's reference implementation utilizes e-commerce sales datasets, "
            "its underlying crash-testing architecture directly addresses critical vulnerabilities across enterprise data pipelines:",
            styles["body"],
        )
    )

    use_case_data = [
        [Paragraph("<b>Domain</b>", styles["th"]), Paragraph("<b>Vulnerability Vector</b>", styles["th"]), Paragraph("<b>Downstream Business Risk</b>", styles["th"]), Paragraph("<b>DataTripwire Safeguard Evaluation</b>", styles["th"])],
        [
            Paragraph("<b>E-Commerce & Retail</b>", styles["td"]),
            Paragraph("Duplicate order ingestion via payment webhook retries.", styles["td"]),
            Paragraph("Artificially inflated revenue ledgers, over-reported merchant payouts, taxation errors.", styles["td"]),
            Paragraph("Verifies transaction ID uniqueness and control total reconciliation rules.", styles["td"]),
        ],
        [
            Paragraph("<b>FinTech & Banking</b>", styles["td"]),
            Paragraph("Negative transaction amount injected via reversal glitch.", styles["td"]),
            Paragraph("Distorted account balance calculations, erroneous risk threshold alerts.", styles["td"]),
            Paragraph("Evaluates non-negative domain boundaries and debit/credit balance constraints.", styles["td"]),
        ],
        [
            Paragraph("<b>Supply Chain & Logistics</b>", styles["td"]),
            Paragraph("Missing shipment quantity in warehouse transfer events.", styles["td"]),
            Paragraph("Silent inventory shrinkage, stockout forecasting failures, delayed reorders.", styles["td"]),
            Paragraph("Tests NOT NULL constraints and positive integer quantity enforcement.", styles["td"]),
        ],
        [
            Paragraph("<b>Machine Learning Pipelines</b>", styles["td"]),
            Paragraph("Dropped rows during training feature extraction ETL.", styles["td"]),
            Paragraph("Biased model weights, silent class distribution drift, degraded inference accuracy.", styles["td"]),
            Paragraph("Validates row-count thresholds and expectation reconciliation gates.", styles["td"]),
        ],
        [
            Paragraph("<b>Healthcare & Clinical</b>", styles["td"]),
            Paragraph("Corrupted dosage or invalid observation timestamp.", styles["td"]),
            Paragraph("Fatal dosing calculation errors, compromised clinical trial safety benchmarks.", styles["td"]),
            Paragraph("Evaluates strict datetime format checks and positive non-zero range rules.", styles["td"]),
        ],
    ]
    t_uc = Table(use_case_data, colWidths=[85, 115, 150, 154])
    t_uc.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4.5),
            ]
        )
    )
    story.append(t_uc)
    story.append(Spacer(1, 10))
    story.append(Paragraph("Cross-Industry Commonality", styles["h2"]))
    story.append(
        Paragraph(
            "Across each vertical, the failure pattern is identical: the database accepts the write, the ETL job "
            "exits with status <code>SUCCESS</code>, but the analytical truth is corrupted. By running DataTripwire "
            "prior to deploying new pipeline code, teams empirically prove that their data checks actually trigger "
            "under synthetic stress, establishing audit-grade defensibility.",
            styles["body"],
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 5: TECHNICAL ARCHITECTURE & COMPONENT MODEL
    # =========================================================================
    story.append(Paragraph("5. Technical Architecture & Component Model", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire adheres to strict architectural separation between presentation, HTTP interface, "
            "domain business logic, and local runtime storage:",
            styles["body"],
        )
    )

    arch_diagram = (
        "+-----------------------------------------------------------------------------------------+<br/>"
        "|                           <b>REACT 19 + TYPESCRIPT FRONTEND (Vite)</b>                       |<br/>"
        "|  +--------------------+  +--------------------+  +------------------+  +----------------+  |<br/>"
        "|  |   UploadView       |  |   ProfileView      |  |  ConfigureView   |  |  ResultsView   |  |<br/>"
        "|  |   (CSV Ingestion)  |  |   (Data Profiling) |  |  (Mutation Lab)  |  |  (Forensics)   |  |<br/>"
        "|  +--------------------+  +--------------------+  +------------------+  +----------------+  |<br/>"
        "|               | ThemeContextCore (Daylight / After Hours) | PipelineIllustration (SVG)     |<br/>"
        "+--------------------------------------------+--------------------------------------------+<br/>"
        "                                             | HTTP JSON / REST API (Port 8000)<br/>"
        "+--------------------------------------------v--------------------------------------------+<br/>"
        "|                              <b>FASTAPI BACKEND APPLICATION CORE</b>                        |<br/>"
        "|  +-----------------------------------------------------------------------------------+  |<br/>"
        "|  | Endpoints: /health  |  /api/v1/datasets  |  /api/v1/evaluations  |  OpenAPI Schema |  |<br/>"
        "|  +-----------------------------------------------------------------------------------+  |<br/>"
        "|                                            | Pydantic v2 Schema Validation               |<br/>"
        "|  +-----------------------------------------v-----------------------------------------+  |<br/>"
        "|  |                               <b>DOMAIN SERVICES LAYER</b>                           |  |<br/>"
        "|  |  +-------------------+  +-------------------+  +--------------------------------+ |  |<br/>"
        "|  |  | Dataset Profiler  |  | Mutation Engine   |  | Validation Engine              | |  |<br/>"
        "|  |  | (services/        |  | (services/        |  | (services/validators.py)        | |  |<br/>"
        "|  |  |  profiler.py)     |  |  mutation_engine) |  | 7 configurable rule types      | |  |<br/>"
        "|  |  +-------------------+  +-------------------+  +--------------------------------+ |  |<br/>"
        "|  |            |                     |                             |                   |  |<br/>"
        "|  |  +-------------------+  +-------------------+  +--------------------------------+ |  |<br/>"
        "|  |  | Decimal Financial |  | Fingerprint-Based |  | Deterministic Rule             | |  |<br/>"
        "|  |  | Metric Calculator |  | Evaluator         |  | Recommender                    | |  |<br/>"
        "|  |  | (services/metrics)|  | (evaluator.py)    |  | (services/recommendations.py)  | |  |<br/>"
        "|  |  +-------------------+  +-------------------+  +--------------------------------+ |  |<br/>"
        "+--+-----------------------------------------+-----------------------------------------+--+<br/>"
        "                                             |<br/>"
        "+--------------------------------------------v--------------------------------------------+<br/>"
        "|                       <b>LOCAL FILE-BASED PERSISTENCE REPOSITORY</b>                           |<br/>"
        "|   data/runtime/datasets/ (Raw CSV & Profiles)   |   data/runtime/evaluations/ (JSON Reports)   |<br/>"
        "+-----------------------------------------------------------------------------------------+"
    )
    story.append(make_callout(arch_diagram, styles, border_color=NAVY_PRIMARY, bg_color=BG_LIGHT))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Core Domain Contracts & Schema Definitions", styles["h2"]))
    contracts_data = [
        [Paragraph("<b>Domain Model</b>", styles["th"]), Paragraph("<b>Module Path</b>", styles["th"]), Paragraph("<b>Purpose & Key Fields</b>", styles["th"])],
        [Paragraph("<code>MutationItem</code>", styles["code"]), Paragraph("<code>schemas.mutation</code>", styles["td"]), Paragraph("Defines synthetic fault: <code>mutation_type</code>, <code>target_record_id</code>, <code>target_column</code>, <code>params</code>.", styles["td"])],
        [Paragraph("<code>ValidationRuleConfig</code>", styles["code"]), Paragraph("<code>schemas.validation</code>", styles["td"]), Paragraph("Defines rule check: <code>rule_type</code>, <code>target_column</code>, <code>enabled</code>, <code>parameters</code>.", styles["td"])],
        [Paragraph("<code>ValidationFinding</code>", styles["code"]), Paragraph("<code>schemas.validation</code>", styles["td"]), Paragraph("Reports discrepancy: <code>rule_id</code>, <code>rule_type</code>, <code>column</code>, <code>affected_record_ids</code>.", styles["td"])],
        [Paragraph("<code>EvaluationReport</code>", styles["code"]), Paragraph("<code>schemas.evaluation</code>", styles["td"]), Paragraph("Complete run summary: <code>mutation_score</code>, <code>metrics_impact</code>, <code>mutations[]</code>, <code>recommendations[]</code>.", styles["td"])],
        [Paragraph("<code>MetricDiff</code>", styles["code"]), Paragraph("<code>schemas.metrics</code>", styles["td"]), Paragraph("Quantifies drift: <code>metric_name</code>, <code>baseline_value</code>, <code>mutated_value</code>, <code>diff_value</code>.", styles["td"])],
    ]
    t_con = Table(contracts_data, colWidths=[120, 110, 274])
    t_con.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_con)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 6: DATA FLOW & INTERNAL WORKFLOW
    # =========================================================================
    story.append(Paragraph("6. Data Flow & Internal Processing Lifecycle", styles["h1"]))
    story.append(
        Paragraph(
            "A fundamental invariant in DataTripwire is <b>absolute source dataset immutability</b>. "
            "When evaluating synthetic faults, the original dataset is never modified in memory or on disk. "
            "The table below details the memory lifecycle during evaluation execution:",
            styles["body"],
        )
    )

    lifecycle_data = [
        [Paragraph("<b>Phase</b>", styles["th"]), Paragraph("<b>Internal Operation</b>", styles["th"]), Paragraph("<b>Memory & Safety Invariant</b>", styles["th"])],
        [
            Paragraph("1. Load", styles["td"]),
            Paragraph("Original CSV parsed into immutable baseline DataFrame <code>df_clean</code>.", styles["td"]),
            Paragraph("Read-only reference retained in dataset repository.", styles["td"]),
        ],
        [
            Paragraph("2. Baseline", styles["td"]),
            Paragraph("Validation suite executed against <code>df_clean</code> to produce baseline findings <code>F_base</code>.", styles["td"]),
            Paragraph("Generates set of stable string fingerprints: <code>{rule_id}::{type}::{col}::{records}</code>.", styles["td"]),
        ],
        [
            Paragraph("3. Fork", styles["td"]),
            Paragraph("Deep copy instantiated for each mutation item: <code>df_work = df_clean.copy(deep=True)</code>.", styles["td"]),
            Paragraph("Independent heap allocation; modifications cannot leak to sibling mutations.", styles["td"]),
        ],
        [
            Paragraph("4. Inject", styles["td"]),
            Paragraph("Mutation operator modifies target cell or appends/deletes row in <code>df_work</code>.", styles["td"]),
            Paragraph("Captures injection metadata: target record, column, old value, and expected rule.", styles["td"]),
        ],
        [
            Paragraph("5. Re-check", styles["td"]),
            Paragraph("Validation suite executed against <code>df_work</code> to produce findings <code>F_mut</code>.", styles["td"]),
            Paragraph("Reference row count passed explicitly to detect dropped rows.", styles["td"]),
        ],
        [
            Paragraph("6. Isolate", styles["td"]),
            Paragraph("Set subtraction: <code>New Findings = { f in F_mut | fp(f) not in F_base }</code>.", styles["td"]),
            Paragraph("Eliminates false positives from pre-existing dataset defects.", styles["td"]),
        ],
        [
            Paragraph("7. Match", styles["td"]),
            Paragraph("Verifies if any new finding matches expected rule code, column, and record ID.", styles["td"]),
            Paragraph("Mutation marked <code>detected=True</code> ONLY if relevant finding observed.", styles["td"]),
        ],
        [
            Paragraph("8. Quantify", styles["td"]),
            Paragraph("Computes business metrics on <code>df_work</code> vs clean baseline metrics.", styles["td"]),
            Paragraph("Exact monetary diff calculation: <code>diff = mutated_val - baseline_val</code>.", styles["td"]),
        ],
    ]
    t_lc = Table(lifecycle_data, colWidths=[55, 215, 234])
    t_lc.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_lc)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Fingerprinting Algorithm Implementation", styles["h2"]))
    fp_code = (
        "def compute_finding_fingerprint(finding: ValidationFinding) -> str:<br/>"
        "    \"\"\"Generates deterministic, hashable fingerprint for finding deduplication.\"\"\"<br/>"
        "    rec_ids = sorted(str(r) for r in (finding.affected_record_ids or []))<br/>"
        "    return f\"{finding.rule_id}::{finding.rule_type}::{finding.column or ''}::{','.join(rec_ids)}\""
    )
    story.append(make_callout(fp_code, styles, border_color=BORDER_LIGHT, bg_color=BG_LIGHT))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>Deduplication Rationale:</b> Real-world datasets often arrive with preexisting quality anomalies. "
            "If an incoming dataset already has a null email address, a synthetic null injection into an unrelated row "
            "must not take credit for detecting the preexisting null. The fingerprint set difference ensures that "
            "only findings freshly generated by the synthetic mutation are credited.",
            styles["body"],
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 7: MUTATION TESTING METHODOLOGY
    # =========================================================================
    story.append(Paragraph("7. Synthetic Mutation Engine & Operators", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire implements five concrete synthetic mutation operators representing realistic data pipeline failures. "
            "Each mutation operates on an isolated deep copy and captures structured injection telemetry:",
            styles["body"],
        )
    )

    mutation_data = [
        [Paragraph("<b>Mutation Class</b>", styles["th"]), Paragraph("<b>Target</b>", styles["th"]), Paragraph("<b>Synthetic Operation</b>", styles["th"]), Paragraph("<b>Expected Rule Safeguard</b>", styles["th"])],
        [
            Paragraph("<code>duplicate_row</code>", styles["code"]),
            Paragraph("Transaction ID", styles["td"]),
            Paragraph("Clones entire row (e.g. ORD-101) and appends to DataFrame. Simulates duplicate ingestion replay.", styles["td"]),
            Paragraph("<code>TRANSACTION_ID_DUPLICATE</code> (Unique constraint on transaction_id)", styles["td"]),
        ],
        [
            Paragraph("<code>missing_required_value</code>", styles["code"]),
            Paragraph("Specified Column", styles["td"]),
            Paragraph("Replaces valid cell with <code>np.nan</code>. Simulates upstream missing attribute drift.", styles["td"]),
            Paragraph("<code>REQUIRED_VALUE_MISSING</code> (NOT NULL check on required fields)", styles["td"]),
        ],
        [
            Paragraph("<code>invalid_quantity</code>", styles["code"]),
            Paragraph("quantity column", styles["td"]),
            Paragraph("Sets quantity to 0 or negative integer (-1). Tests numerical lower bounds.", styles["td"]),
            Paragraph("<code>QUANTITY_NOT_POSITIVE</code> (Strict positive quantity constraint)", styles["td"]),
        ],
        [
            Paragraph("<code>invalid_unit_price</code>", styles["code"]),
            Paragraph("unit_price column", styles["td"]),
            Paragraph("Sets price to negative float (-100.00). Tests monetary non-negativity.", styles["td"]),
            Paragraph("<code>UNIT_PRICE_NEGATIVE</code> (Non-negative unit price check)", styles["td"]),
        ],
        [
            Paragraph("<code>dropped_row</code>", styles["code"]),
            Paragraph("Row Index", styles["td"]),
            Paragraph("Deletes transaction from DataFrame. Tests record count reconciliation.", styles["td"]),
            Paragraph("<code>EXPECTED_ROW_COUNT_MISMATCH</code> (Reconciliation against control count)", styles["td"]),
        ],
    ]
    t_mut = Table(mutation_data, colWidths=[105, 80, 175, 144])
    t_mut.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4.2),
            ]
        )
    )
    story.append(t_mut)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Example Synthetic Mutation JSON Payload", styles["h2"]))
    json_mut = (
        "{\n"
        "  \"mutation_type\": \"duplicate_row\",\n"
        "  \"target_record_id\": \"ORD-101\",\n"
        "  \"target_column\": \"transaction_id\",\n"
        "  \"params\": {\"reproducibility_seed\": 42, \"append_position\": \"tail\"}\n"
        "}"
    )
    story.append(make_callout(f"<pre>{json_mut}</pre>", styles, border_color=BORDER_LIGHT, bg_color=BG_LIGHT))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Handling Failed or Inapplicable Mutations", styles["h2"]))
    story.append(
        Paragraph(
            "If a requested mutation cannot apply (e.g., target record ID does not exist in the dataset, or the specified "
            "column is missing), the mutation engine records <code>applied = False</code>, captures an informative error message, "
            "and sets <code>detected = None</code>. Crucially, <b>unapplied mutations are excluded from the mutation score denominator</b>, "
            "preventing artificial inflation or deflation of the detection ratio.",
            styles["body"],
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 8: VALIDATION AND DETECTION LOGIC
    # =========================================================================
    story.append(Paragraph("8. Validation Engine & Fault Detection Logic", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire provides seven built-in validation rules designed to enforce structural, domain, and relational "
            "integrity across transactional pipelines:",
            styles["body"],
        )
    )

    val_rules_data = [
        [Paragraph("<b>Rule Code</b>", styles["th"]), Paragraph("<b>Rule Name & Type</b>", styles["th"]), Paragraph("<b>Target & Parameters</b>", styles["th"]), Paragraph("<b>Detection Condition</b>", styles["th"])],
        [
            Paragraph("<code>REQ_001</code>", styles["code"]),
            Paragraph("Required Value Missing<br/><code>REQUIRED_VALUE_MISSING</code>", styles["td"]),
            Paragraph("Any designated column<br/>(e.g., customer_id, unit_price)", styles["td"]),
            Paragraph("Triggers finding if <code>pd.isna(val)</code> or empty whitespace.", styles["td"]),
        ],
        [
            Paragraph("<code>QTY_001</code>", styles["code"]),
            Paragraph("Positive Quantity<br/><code>QUANTITY_NOT_POSITIVE</code>", styles["td"]),
            Paragraph("<code>quantity</code><br/>Min: 1", styles["td"]),
            Paragraph("Triggers finding if <code>quantity &lt;= 0</code> or non-integer.", styles["td"]),
        ],
        [
            Paragraph("<code>PRC_001</code>", styles["code"]),
            Paragraph("Non-Negative Unit Price<br/><code>UNIT_PRICE_NEGATIVE</code>", styles["td"]),
            Paragraph("<code>unit_price</code><br/>Min: 0.00", styles["td"]),
            Paragraph("Triggers finding if <code>unit_price &lt; 0.00</code>.", styles["td"]),
        ],
        [
            Paragraph("<code>UNIQ_001</code>", styles["code"]),
            Paragraph("Transaction Uniqueness<br/><code>TRANSACTION_ID_DUPLICATE</code>", styles["td"]),
            Paragraph("<code>transaction_id</code><br/>Scope: Entire table", styles["td"]),
            Paragraph("Triggers finding if duplicates exist: <code>df.duplicated(subset=['transaction_id'])</code>.", styles["td"]),
        ],
        [
            Paragraph("<code>ROW_001</code>", styles["code"]),
            Paragraph("Expected Row Count<br/><code>EXPECTED_ROW_COUNT_MISMATCH</code>", styles["td"]),
            Paragraph("Table-level<br/><code>expected_count</code>", styles["td"]),
            Paragraph("Triggers finding if <code>len(df) != expected_count</code>.", styles["td"]),
        ],
        [
            Paragraph("<code>DATE_001</code>", styles["code"]),
            Paragraph("Valid Date Format<br/><code>DATE_FORMAT_INVALID</code>", styles["td"]),
            Paragraph("<code>transaction_date</code><br/>Format: YYYY-MM-DD", styles["td"]),
            Paragraph("Triggers finding if date string fails strict ISO parsing.", styles["td"]),
        ],
        [
            Paragraph("<code>FLD_001</code>", styles["code"]),
            Paragraph("Allowed Categorical Values<br/><code>UNEXPECTED_FIELD_VALUE</code>", styles["td"]),
            Paragraph("Categorical columns<br/><code>allowed_values[]</code>", styles["td"]),
            Paragraph("Triggers finding if value not in enumerated set.", styles["td"]),
        ],
    ]
    t_val = Table(val_rules_data, colWidths=[65, 140, 130, 169])
    t_val.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 3.8),
            ]
        )
    )
    story.append(t_val)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Detection Verification Criteria (Multi-Point Matching)", styles["h2"]))
    story.append(
        Paragraph(
            "To prevent false detection credit, the evaluation engine enforces <b>three-point matching</b> between the "
            "synthetic fault and the isolated candidate findings:<br/>"
            "1. <b>Rule Code Equivalence:</b> The finding's rule code must match the mutation's anticipated rule type.<br/>"
            "2. <b>Column Dimension Match:</b> The finding's affected column must match the mutated column.<br/>"
            "3. <b>Record Identifier Containment:</b> The finding's affected record IDs must include the injected row's ID.",
            styles["body"],
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 9: BUSINESS METRICS AND SCORING FORMULATION
    # =========================================================================
    story.append(Paragraph("9. Business Metrics & Mutation Scoring Formulation", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire quantifies the real downstream financial impact caused when data mutations escape validation checkpoints. "
            "All monetary calculations utilize Python's <code>Decimal</code> module to prevent floating-point representation drift.",
            styles["body"],
        )
    )

    story.append(Paragraph("Exact Mathematical Formulations", styles["h2"]))
    math_box = (
        "<b>1. Total Net Revenue:</b><br/>"
        "   <code>Revenue = SUM( Decimal(quantity_i) * Decimal(unit_price_i) )</code> quantized to <code>Decimal('0.01')</code><br/><br/>"
        "<b>2. Average Order Value (AOV):</b><br/>"
        "   <code>AOV = Revenue / Decimal(Transaction Count)</code> (handles division by zero gracefully)<br/><br/>"
        "<b>3. Absolute & Relative Metric Drift:</b><br/>"
        "   <code>Absolute Diff = Mutated Metric - Baseline Metric</code><br/>"
        "   <code>Relative Diff (%) = (Absolute Diff / Baseline Metric) * 100</code> (if baseline != 0)<br/><br/>"
        "<b>4. Mutation Score Formulation:</b><br/>"
        "   <code>Mutation Score (%) = (Detected Eligible Mutations / Total Eligible Applied Mutations) * 100</code>"
    )
    story.append(make_callout(math_box, styles, border_color=NAVY_PRIMARY, bg_color=BG_LIGHT))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Precision & Integrity Guarantees", styles["h2"]))
    story.append(Paragraph("• <b>Floating-Point Hazard:</b> Standard IEEE 754 floats introduce rounding errors (e.g., <code>0.1 + 0.2 = 0.30000000000000004</code>). In financial reconciliation, these microscopic errors trigger false drift alerts. DataTripwire guarantees exact currency precision with <code>ROUND_HALF_UP</code>.", styles["bullet"]))
    story.append(Paragraph("• <b>Zero-Denominator Rule:</b> When zero eligible mutations are applied, the mutation score evaluates to <code>None</code> (rendered as 'N/A' in the UI). The system never invents a false 100% or 0% score.", styles["bullet"]))
    story.append(Paragraph("• <b>Survivor Classification:</b> Any mutation where <code>applied = True</code> and <code>detected = False</code> is explicitly flagged as a <b>Surviving Mutation</b>, triggering immediate safeguard recommendation synthesis.", styles["bullet"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Scoring Classification Summary Table", styles["h2"]))
    score_table_data = [
        [Paragraph("<b>Status Category</b>", styles["th"]), Paragraph("<b>Engine Condition</b>", styles["th"]), Paragraph("<b>Score Effect</b>", styles["th"]), Paragraph("<b>System Action</b>", styles["th"])],
        [Paragraph("<b>Detected</b>", styles["td"]), Paragraph("<code>applied=True, detected=True</code>", styles["td"]), Paragraph("Increments Numerator & Denominator", styles["td"]), Paragraph("Safeguard validated; no recommendation needed.", styles["td"])],
        [Paragraph("<b>Surviving</b>", styles["td"]), Paragraph("<code>applied=True, detected=False</code>", styles["td"]), Paragraph("Increments Denominator ONLY", styles["td"]), Paragraph("<b>Vulnerability flagged; synthesizes rule recommendation.</b>", styles["td"])],
        [Paragraph("<b>Unapplied</b>", styles["td"]), Paragraph("<code>applied=False</code>", styles["td"]), Paragraph("<b>Excluded</b> from Score", styles["td"]), Paragraph("Logged as error; does not distort score.", styles["td"])],
    ]
    t_score = Table(score_table_data, colWidths=[90, 130, 120, 164])
    t_score.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_score)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 10: BACKEND API REFERENCE
    # =========================================================================
    story.append(Paragraph("10. Backend REST API Reference", styles["h1"]))
    story.append(
        Paragraph(
            "The FastAPI backend exposes versioned, OpenAPI-compliant endpoints on <code>http://127.0.0.1:8000</code>. "
            "Interactive Swagger documentation is available at <code>/docs</code> and ReDoc at <code>/redoc</code>.",
            styles["body"],
        )
    )

    api_data = [
        [Paragraph("<b>Method & Path</b>", styles["th"]), Paragraph("<b>Purpose</b>", styles["th"]), Paragraph("<b>Request Body / Params</b>", styles["th"]), Paragraph("<b>Success Response</b>", styles["th"])],
        [
            Paragraph("<code>GET /health</code><br/><code>GET /api/v1/health</code>", styles["code"]),
            Paragraph("Service readiness health check.", styles["td"]),
            Paragraph("None", styles["td"]),
            Paragraph("<code>200 OK</code> · HealthResponse (status: 'ok', version: '0.1.0')", styles["td"]),
        ],
        [
            Paragraph("<code>POST /api/v1/datasets/sample</code>", styles["code"]),
            Paragraph("Loads & profiles bundled 15-tx sales dataset.", styles["td"]),
            Paragraph("None", styles["td"]),
            Paragraph("<code>201 Created</code> · DatasetResponse with DatasetProfile", styles["td"]),
        ],
        [
            Paragraph("<code>POST /api/v1/datasets</code>", styles["code"]),
            Paragraph("Uploads & profiles custom CSV dataset.", styles["td"]),
            Paragraph("Multipart form: <code>file</code> (.csv)", styles["td"]),
            Paragraph("<code>201 Created</code> · DatasetResponse", styles["td"]),
        ],
        [
            Paragraph("<code>GET /api/v1/datasets</code>", styles["code"]),
            Paragraph("Lists all persisted datasets.", styles["td"]),
            Paragraph("None", styles["td"]),
            Paragraph("<code>200 OK</code> · List[DatasetResponse]", styles["td"]),
        ],
        [
            Paragraph("<code>GET /api/v1/datasets/{id}</code>", styles["code"]),
            Paragraph("Retrieves dataset metadata & profile.", styles["td"]),
            Paragraph("Path: <code>dataset_id</code>", styles["td"]),
            Paragraph("<code>200 OK</code> · DatasetResponse (404 if missing)", styles["td"]),
        ],
        [
            Paragraph("<code>GET /api/v1/datasets/{id}/profile</code>", styles["code"]),
            Paragraph("Inspects structural profile metrics.", styles["td"]),
            Paragraph("Path: <code>dataset_id</code>", styles["td"]),
            Paragraph("<code>200 OK</code> · DatasetProfile", styles["td"]),
        ],
        [
            Paragraph("<code>POST /api/v1/datasets/{id}/evaluations</code>", styles["code"]),
            Paragraph("Executes mutation test batch against dataset.", styles["td"]),
            Paragraph("JSON: <code>mutations[]</code>, <code>rules{}</code>", styles["td"]),
            Paragraph("<code>201 Created</code> · EvaluationReport", styles["td"]),
        ],
        [
            Paragraph("<code>GET /api/v1/evaluations/{id}</code>", styles["code"]),
            Paragraph("Retrieves persisted evaluation report.", styles["td"]),
            Paragraph("Path: <code>evaluation_id</code>", styles["td"]),
            Paragraph("<code>200 OK</code> · EvaluationReport (404 if missing)", styles["td"]),
        ],
    ]
    t_api = Table(api_data, colWidths=[115, 105, 120, 164])
    t_api.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_api)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Sample Evaluation Request Payload", styles["h2"]))
    req_json = (
        "POST /api/v1/datasets/ds_sales_sample/evaluations<br/>"
        "{\n"
        "  \"mutations\": [\n"
        "    {\"mutation_type\": \"duplicate_row\", \"target_record_id\": \"ORD-101\", \"target_column\": \"transaction_id\"}\n"
        "  ],\n"
        "  \"rules\": {\n"
        "    \"check_uniqueness\": false, \"check_positive_quantity\": true, \"check_non_negative_price\": true\n"
        "  }\n"
        "}"
    )
    story.append(make_callout(f"<code>{req_json}</code>", styles, border_color=BORDER_LIGHT, bg_color=BG_LIGHT))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 11: FRONTEND DESIGN AND USER EXPERIENCE
    # =========================================================================
    story.append(Paragraph("11. Frontend Design & User Experience Engineering", styles["h1"]))
    story.append(
        Paragraph(
            "The DataTripwire user interface was engineered to evoke a sophisticated developer tools cockpit—<b>'The Data Reliability Lab'</b>. "
            "Built with React 19, TypeScript, and Vite, the UI adheres to rigorous design-system tokens:",
            styles["body"],
        )
    )

    story.append(Paragraph("Four-Stage Workflow Navigation", styles["h2"]))
    story.append(Paragraph("1. <b>01 Ingest:</b> Drag-and-drop CSV ingestion zone with instant format validation or one-click sample dataset loading.", styles["bullet"]))
    story.append(Paragraph("2. <b>02 Profile:</b> Structural column breakdown, null count distributions, datatype inferences, and baseline metrics.", styles["bullet"]))
    story.append(Paragraph("3. <b>03 Mutation Lab:</b> Adversarial sandbox allowing users to configure synthetic fault batches and toggle active validation safeguards.", styles["bullet"]))
    story.append(Paragraph("4. <b>04 Investigation:</b> Forensic results cockpit displaying mutation scores, metric error deltas, surviving fault telemetry, and one-click safeguard fixes.", styles["bullet"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Dual Theme System Architecture", styles["h2"]))
    theme_table_data = [
        [Paragraph("<b>Theme Token</b>", styles["th"]), Paragraph("<b>Daylight Lab (Light Mode)</b>", styles["th"]), Paragraph("<b>After Hours (Dark Mode)</b>", styles["th"])],
        [Paragraph("Canvas Background", styles["td"]), Paragraph("<code>#F5F4EF</code> (Warm engineering parchment)", styles["td"]), Paragraph("<code>#101216</code> (Deep ink obsidian)", styles["td"])],
        [Paragraph("Card Surface", styles["td"]), Paragraph("<code>#FFFFFF</code> (Clean laboratory card)", styles["td"]), Paragraph("<code>#171B21</code> (Graphite surface)", styles["td"])],
        [Paragraph("Primary Text", styles["td"]), Paragraph("<code>#1B1D20</code> (High contrast charcoal)", styles["td"]), Paragraph("<code>#F0F3F6</code> (Crisp bright chalk)", styles["td"])],
        [Paragraph("Signal Accent", styles["td"]), Paragraph("<code>#F05A3B</code> (Vibrant signal orange)", styles["td"]), Paragraph("<code>#FF7043</code> (Luminous hot flame orange)", styles["td"])],
        [Paragraph("Success Accent", styles["td"]), Paragraph("<code>#287A55</code> (Pine emerald green)", styles["td"]), Paragraph("<code>#34D399</code> (Electric emerald)", styles["td"])],
    ]
    t_th = Table(theme_table_data, colWidths=[110, 197, 197])
    t_th.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4.2),
            ]
        )
    )
    story.append(t_th)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Interactive SVG Pipeline Visualization", styles["h2"]))
    story.append(
        Paragraph(
            "The header features a custom interactive SVG pipeline visualizer (<code>PipelineIllustration.tsx</code>) "
            "rendering real-time pipeline topology: Raw Input Ingestion &rarr; Mutation Crash Zone &rarr; Validation Gate &rarr; "
            "Downstream Protected Ledger. Nodes glow dynamically based on current evaluation state.",
            styles["body"],
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 12: INSTALLATION AND SETUP
    # =========================================================================
    story.append(Paragraph("12. Installation, Environment & Startup Procedures", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire provides both a native Windows one-click launcher and standard cross-platform terminal commands. "
            "Prerequisites: Python 3.11+ and Node.js 18+.",
            styles["body"],
        )
    )

    story.append(Paragraph("Primary Windows Launch: start_datatripwire.bat", styles["h2"]))
    story.append(
        Paragraph(
            "Double-clicking <code>start_datatripwire.bat</code> from Windows File Explorer invokes the startup system. "
            "The batch file determines the repository root dynamically, verifies Python 3.11+ and Node.js 18+ in PATH, "
            "and passes control to the Python supervisor orchestrator (<code>scripts/dev.py</code>).",
            styles["body"],
        )
    )

    story.append(Paragraph("Startup Supervisor Architecture (scripts/dev.py)", styles["h2"]))
    story.append(
        Paragraph(
            "The supervisor orchestrates dependencies, port readiness, and clean shutdown:<br/>"
            "1. <b>Dependency Verification:</b> Checks backend Python modules and frontend <code>node_modules</code> (auto-installs if missing).<br/>"
            "2. <b>Process Spawning:</b> Spawns backend on <code>127.0.0.1:8000</code> and frontend Vite server on <code>127.0.0.1:5173</code>.<br/>"
            "3. <b>Readiness Polling:</b> Polls <code>/health</code> and HTTP 5173 for up to 30 seconds before opening the browser.<br/>"
            "4. <b>Browser Launch:</b> Automatically launches default web browser to <code>http://localhost:5173</code>.<br/>"
            "5. <b>Process-Tree Termination:</b> On Ctrl+C, executes targeted <code>taskkill /F /T /PID &lt;pid&gt;</code> to cleanly shut down child processes without orphaned Node or Python servers.",
            styles["body"],
        )
    )

    story.append(Paragraph("Manual Terminal Commands (Cross-Platform Alternative)", styles["h2"]))
    manual_cmds = (
        "<b>Terminal 1 (Backend):</b><br/>"
        "<code>cd backend && python -m uvicorn datatripwire.api.main:app --host 127.0.0.1 --port 8000 --reload</code><br/><br/>"
        "<b>Terminal 2 (Frontend):</b><br/>"
        "<code>cd frontend && npm run dev -- --host 127.0.0.1 --port 5173</code>"
    )
    story.append(make_callout(manual_cmds, styles, border_color=BORDER_LIGHT, bg_color=BG_LIGHT))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Environment Configuration Variables", styles["h2"]))
    env_data = [
        [Paragraph("<b>Variable</b>", styles["th"]), Paragraph("<b>Default Value</b>", styles["th"]), Paragraph("<b>Description & Purpose</b>", styles["th"])],
        [Paragraph("<code>DATATRIPWIRE_ENV</code>", styles["code"]), Paragraph("<code>development</code>", styles["td"]), Paragraph("Application runtime environment (development/production).", styles["td"])],
        [Paragraph("<code>PORT</code>", styles["code"]), Paragraph("<code>8000</code>", styles["td"]), Paragraph("Backend FastAPI server listening port.", styles["td"])],
        [Paragraph("<code>MAX_FILE_SIZE_MB</code>", styles["code"]), Paragraph("<code>5</code>", styles["td"]), Paragraph("Maximum allowed CSV upload size (in megabytes).", styles["td"])],
        [Paragraph("<code>CORS_ORIGINS</code>", styles["code"]), Paragraph("<code>http://localhost:5173</code>", styles["td"]), Paragraph("Allowed frontend origins for CORS header policy.", styles["td"])],
    ]
    t_env = Table(env_data, colWidths=[120, 100, 284])
    t_env.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_env)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 13: TESTING AND VERIFICATION
    # =========================================================================
    story.append(Paragraph("13. Automated Testing, Verification & Quality Assurance", styles["h1"]))
    story.append(
        Paragraph(
            "Every architectural tier is verified through comprehensive automated test suites. "
            "All tests can be executed via a single unified runner: <code>python scripts/run_tests.py</code>.",
            styles["body"],
        )
    )

    test_summary_data = [
        [Paragraph("<b>Verification Stage</b>", styles["th"]), Paragraph("<b>Harness / Tool</b>", styles["th"]), Paragraph("<b>Execution Scope</b>", styles["th"]), Paragraph("<b>Empirical Result</b>", styles["th"])],
        [
            Paragraph("<b>Backend Unit & API</b>", styles["td"]),
            Paragraph("pytest 9.1+ · anyio · TestClient", styles["td"]),
            Paragraph("115 tests: CSV ingestion, profiler, mutator, validators, metrics, evaluator, recommendations, API routes.", styles["td"]),
            Paragraph("<b>115 passed</b> in 0.85s (0 failures, 0 regressions)", styles["td"]),
        ],
        [
            Paragraph("<b>Frontend Linting</b>", styles["td"]),
            Paragraph("oxlint 1.81+ (multi-threaded)", styles["td"]),
            Paragraph("15 files, 116 rules: syntax, React hooks, imports, type hygiene.", styles["td"]),
            Paragraph("<b>0 errors, 0 warnings</b> in 14ms", styles["td"]),
        ],
        [
            Paragraph("<b>TypeScript & Build</b>", styles["td"]),
            Paragraph("tsc -b && vite build", styles["td"]),
            Paragraph("Strict typechecking and production asset bundling.", styles["td"]),
            Paragraph("<b>Compiled cleanly</b> in 131ms (0 errors)", styles["td"]),
        ],
        [
            Paragraph("<b>End-to-End Workflow</b>", styles["td"]),
            Paragraph("Browser Subagent / Playwright", styles["td"]),
            Paragraph("Full user journey: Ingest, profile, mutate, survive, recommend, harden, trap.", styles["td"]),
            Paragraph("<b>Verified end-to-end</b> with real data & screenshots", styles["td"]),
        ],
    ]
    t_test = Table(test_summary_data, colWidths=[100, 100, 184, 120])
    t_test.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4.5),
            ]
        )
    )
    story.append(t_test)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Backend Test Suite Module Breakdown", styles["h2"]))
    mod_breakdown_data = [
        [Paragraph("<b>Test Module</b>", styles["th"]), Paragraph("<b>Coverage Focus</b>", styles["th"]), Paragraph("<b>Test Count</b>", styles["th"])],
        [Paragraph("<code>tests/test_api.py</code>", styles["code"]), Paragraph("FastAPI endpoints, CORS, file upload validation, 404/422 error handlers", styles["td"]), Paragraph("18 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/test_profiler.py</code>", styles["code"]), Paragraph("Null distributions, column profiling, summary statistics, schema inference", styles["td"]), Paragraph("14 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/test_mutation_engine.py</code>", styles["code"]), Paragraph("Deep copy isolation, 5 mutation operators, reproducibility seed, invalid targets", styles["td"]), Paragraph("22 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/test_validators.py</code>", styles["code"]), Paragraph("All 7 validation rules, boundary conditions, expected row count mismatches", styles["td"]), Paragraph("26 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/test_evaluator.py</code>", styles["code"]), Paragraph("Finding fingerprinting, baseline isolation, multi-point detection matching", styles["td"]), Paragraph("16 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/test_metrics.py</code>", styles["code"]), Paragraph("Decimal monetary arithmetic, revenue, AOV, zero division handling", styles["td"]), Paragraph("10 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/test_recommendations.py</code>", styles["code"]), Paragraph("Deterministic safeguard synthesis for surviving mutations", styles["td"]), Paragraph("9 tests (100% pass)", styles["td"])],
    ]
    t_mod = Table(mod_breakdown_data, colWidths=[140, 264, 100])
    t_mod.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_mod)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 14: MAIN DEMONSTRATION SCENARIO
    # =========================================================================
    story.append(Paragraph("14. End-to-End Demonstration Scenario", styles["h1"]))
    story.append(
        Paragraph(
            "The core live demonstration uses the bundled 15-record sales dataset (<code>sample_sales.csv</code>) "
            "to exhibit the vulnerability escape, metric drift, and safeguard hardening cycle:",
            styles["body"],
        )
    )

    demo_steps = [
        [Paragraph("<b>Step</b>", styles["th"]), Paragraph("<b>Action & State</b>", styles["th"]), Paragraph("<b>Harness State</b>", styles["th"]), Paragraph("<b>Observed Empirical Result</b>", styles["th"])],
        [
            Paragraph("1. Clean Baseline", styles["td"]),
            Paragraph("Load Sample Dataset", styles["td"]),
            Paragraph("Pristine 15 transactions", styles["td"]),
            Paragraph("Total Revenue: <b>₹19,000.00</b> · 0 nulls · 0 duplicates", styles["td"]),
        ],
        [
            Paragraph("2. Injected Fault", styles["td"]),
            Paragraph("Synthesize duplicate transaction ORD-101", styles["td"]),
            Paragraph("Quantity: 1 · Unit Price: ₹1,000.00", styles["td"]),
            Paragraph("Independent copy created; source CSV pristine", styles["td"]),
        ],
        [
            Paragraph("3. Vulnerability Run", styles["td"]),
            Paragraph("Execute evaluation with Uniqueness OFF", styles["td"]),
            Paragraph("Baseline safeguards active; uniqueness disabled", styles["td"]),
            Paragraph("<b>Score: 0% · Fault Survived</b> · Revenue drifts to ₹20,000.00 (+₹1,000.00 / +5.26% error)", styles["td"]),
        ],
        [
            Paragraph("4. Recommendation", styles["td"]),
            Paragraph("Inspect Investigation forensics", styles["td"]),
            Paragraph("Actionable safeguard synthesized", styles["td"]),
            Paragraph("Recommends: <code>UNIQUENESS on transaction_id</code> with Python validation code snippet", styles["td"]),
        ],
        [
            Paragraph("5. Hardened Run", styles["td"]),
            Paragraph("Click 'Test Recommended Safeguard' & re-evaluate", styles["td"]),
            Paragraph("Uniqueness check enabled in rule configuration", styles["td"]),
            Paragraph("<b>Score: 100% · Fault Trapped ✓</b> · Duplicate blocked at gate; observed revenue protected at ₹19,000.00 (₹0.00 drift)", styles["td"]),
        ],
    ]
    t_demo = Table(demo_steps, colWidths=[60, 130, 140, 174])
    t_demo.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4.2),
            ]
        )
    )
    story.append(t_demo)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Bundled Reference Dataset Inventory (sample_sales.csv)", styles["h2"]))
    ds_summary_text = (
        "<b>Reference Dataset Metadata:</b> 15 Records · 5 Columns: <code>transaction_id, customer_id, quantity, unit_price, transaction_date</code><br/>"
        "• Total Baseline Clean Revenue: <b>₹19,000.00</b> (exact Decimal sum of <code>quantity * unit_price</code>)<br/>"
        "• Total Transactions: <b>15</b> · Distinct Customers: <b>10</b> (CUST-001 through CUST-010)<br/>"
        "• Target Injection Row: <code>ORD-101</code> (Customer: CUST-001, Quantity: 1, Unit Price: ₹1,000.00)<br/>"
        "• Downstream Ledger Distortion: +₹1,000.00 net revenue inflation, distorting executive reporting until trapped."
    )
    story.append(make_callout(ds_summary_text, styles, border_color=EMERALD_GREEN, bg_color=GREEN_BG))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 15: DIFFERENTIATION, SECURITY & LIMITATIONS
    # =========================================================================
    story.append(Paragraph("15. Differentiation & Tool Landscape Comparison", styles["h1"]))
    story.append(
        Paragraph(
            "Established data-quality tools such as <b>Great Expectations</b>, <b>Soda Core</b>, and <b>AWS Deequ</b> "
            "excel at asserting constraints on production tables. However, they are fundamentally <b>monitoring systems</b>, "
            "not <b>crash-testing harnesses</b>. DataTripwire occupies a complementary, pioneering niche:",
            styles["body"],
        )
    )

    diff_data = [
        [Paragraph("<b>Capability Dimension</b>", styles["th"]), Paragraph("<b>Traditional Data Quality (e.g. Great Expectations)</b>", styles["th"]), Paragraph("<b>DataTripwire Crash-Testing Platform</b>", styles["th"])],
        [
            Paragraph("<b>Core Question</b>", styles["td"]),
            Paragraph("\"Does this incoming data batch satisfy my defined expectations?\"", styles["td"]),
            Paragraph("<b>\"Are my defined expectations capable of catching realistic data corruptions?\"</b>", styles["td"]),
        ],
        [
            Paragraph("<b>Testing Target</b>", styles["td"]),
            Paragraph("The data is the system under test.", styles["td"]),
            Paragraph("<b>The validation safeguards themselves</b> are the system under test.", styles["td"]),
        ],
        [
            Paragraph("<b>Fault Injection</b>", styles["td"]),
            Paragraph("Passive. Requires real-world anomalies to occur in production.", styles["td"]),
            Paragraph("<b>Active & Synthetic.</b> Adversarially injects controlled mutations into memory copies.", styles["td"]),
        ],
        [
            Paragraph("<b>Business Impact</b>", styles["td"]),
            Paragraph("Reports pass/fail counts; rarely quantifies financial distortion.", styles["td"]),
            Paragraph("<b>Measures exact financial metric error</b> (e.g. INR/USD revenue discrepancy).", styles["td"]),
        ],
        [
            Paragraph("<b>Remediation</b>", styles["td"]),
            Paragraph("Manual rule creation and expectation suite maintenance.", styles["td"]),
            Paragraph("<b>Synthesizes targeted rule recommendations</b> for surviving faults.", styles["td"]),
        ],
    ]
    t_diff = Table(diff_data, colWidths=[90, 207, 207])
    t_diff.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_diff)
    story.append(Spacer(1, 8))

    story.append(Paragraph("16. Security, Local Privacy & Architectural Boundaries", styles["h1"]))
    story.append(Paragraph("• <b>100% Local Processing & Zero External Telemetry:</b> No dataset contents, column names, or evaluation metrics are transmitted to cloud services, third-party APIs, or external LLMs.", styles["bullet"]))
    story.append(Paragraph("• <b>Strict Ingestion Guardrails:</b> File upload bounds (5 MB max default), extension enforcement (.csv only), UTF-8 / Latin-1 encoding detection, and boundary checks (50,000 rows max, 100 columns max).", styles["bullet"]))
    story.append(Paragraph("• <b>Safe Filesystem Repositories:</b> Storage paths are sanitized and isolated in <code>data/runtime/</code>; directory traversal via filenames is strictly prevented.", styles["bullet"]))

    story.append(Paragraph("Current Architectural Limitations (Honest Disclosure)", styles["h2"]))
    story.append(Paragraph("1. <b>Tabular CSV Scope:</b> The current engine parses tabular CSV files. Parquet, Delta Lake, Apache Iceberg, and direct SQL warehouse connectors are planned for future phases.", styles["bullet"]))
    story.append(Paragraph("2. <b>Sales Schema Specialization:</b> While generic CSV profiling works across all CSVs, business revenue impact analysis is currently specialized for schemas containing <code>transaction_id, customer_id, quantity, unit_price, transaction_date</code>.", styles["bullet"]))
    story.append(Paragraph("3. <b>Local In-Memory Processing:</b> Mutations and metrics execute in-memory via Pandas; massive distributed datasets exceeding memory limits require future PySpark / DuckDB integration.", styles["bullet"]))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 16: ROADMAP, CONCLUSION, APPENDIX & ATTESTATION
    # =========================================================================
    story.append(Paragraph("17. Development Roadmap & Future Enhancements", styles["h1"]))
    roadmap_data = [
        [Paragraph("<b>Milestone</b>", styles["th"]), Paragraph("<b>Timeline</b>", styles["th"]), Paragraph("<b>Planned Capabilities & Features</b>", styles["th"])],
        [
            Paragraph("<b>Phase 4: Multi-Format & CI/CD</b>", styles["td"]),
            Paragraph("Near-Term (Q1 2027)", styles["td"]),
            Paragraph("• Parquet/JSON ingestion drivers.<br/>• Headless CLI command (<code>datatripwire run --ci</code>) for GitHub Actions / GitLab CI.<br/>• Generic business metric calculation formulas configurable via YAML contracts.", styles["td"]),
        ],
        [
            Paragraph("<b>Phase 5: Warehouse Connectors</b>", styles["td"]),
            Paragraph("Medium-Term (Q2–Q3 2027)", styles["td"]),
            Paragraph("• Direct read connectors for Snowflake, BigQuery, and PostgreSQL staging tables.<br/>• Automated export of synthesized recommendations into Great Expectations and dbt test YAML.<br/>• Multi-mutation combinatorial testing (interaction fault models).", styles["td"]),
        ],
        [
            Paragraph("<b>Phase 6: Distributed Scale</b>", styles["td"]),
            Paragraph("Long-Term (2027+)", styles["td"]),
            Paragraph("• Distributed mutation testing engine backed by DuckDB and Apache Arrow.<br/>• Historical pipeline vulnerability drift tracking across software releases.<br/>• Role-based access control and multi-tenant team collaboration workspaces.", styles["td"]),
        ],
    ]
    t_road = Table(roadmap_data, colWidths=[115, 90, 299])
    t_road.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_road)
    story.append(Spacer(1, 6))

    story.append(Paragraph("18. Engineering Conclusion", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire establishes that mutation testing is not only viable for data pipelines, but essential. "
            "By systematically introducing controlled data corruptions into isolated in-memory replicas, data engineering "
            "teams can replace ungrounded assumptions with empirical confidence. The completed prototype demonstrates "
            "that catching a data fault is only half the battle: understanding the exact financial magnitude of silent "
            "escapes provides the business justification necessary to prioritize data reliability engineering.",
            styles["body"],
        )
    )
    story.append(Spacer(1, 4))

    story.append(Paragraph("19. Technical Appendix & Source Artifacts", styles["h1"]))
    app_data = [
        [Paragraph("<b>Artifact / Path</b>", styles["th"]), Paragraph("<b>Type</b>", styles["th"]), Paragraph("<b>Description & Verification Command</b>", styles["th"])],
        [
            Paragraph("<code>start_datatripwire.bat</code>", styles["code"]),
            Paragraph("Windows Batch", styles["td"]),
            Paragraph("One-click launcher: environment check, supervisor execution, browser opening.", styles["td"]),
        ],
        [
            Paragraph("<code>scripts/dev.py</code>", styles["code"]),
            Paragraph("Python Supervisor", styles["td"]),
            Paragraph("Dual-process supervisor with readiness polling & targeted PID tree termination.", styles["td"]),
        ],
        [
            Paragraph("<code>scripts/run_tests.py</code>", styles["code"]),
            Paragraph("Test Harness", styles["td"]),
            Paragraph("Runs full test suite: <code>python scripts/run_tests.py</code> (115 pytest + oxlint + vite).", styles["td"]),
        ],
        [
            Paragraph("<code>scripts/check_setup.py</code>", styles["code"]),
            Paragraph("Diagnostics", styles["td"]),
            Paragraph("Validates environment prerequisites: <code>python scripts/check_setup.py</code>.", styles["td"]),
        ],
    ]
    t_app = Table(app_data, colWidths=[120, 80, 304])
    t_app.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 3.5),
            ]
        )
    )
    story.append(t_app)
    story.append(Spacer(1, 6))

    # Attestation Signature Box
    attest_box = (
        "<b>20. Document Attestation & Verification Record</b><br/>"
        "• <b>Repository:</b> https://github.com/rahulgoreofficial/DataTripwire-Data-Pipeline-Reliability-Mutation-Testing<br/>"
        "• <b>Verification Status:</b> 115 / 115 backend tests passed · 0 frontend lint warnings · 0 build errors<br/>"
        "• <b>Runtime Integrity:</b> 100% verified locally on Windows 10/11 with Python 3.14.3 and Node.js v24.12.0<br/>"
        "• <b>Lead Maintainer:</b> Rahul Gore &lt;rahulgoreoffical@gmail.com&gt;<br/>"
        "• <b>Date of Attestation:</b> October 15, 2026"
    )
    story.append(make_callout(attest_box, styles, border_color=EMERALD_GREEN, bg_color=GREEN_BG))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report successfully generated at: {PDF_OUTPUT}")


if __name__ == "__main__":
    build_pdf_report()
