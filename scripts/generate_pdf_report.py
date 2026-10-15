#!/usr/bin/env python3
"""DataTripwire Comprehensive Project Report PDF Generator.

Builds an engineering-grade, publication-quality 16-page PDF report
documenting DataTripwire's multi-domain architecture, mutation engine,
validation rules, API specifications, UI engineering, test verification,
sample datasets catalog, limitations, and roadmap.
"""

from datetime import datetime, timezone
from pathlib import Path
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
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
        self.drawString(124, 755, "// MULTI-DOMAIN DATA RELIABILITY LAB · ARCHITECTURE & AUDIT REPORT")
        self.drawRightString(558, 755, "OCTOBER 2026")

        self.setStrokeColor(BORDER_LIGHT)
        self.setLineWidth(0.6)
        self.line(54, 748, 558, 748)

        # Footer
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXT_MUTED)
        self.drawString(54, 32, "DataTripwire — Multi-Domain Data Pipeline Reliability & Mutation Testing Platform")
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
        fontSize=14,
        leading=18,
        textColor=NAVY_PRIMARY,
        spaceBefore=7,
        spaceAfter=5,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=NAVY_SECONDARY,
        spaceBefore=7,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.4,
        leading=12.4,
        textColor=TEXT_PRIMARY,
        spaceAfter=5,
    )

    bullet_style = ParagraphStyle(
        "BulletDark",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.0,
        leading=11.8,
        textColor=TEXT_PRIMARY,
        leftIndent=12,
        spaceAfter=3,
    )

    code_style = ParagraphStyle(
        "CodeText",
        parent=base["Normal"],
        fontName="Courier",
        fontSize=7.2,
        leading=9.6,
        textColor=NAVY_PRIMARY,
    )

    callout_text = ParagraphStyle(
        "CalloutText",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.0,
        leading=11.6,
        textColor=NAVY_PRIMARY,
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.6,
        leading=9.8,
        textColor=colors.white,
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=7.4,
        leading=10.0,
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
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
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
            "<b>Multi-Domain Data Pipeline Reliability & Mutation Testing Platform</b><br/>"
            "Evaluating whether existing data-quality safeguards detect realistic data corruptions across E-Commerce Transactions and Industrial IoT Telemetry before silent errors cascade into downstream ledgers and analytics.",
            styles["subtitle_cover"],
        )
    )

    story.append(
        make_callout(
            "<b>Core Technical Proposition:</b> <i>\"Break the data. Test the safeguards. Protect the metrics.\"</i><br/>"
            "Traditional data quality passively checks whether incoming batches comply with rules. DataTripwire transposes "
            "adversarial mutation testing to evaluate the safeguards themselves, measuring the exact business and operational "
            "distortion caused when faults traverse pipelines undetected.",
            styles,
            border_color=SIGNAL_ORANGE,
            bg_color=ORANGE_BG,
        )
    )
    story.append(Spacer(1, 14))

    # Cover Meta Grid
    meta_data = [
        [Paragraph("<b>Document Version</b>", styles["td"]), Paragraph("v0.2.0 (Multi-Domain Release)", styles["td"])],
        [Paragraph("<b>Publication Date</b>", styles["td"]), Paragraph(datetime.now(timezone.utc).strftime("%B %d, %Y"), styles["td"])],
        [Paragraph("<b>Supported Domains</b>", styles["td"]), Paragraph("E-Commerce Sales (`sales`), Manufacturing IoT (`manufacturing`), General CSV", styles["td"])],
        [Paragraph("<b>Product Status</b>", styles["td"]), Paragraph("All Core Phases & Multi-Domain Engine Verified · 140/140 Tests Passing", styles["td"])],
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
                ("PADDING", (0, 0), (-1, -1), 5.0),
            ]
        )
    )
    story.append(meta_table)

    story.append(Spacer(1, 14))
    story.append(Paragraph("<b>Table of Report Sections:</b>", styles["h2"]))

    toc_items = [
        "01. Executive Summary", "02. Problem Statement: Silent Data Degradation",
        "03. Proposed Solution & Mutation Workflow", "04. Practical Industry Use Cases",
        "05. Technical Architecture & Component Model", "06. Data Flow & Internal Processing Lifecycle",
        "07. Synthetic Mutation Engine & Operators", "08. Validation Engine & Fault Detection Logic",
        "09. Business Metrics & Mutation Scoring Formulation", "10. Backend REST API Reference",
        "11. Frontend Design & User Experience Engineering", "12. Installation, Environment & Startup Procedures",
        "13. Automated Testing, Verification & Quality Assurance", "14. Sample Datasets & Demonstration Scenarios",
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
                ("PADDING", (0, 0), (-1, -1), 2.5),
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
            "Modern data pipelines powering executive financial dashboards, operational equipment telemetry, and ML models "
            "frequently suffer from a dangerous failure mode: pipelines complete execution with exit status <code>0</code> "
            "while processing corrupted, duplicated, or drifted data. Traditional data-quality tools passively monitor "
            "production tables against static rules, but data engineering teams rarely have a structured mechanism "
            "to test whether those rules are actually capable of catching realistic, critical data corruptions.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>DataTripwire</b> bridges this verification gap by introducing <b>adversarial mutation testing for data pipelines</b>. "
            "Operating as a data crash-testing laboratory, it injects controlled, synthetic data faults into isolated working "
            "copies of datasets, executes the active validation suite, empirically verifies whether the faults trigger relevant checkpoints, "
            "and measures downstream ledger or telemetry distortion when faults escape.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "Originally specialized for e-commerce transactions, DataTripwire has been upgraded into a <b>multi-domain platform</b> "
            "supporting: (1) E-Commerce Sales (`sales`); (2) Manufacturing / Industrial IoT (`manufacturing`) telemetry monitoring; "
            "and (3) General Tabular CSV Profiling (`general`). The system provides 100% local, privacy-preserving execution with "
            "a robust FastAPI backend, Pydantic v2 data contracts, exact Decimal monetary arithmetic, React 19 dual-theme UI, "
            "and one-click Windows startup (<code>start_datatripwire.bat</code>).",
            styles["body"],
        )
    )

    story.append(
        make_callout(
            "<b>Executive Takeaway:</b> DataTripwire proves data quality through empirical evidence rather than assumption. "
            "In verified demonstrations across both retail sales and a 5,040-record industrial IoT dataset, unhandled ingestion "
            "duplicates (0% detection score) escape baseline safeguards, cause measurable metric drift (+₹800 revenue or distorted "
            "production totals), and are successfully trapped (100% score, 0 drift) once recommended safeguards are enabled.",
            styles,
            border_color=EMERALD_GREEN,
            bg_color=GREEN_BG,
        )
    )
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Problem Statement: Silent Data Degradation", styles["h1"]))
    story.append(
        Paragraph(
            "Enterprise data teams face a fundamental asymmetry: software engineers routinely test code paths with unit "
            "and integration tests, yet data pipelines are typically tested only against clean historical feeds. "
            "When unexpected anomalies emerge, pipelines silently fail:",
            styles["body"],
        )
    )
    story.append(Paragraph("• <b>Ingestion Replay & Duplicate Records:</b> Upstream webhook retries or message queue replays generate duplicate sales or sensor events. Without uniqueness constraints, revenue inflates or machine runtime totals distort without database syntax errors.", styles["bullet"]))
    story.append(Paragraph("• <b>Schema Drift & Null Contamination:</b> Upstream microservices alter field requirements, causing essential fields (unit price, temperature, machine ID) to arrive null, leading to silent drops in SQL aggregate joins.", styles["bullet"]))
    story.append(Paragraph("• <b>Domain Range Violations:</b> Negative prices, negative sensor vibration, or impossible quality pass rates (&gt;100%) skew downstream averages while passing general numeric datatype checks.", styles["bullet"]))
    story.append(Paragraph("• <b>Unchecked Control Totals:</b> Upstream filtering drops records, yet downstream pipelines process the subset without reconciling against expected ingestion counts.", styles["bullet"]))
    story.append(
        Paragraph(
            "<b>The Cost of Silent Failures:</b> Because downstream systems assume clean feeds, corrupt rows infiltrate data "
            "warehouses, skewing financial reporting, triggering erroneous automated inventory replenishments, or corrupting "
            "industrial maintenance forecasting weeks before human auditors notice discrepancies.",
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
        [Paragraph("02", styles["td"]), Paragraph("Domain Profiling", styles["td"]), Paragraph("Computes structural metadata: row/column counts, null distributions, numeric summaries, and evaluates domain compatibility.", styles["td"])],
        [Paragraph("03", styles["td"]), Paragraph("Baseline Metrics", styles["td"]), Paragraph("Calculates clean domain metrics (revenue, orders, or IoT sensor readings/power) from pristine source data.", styles["td"])],
        [Paragraph("04", styles["td"]), Paragraph("Baseline Validation", styles["td"]), Paragraph("Executes active rule suite against pristine dataset to capture existing findings and fingerprints.", styles["td"])],
        [Paragraph("05", styles["td"]), Paragraph("Working Copy Isolation", styles["td"]), Paragraph("Creates independent deep copy (<code>df.copy(deep=True)</code>) to guarantee source dataset immutability.", styles["td"])],
        [Paragraph("06", styles["td"]), Paragraph("Fault Injection", styles["td"]), Paragraph("Injects deterministic synthetic mutation (duplicate row/reading, null sensor, negative measurement, dropped row).", styles["td"])],
        [Paragraph("07", styles["td"]), Paragraph("Mutated Validation", styles["td"]), Paragraph("Runs domain validation rules against mutated copy; isolates newly introduced findings from baseline fingerprints.", styles["td"])],
        [Paragraph("08", styles["td"]), Paragraph("Detection Matching", styles["td"]), Paragraph("Evaluates whether new findings explicitly correspond to injected fault type, target column, and target record.", styles["td"])],
        [Paragraph("09", styles["td"]), Paragraph("Downstream Impact", styles["td"]), Paragraph("Quantifies delta between clean and corrupted metrics (e.g., net revenue error in INR or distortion in units produced).", styles["td"])],
        [Paragraph("10", styles["td"]), Paragraph("Rule Recommendation", styles["td"]), Paragraph("Synthesizes deterministic, explainable validation safeguard configurations to close identified escape gaps.", styles["td"])],
    ]
    t_flow = Table(flow_table_data, colWidths=[35, 115, 354])
    t_flow.setStyle(
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
    story.append(t_flow)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Core Differentiator: Adversarial Safeguard Verification", styles["h2"]))
    story.append(
        Paragraph(
            "Unlike traditional monitoring tools that merely report whether data passes existing rules, DataTripwire "
            "answers: <b>'If an upstream failure occurs, will our current validation rules catch it, or will it slip through unnoticed?'</b> "
            "This empirical verification cycle empowers data engineers to harden pipelines before incidents impact business decisions.",
            styles["body"],
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: PRACTICAL INDUSTRY USE CASES
    # =========================================================================
    story.append(Paragraph("4. Practical Industry Use Cases", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire addresses data reliability across diverse enterprise operational environments:",
            styles["body"],
        )
    )

    use_case_data = [
        [Paragraph("<b>Domain Vertical</b>", styles["th"]), Paragraph("<b>Synthetic Fault Vector</b>", styles["th"]), Paragraph("<b>Downstream Business & Operational Impact</b>", styles["th"]), Paragraph("<b>Evaluated Validation Safeguard</b>", styles["th"])],
        [
            Paragraph("<b>E-Commerce & Retail Sales</b>", styles["td"]),
            Paragraph("Duplicate order row injected (ORD-101 cloned via ingestion retry).", styles["td"]),
            Paragraph("Net revenue falsely inflated (+₹800.00), overstating revenue ledgers and skewing inventory allocation.", styles["td"]),
            Paragraph("Primary-key uniqueness check on <code>transaction_id</code>.", styles["td"]),
        ],
        [
            Paragraph("<b>Manufacturing & Industrial IoT</b>", styles["td"]),
            Paragraph("Duplicate sensor frame or negative vibration reading (-5.0 mm/s).", styles["td"]),
            Paragraph("Distorted machine runtime totals, erroneous predictive maintenance alerts, corrupted overall yield stats.", styles["td"]),
            Paragraph("Composite uniqueness check on <code>(machine_id, timestamp)</code> and non-negative physical bounds.", styles["td"]),
        ],
        [
            Paragraph("<b>FinTech & Banking</b>", styles["td"]),
            Paragraph("Negative transaction amount or missing currency code.", styles["td"]),
            Paragraph("Corrupted balance calculations, flawed ledger reconciliations, erroneous risk threshold alerts.", styles["td"]),
            Paragraph("Non-negative domain boundaries and debit/credit balance constraints.", styles["td"]),
        ],
        [
            Paragraph("<b>Supply Chain & Logistics</b>", styles["td"]),
            Paragraph("Missing transfer quantity in shipment warehouse events.", styles["td"]),
            Paragraph("Silent inventory shrinkage, stockout forecasting failures, delayed reorder triggers.", styles["td"]),
            Paragraph("NOT NULL constraints and positive integer quantity enforcement.", styles["td"]),
        ],
        [
            Paragraph("<b>Machine Learning Feature Stores</b>", styles["td"]),
            Paragraph("Dropped rows during training feature extraction ETL.", styles["td"]),
            Paragraph("Biased model weights, silent class distribution drift, degraded inference accuracy in production.", styles["td"]),
            Paragraph("Expected row count thresholds and control-count reconciliation gates.", styles["td"]),
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
                ("PADDING", (0, 0), (-1, -1), 4.2),
            ]
        )
    )
    story.append(t_uc)
    story.append(Spacer(1, 8))
    story.append(Paragraph("Cross-Industry Commonality", styles["h2"]))
    story.append(
        Paragraph(
            "Across every vertical, the failure pattern is identical: the database accepts the write, the ETL job "
            "exits with status <code>SUCCESS</code>, but analytical truth is compromised. By running DataTripwire "
            "prior to deploying new pipeline code, teams empirically prove that their data checks trigger under stress.",
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
            "domain business logic, and local runtime storage. The multi-domain upgrade introduces a modular "
            "registry and strategy pattern:",
            styles["body"],
        )
    )

    arch_diagram = (
        "+-----------------------------------------------------------------------------------------+<br/>"
        "|                           <b>REACT 19 + TYPESCRIPT FRONTEND (Vite)</b>                       |<br/>"
        "|  +--------------------+  +--------------------+  +------------------+  +----------------+  |<br/>"
        "|  |   UploadView       |  |   ProfileView      |  |  ConfigureView   |  |  ResultsView   |  |<br/>"
        "|  |   (CSV Ingestion)  |  | (Domain Selection) |  |  (Mutation Lab)  |  |  (Forensics)   |  |<br/>"
        "|  +--------------------+  +--------------------+  +------------------+  +----------------+  |<br/>"
        "|         | ThemeContextCore (Daylight / After Hours) | Multi-Domain PipelineIllustration     |<br/>"
        "+--------------------------------------------+--------------------------------------------+<br/>"
        "                                             | HTTP JSON / REST API (Port 8000)<br/>"
        "+--------------------------------------------v--------------------------------------------+<br/>"
        "|                              <b>FASTAPI BACKEND APPLICATION CORE</b>                        |<br/>"
        "|  +-----------------------------------------------------------------------------------+  |<br/>"
        "|  | Routes: /health | /api/v1/domains | /api/v1/datasets | /api/v1/evaluations | OpenAPI   |  |<br/>"
        "|  +-----------------------------------------------------------------------------------+  |<br/>"
        "|                                            | Pydantic v2 Schema Validation               |<br/>"
        "|  +-----------------------------------------v-----------------------------------------+  |<br/>"
        "|  |                               <b>DOMAIN REGISTRY LAYER</b>                              |  |<br/>"
        "|  |  +------------------------------------------------------------------------------+ |  |<br/>"
        "|  |  | DomainRegistry (Auto-detection & Manual Profile Selection)                     | |  |<br/>"
        "|  |  | -> SalesDomainProfile (5 cols, Decimal revenue, 5 sales mutations)           | |  |<br/>"
        "|  |  | -> ManufacturingDomainProfile (18 cols, telemetry metrics, 5 sensor mutators)  | |  |<br/>"
        "|  |  | -> GeneralDomainProfile (Standard tabular profiling, mutations disabled)      | |  |<br/>"
        "|  |  +------------------------------------------------------------------------------+ |  |<br/>"
        "|  |                                            |                                       |  |<br/>"
        "|  |  +-------------------+  +-------------------+  +--------------------------------+ |  |<br/>"
        "|  |  | Dataset Profiler  |  | Mutation Engine   |  | Fingerprint Evaluator          | |  |<br/>"
        "|  |  | (services/        |  | (services/        |  | (services/evaluator.py)        | |  |<br/>"
        "|  |  |  profiler.py)     |  |  mutation_engine) |  | Fingerprint discrepancy match  | |  |<br/>"
        "|  |  +-------------------+  +-------------------+  +--------------------------------+ |  |<br/>"
        "+--+-----------------------------------------+-----------------------------------------+--+<br/>"
        "                                             |<br/>"
        "+--------------------------------------------v--------------------------------------------+<br/>"
        "|                       <b>LOCAL FILE-BASED PERSISTENCE REPOSITORY</b>                           |<br/>"
        "|   data/runtime/datasets/ (Raw CSV & Profiles)   |   data/runtime/evaluations/ (JSON Reports)   |<br/>"
        "+-----------------------------------------------------------------------------------------+"
    )
    story.append(make_callout(arch_diagram, styles, border_color=NAVY_PRIMARY, bg_color=BG_LIGHT))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Core Domain Contracts & Schema Definitions", styles["h2"]))
    contracts_data = [
        [Paragraph("<b>Domain Model</b>", styles["th"]), Paragraph("<b>Module Path</b>", styles["th"]), Paragraph("<b>Purpose & Key Fields</b>", styles["th"])],
        [Paragraph("<code>BaseDomainProfile</code>", styles["code"]), Paragraph("<code>domains.base</code>", styles["td"]), Paragraph("Abstract strategy contract for validation rules, mutations, metrics, and recommendations.", styles["td"])],
        [Paragraph("<code>DomainRegistry</code>", styles["code"]), Paragraph("<code>domains.registry</code>", styles["td"]), Paragraph("Singleton registry resolving domain profiles from column headers or explicit requests.", styles["td"])],
        [Paragraph("<code>MutationItem</code>", styles["code"]), Paragraph("<code>schemas.py</code>", styles["td"]), Paragraph("Defines synthetic fault: <code>mutation_type</code>, <code>target_record_id</code>, <code>target_column</code>, <code>value</code>.", styles["td"])],
        [Paragraph("<code>ValidationRuleConfig</code>", styles["code"]), Paragraph("<code>schemas.py</code>", styles["td"]), Paragraph("Defines rule toggles for sales and manufacturing checkpoints.", styles["td"])],
        [Paragraph("<code>EvaluationReport</code>", styles["code"]), Paragraph("<code>schemas.py</code>", styles["td"]), Paragraph("Complete run summary: <code>mutation_score</code>, <code>metric_deltas</code>, <code>evaluations[]</code>, <code>recommendations[]</code>.", styles["td"])],
    ]
    t_con = Table(contracts_data, colWidths=[120, 110, 274])
    t_con.setStyle(
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
            Paragraph("Domain validation suite executed against <code>df_clean</code> to produce baseline findings <code>F_base</code>.", styles["td"]),
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
            Paragraph("Computes business/operational metrics on <code>df_work</code> vs clean baseline metrics.", styles["td"]),
            Paragraph("Exact metric delta calculation: <code>delta = mutated_val - baseline_val</code>.", styles["td"]),
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
                ("PADDING", (0, 0), (-1, -1), 3.8),
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
            "If an incoming dataset already has an invalid measurement, a synthetic injection into an unrelated row "
            "must not take credit for detecting the preexisting defect. The fingerprint set difference ensures that "
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
            "DataTripwire implements domain-specific synthetic mutation operators representing realistic pipeline failures. "
            "Each operator modifies an isolated in-memory replica deterministically:",
            styles["body"],
        )
    )

    story.append(Paragraph("E-Commerce Sales Domain Mutations", styles["h2"]))
    mutation_data = [
        [Paragraph("<b>Mutation Class</b>", styles["th"]), Paragraph("<b>Target</b>", styles["th"]), Paragraph("<b>Synthetic Operation</b>", styles["th"]), Paragraph("<b>Expected Rule Safeguard</b>", styles["th"])],
        [Paragraph("<code>duplicate_row</code>", styles["code"]), Paragraph("Transaction ID", styles["td"]), Paragraph("Clones entire row (ORD-101) and appends to DataFrame. Simulates ingestion retry replay.", styles["td"]), Paragraph("<code>check_unique_transaction_id</code>", styles["td"])],
        [Paragraph("<code>missing_required_value</code>", styles["code"]), Paragraph("Target Column", styles["td"]), Paragraph("Replaces cell with <code>np.nan</code>. Simulates upstream missing attribute drift.", styles["td"]), Paragraph("<code>check_required_values</code>", styles["td"])],
        [Paragraph("<code>invalid_quantity</code>", styles["code"]), Paragraph("quantity", styles["td"]), Paragraph("Sets quantity to 0 or negative integer (-1). Tests numerical lower bounds.", styles["td"]), Paragraph("<code>check_quantity_positive</code>", styles["td"])],
        [Paragraph("<code>invalid_unit_price</code>", styles["code"]), Paragraph("unit_price", styles["td"]), Paragraph("Sets price to negative float (-100.00). Tests monetary non-negativity.", styles["td"]), Paragraph("<code>check_unit_price_nonnegative</code>", styles["td"])],
        [Paragraph("<code>dropped_row</code>", styles["code"]), Paragraph("Row Index", styles["td"]), Paragraph("Deletes transaction from DataFrame. Tests record count reconciliation.", styles["td"]), Paragraph("<code>check_expected_row_count</code>", styles["td"])],
    ]
    t_mut = Table(mutation_data, colWidths=[110, 80, 175, 139])
    t_mut.setStyle(
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
    story.append(t_mut)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Manufacturing / Industrial IoT Domain Mutations", styles["h2"]))
    mfg_mutation_data = [
        [Paragraph("<b>Mutation Class</b>", styles["th"]), Paragraph("<b>Target</b>", styles["th"]), Paragraph("<b>Synthetic Operation</b>", styles["th"]), Paragraph("<b>Expected Rule Safeguard</b>", styles["th"])],
        [Paragraph("<code>duplicate_sensor_reading</code>", styles["code"]), Paragraph("Reading ID", styles["td"]), Paragraph("Clones entire telemetry frame (e.g. RDG-01-0001). Simulates sensor network replay.", styles["td"]), Paragraph("<code>check_machine_timestamp_unique</code>", styles["td"])],
        [Paragraph("<code>missing_sensor_value</code>", styles["code"]), Paragraph("Sensor Field", styles["td"]), Paragraph("Replaces sensor reading (e.g. temperature_c) with null. Tests telemetry non-null rules.", styles["td"]), Paragraph("<code>check_required_values</code>", styles["td"])],
        [Paragraph("<code>invalid_sensor_value</code>", styles["code"]), Paragraph("Sensor Field", styles["td"]), Paragraph("Sets measurement to negative or out-of-bounds value (e.g. vibration: -5.0 mm/s).", styles["td"]), Paragraph("<code>check_non_negative_measurements</code>", styles["td"])],
        [Paragraph("<code>dropped_sensor_reading</code>", styles["code"]), Paragraph("Reading ID", styles["td"]), Paragraph("Deletes sensor reading from working DataFrame. Tests stream reconciliation.", styles["td"]), Paragraph("<code>check_expected_record_count</code>", styles["td"])],
        [Paragraph("<code>invalid_production_value</code>", styles["code"]), Paragraph("Units/Defects", styles["td"]), Paragraph("Sets defect_count > units_produced (e.g. 50 defects on 10 units).", styles["td"]), Paragraph("<code>check_production_consistency</code>", styles["td"])],
    ]
    t_mfg_mut = Table(mfg_mutation_data, colWidths=[110, 80, 175, 139])
    t_mfg_mut.setStyle(
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
    story.append(t_mfg_mut)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 8: VALIDATION AND DETECTION LOGIC
    # =========================================================================
    story.append(Paragraph("8. Validation Engine & Fault Detection Logic", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire provides configurable validation rules across transactional sales and industrial telemetry pipelines:",
            styles["body"],
        )
    )

    story.append(Paragraph("Manufacturing & Industrial IoT Validation Rules", styles["h2"]))
    mfg_val_rules = [
        [Paragraph("<b>Rule Code</b>", styles["th"]), Paragraph("<b>Rule Name & Type</b>", styles["th"]), Paragraph("<b>Target Fields</b>", styles["th"]), Paragraph("<b>Detection & Invariant Condition</b>", styles["th"])],
        [Paragraph("<code>RULE_MFG_COMPOSITE_UNIQUE</code>", styles["code"]), Paragraph("Machine & Timestamp Unique", styles["td"]), Paragraph("<code>machine_id, timestamp</code>", styles["td"]), Paragraph("Flags duplicate <code>(machine_id, timestamp)</code> pairs (key demo safeguard).", styles["td"])],
        [Paragraph("<code>RULE_MFG_READING_ID_UNIQUE</code>", styles["code"]), Paragraph("Reading ID Uniqueness", styles["td"]), Paragraph("<code>reading_id</code>", styles["td"]), Paragraph("Flags duplicate <code>reading_id</code> values across sensor stream.", styles["td"])],
        [Paragraph("<code>RULE_MFG_NON_NEGATIVE</code>", styles["code"]), Paragraph("Non-Negative Measurements", styles["td"]), Paragraph("pressure, vibration, current, power", styles["td"]), Paragraph("Enforces physical values &ge; 0 (detects sensor drift or sign errors).", styles["td"])],
        [Paragraph("<code>RULE_MFG_PROD_CONSISTENCY</code>", styles["code"]), Paragraph("Production Consistency", styles["td"]), Paragraph("<code>units_produced, defect_count</code>", styles["td"]), Paragraph("Verifies <code>defect_count &le; units_produced</code>; handles zero production.", styles["td"])],
        [Paragraph("<code>RULE_MFG_TEMP_BOUNDS</code>", styles["code"]), Paragraph("Operating Temperature Limits", styles["td"]), Paragraph("<code>temperature_c</code>", styles["td"]), Paragraph("Checks operating temperature stays within configurable range [40°C - 95°C].", styles["td"])],
        [Paragraph("<code>RULE_MFG_PASS_RATE_RANGE</code>", styles["code"]), Paragraph("Quality Pass Rate Range", styles["td"]), Paragraph("<code>quality_pass_rate_pct</code>", styles["td"]), Paragraph("Enforces yield percentage is strictly within [0.0, 100.0%].", styles["td"])],
    ]
    t_mfg_val = Table(mfg_val_rules, colWidths=[110, 115, 110, 169])
    t_mfg_val.setStyle(
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
    story.append(t_mfg_val)
    story.append(Spacer(1, 6))

    story.append(Paragraph("E-Commerce Sales Validation Rules", styles["h2"]))
    sales_val_rules = [
        [Paragraph("<b>Rule Code</b>", styles["th"]), Paragraph("<b>Rule Name & Type</b>", styles["th"]), Paragraph("<b>Target Fields</b>", styles["th"]), Paragraph("<b>Detection & Invariant Condition</b>", styles["th"])],
        [Paragraph("<code>RULE_UNIQUE_TRANSACTION_ID</code>", styles["code"]), Paragraph("Transaction Uniqueness", styles["td"]), Paragraph("<code>transaction_id</code>", styles["td"]), Paragraph("Flags duplicate transactions; disabled in baseline to demonstrate escape.", styles["td"])],
        [Paragraph("<code>RULE_QUANTITY_POSITIVE</code>", styles["code"]), Paragraph("Positive Quantity", styles["td"]), Paragraph("<code>quantity</code>", styles["td"]), Paragraph("Enforces <code>quantity &gt; 0</code> (detects cancellations entered as sales).", styles["td"])],
        [Paragraph("<code>RULE_UNIT_PRICE_NONNEGATIVE</code>", styles["code"]), Paragraph("Non-Negative Price", styles["td"]), Paragraph("<code>unit_price</code>", styles["td"]), Paragraph("Enforces <code>unit_price &ge; 0.00</code> (detects negative promotional glitches).", styles["td"])],
        [Paragraph("<code>RULE_REQUIRED_VALUES</code>", styles["code"]), Paragraph("Required Non-Null", styles["td"]), Paragraph("Essential sales columns", styles["td"]), Paragraph("Flags missing values or whitespace in mandatory dimensions.", styles["td"])],
    ]
    t_sales_val = Table(sales_val_rules, colWidths=[110, 115, 110, 169])
    t_sales_val.setStyle(
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
    story.append(t_sales_val)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 9: BUSINESS METRICS AND SCORING FORMULATION
    # =========================================================================
    story.append(Paragraph("9. Business Metrics & Mutation Scoring Formulation", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire calculates real metrics from uploaded datasets rather than rendering hardcoded or synthetic dummy outputs. "
            "Metric calculations dynamically adapt to the active domain:",
            styles["body"],
        )
    )

    story.append(Paragraph("Domain Metric Formulations", styles["h2"]))
    math_box = (
        "<b>1. E-Commerce Sales Domain:</b><br/>"
        "   • <code>Revenue = SUM( Decimal(quantity_i) * Decimal(unit_price_i) )</code> quantized to <code>Decimal('0.01')</code><br/>"
        "   • <code>AOV = Revenue / Decimal(Transaction Count)</code> (handles zero transactions safely)<br/><br/>"
        "<b>2. Manufacturing & Industrial IoT Domain:</b><br/>"
        "   • <code>Total Readings</code>, <code>Unique Machines</code>, <code>Unique Facilities</code><br/>"
        "   • <code>Total Production Units = SUM(units_produced)</code> · <code>Total Defects = SUM(defect_count)</code><br/>"
        "   • <code>Total Energy (kWh) = SUM(energy_kwh_20min)</code> across distinct reporting intervals<br/>"
        "   • <code>Average Operating Temperature (°C)</code>, <code>Max Temperature</code>, <code>Average Vibration (mm/s)</code><br/>"
        "   • <code>Quality Pass Rate (%) = MEAN(quality_pass_rate_pct)</code><br/><br/>"
        "<b>3. Mutation Scoring Formulation:</b><br/>"
        "   <code>Mutation Score (%) = (Detected Eligible Mutations / Total Eligible Applied Mutations) * 100</code>"
    )
    story.append(make_callout(math_box, styles, border_color=NAVY_PRIMARY, bg_color=BG_LIGHT))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Scoring Classification Summary Table", styles["h2"]))
    score_table_data = [
        [Paragraph("<b>Status Category</b>", styles["th"]), Paragraph("<b>Engine Condition</b>", styles["th"]), Paragraph("<b>Score Effect</b>", styles["th"]), Paragraph("<b>System Action</b>", styles["th"])],
        [Paragraph("<b>Detected</b>", styles["td"]), Paragraph("<code>applied=True, detected=True</code>", styles["td"]), Paragraph("Increments Numerator & Denominator", styles["td"]), Paragraph("Safeguard validated; metrics protected.", styles["td"])],
        [Paragraph("<b>Surviving</b>", styles["td"]), Paragraph("<code>applied=True, detected=False</code>", styles["td"]), Paragraph("Increments Denominator ONLY", styles["td"]), Paragraph("<b>Vulnerability flagged; synthesizes rule recommendation.</b>", styles["td"])],
        [Paragraph("<b>Unapplied</b>", styles["td"]), Paragraph("<code>applied=False</code>", styles["td"]), Paragraph("<b>Excluded</b> from Score", styles["td"]), Paragraph("Logged as error; does not distort score ratio.", styles["td"])],
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
        [Paragraph("<b>Method & Path</b>", styles["th"]), Paragraph("<b>Purpose</b>", styles["th"]), Paragraph("<b>Request / Params</b>", styles["th"]), Paragraph("<b>Success Response</b>", styles["th"])],
        [
            Paragraph("<code>GET /health</code><br/><code>GET /api/v1/health</code>", styles["code"]),
            Paragraph("Service readiness health check.", styles["td"]),
            Paragraph("None", styles["td"]),
            Paragraph("<code>200 OK</code> · HealthResponse (status: 'ok', version: '0.1.0')", styles["td"]),
        ],
        [
            Paragraph("<code>GET /api/v1/domains</code>", styles["code"]),
            Paragraph("Lists all registered domain profiles.", styles["td"]),
            Paragraph("None", styles["td"]),
            Paragraph("<code>200 OK</code> · List[DomainMetadata] (sales, manufacturing, general)", styles["td"]),
        ],
        [
            Paragraph("<code>POST /api/v1/datasets/sample</code>", styles["code"]),
            Paragraph("Loads bundled 15-record sales dataset.", styles["td"]),
            Paragraph("None", styles["td"]),
            Paragraph("<code>201 Created</code> · DatasetResponse", styles["td"]),
        ],
        [
            Paragraph("<code>POST /api/v1/datasets/sample-manufacturing</code>", styles["code"]),
            Paragraph("Loads bundled 20-record IoT dataset.", styles["td"]),
            Paragraph("None", styles["td"]),
            Paragraph("<code>201 Created</code> · DatasetResponse (is_manufacturing_compatible: true)", styles["td"]),
        ],
        [
            Paragraph("<code>POST /api/v1/datasets</code>", styles["code"]),
            Paragraph("Uploads & profiles arbitrary CSV dataset.", styles["td"]),
            Paragraph("Multipart form: <code>file</code> (.csv)", styles["td"]),
            Paragraph("<code>201 Created</code> · DatasetResponse with detected_domain", styles["td"]),
        ],
        [
            Paragraph("<code>GET /api/v1/datasets/{id}/domains</code>", styles["code"]),
            Paragraph("Evaluates dataset domain compatibility matrix.", styles["td"]),
            Paragraph("Path: <code>dataset_id</code>", styles["td"]),
            Paragraph("<code>200 OK</code> · DomainCompatibilityResponse", styles["td"]),
        ],
        [
            Paragraph("<code>POST /api/v1/datasets/{id}/evaluations</code>", styles["code"]),
            Paragraph("Executes domain-aware mutation testing batch.", styles["td"]),
            Paragraph("JSON: <code>domain</code>, <code>mutations[]</code>, <code>rules{}</code>", styles["td"]),
            Paragraph("<code>201 Created</code> · EvaluationReport with domain metrics", styles["td"]),
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
                ("PADDING", (0, 0), (-1, -1), 3.8),
            ]
        )
    )
    story.append(t_api)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Multi-Domain Evaluation Request Payload", styles["h2"]))
    req_json = (
        "POST /api/v1/datasets/{id}/evaluations<br/>"
        "{\n"
        "  \"domain\": \"manufacturing\",\n"
        "  \"mutations\": [\n"
        "    {\"mutation_type\": \"duplicate_sensor_reading\", \"target_record_id\": \"RDG-01-0001\"}\n"
        "  ],\n"
        "  \"rules\": {\n"
        "    \"check_machine_timestamp_unique\": false, \"check_non_negative_measurements\": true\n"
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
            "Built with React 19, TypeScript, and Vite, the UI adheres to rigorous design-system tokens and adapts dynamically across domains:",
            styles["body"],
        )
    )

    story.append(Paragraph("Four-Stage Workflow Navigation", styles["h2"]))
    story.append(Paragraph("1. <b>01 Ingest:</b> Drag-and-drop CSV ingestion zone with instant format validation, plus instant demo buttons for Retail Sales and Industrial IoT.", styles["bullet"]))
    story.append(Paragraph("2. <b>02 Profile:</b> Structural column breakdown, null counts, numeric summaries, and dynamic domain selector pills (Sales, Manufacturing, General).", styles["bullet"]))
    story.append(Paragraph("3. <b>03 Mutation Lab:</b> Domain-aware fault synthesizer rendering relevant mutation types and safeguards (with key demo pivot switches).", styles["bullet"]))
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

    story.append(Paragraph("Domain-Adaptive SVG Pipeline Visualization", styles["h2"]))
    story.append(
        Paragraph(
            "The top header features a custom interactive SVG pipeline visualizer (<code>PipelineIllustration.tsx</code>) "
            "rendering real-time pipeline topology. When the manufacturing domain is active, the visualization renders "
            "industrial telemetry streams (<code>Raw Telemetry Input &rarr; Sensor Mutation Crash Zone &rarr; Validation Gate &rarr; Protected Telemetry Output</code>).",
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
            "The batch file determines the repository root dynamically, verifies Python and Node.js in PATH, "
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
        [Paragraph("<code>BACKEND_PORT</code>", styles["code"]), Paragraph("<code>8000</code>", styles["td"]), Paragraph("Backend FastAPI server listening port.", styles["td"])],
        [Paragraph("<code>MAX_FILE_SIZE_MB</code>", styles["code"]), Paragraph("<code>10</code>", styles["td"]), Paragraph("Maximum allowed CSV upload size (in megabytes).", styles["td"])],
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
                ("PADDING", (0, 0), (-1, -1), 3.8),
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
            Paragraph("140 tests: sales and manufacturing validation, mutations, metrics, evaluations, recommendations, and the full 5,040-row dataset.", styles["td"]),
            Paragraph("<b>140 passed</b> in 5.8s (0 failures, 0 regressions)", styles["td"]),
        ],
        [
            Paragraph("<b>Frontend Linting</b>", styles["td"]),
            Paragraph("oxlint 1.81+ (multi-threaded)", styles["td"]),
            Paragraph("15 files, 116 rules: syntax, React hooks, imports, type hygiene.", styles["td"]),
            Paragraph("<b>0 errors, 0 warnings</b> in 51ms", styles["td"]),
        ],
        [
            Paragraph("<b>TypeScript & Build</b>", styles["td"]),
            Paragraph("tsc -b && vite build", styles["td"]),
            Paragraph("Strict typechecking and production asset bundling.", styles["td"]),
            Paragraph("<b>Compiled cleanly</b> in 151ms (0 errors)", styles["td"]),
        ],
        [
            Paragraph("<b>End-to-End Workflow</b>", styles["td"]),
            Paragraph("Browser Subagent / Automation", styles["td"]),
            Paragraph("Full user journeys across both Sales and Manufacturing IoT demo workflows.", styles["td"]),
            Paragraph("<b>Verified end-to-end</b> with real browser execution", styles["td"]),
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
                ("PADDING", (0, 0), (-1, -1), 4.2),
            ]
        )
    )
    story.append(t_test)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Backend Test Suite Module Breakdown", styles["h2"]))
    mod_breakdown_data = [
        [Paragraph("<b>Test Module</b>", styles["th"]), Paragraph("<b>Coverage Focus</b>", styles["th"]), Paragraph("<b>Test Count</b>", styles["th"])],
        [Paragraph("<code>tests/unit/test_manufacturing.py</code>", styles["code"]), Paragraph("Manufacturing schema recognition, 11 telemetry validation rules, 5 mutations, metrics, recommendations", styles["td"]), Paragraph("20 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/integration/test_manufacturing_workflow.py</code>", styles["code"]), Paragraph("Full 5,040-row real dataset verification, domain API routes, immutability, reproducibility", styles["td"]), Paragraph("5 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/integration/test_api.py</code>", styles["code"]), Paragraph("FastAPI endpoints, CORS, upload validation, domain compatibility, 404/422 error handlers", styles["td"]), Paragraph("15 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/unit/test_validators.py</code>", styles["code"]), Paragraph("Sales validation rules, boundary conditions, expected row count mismatches", styles["td"]), Paragraph("10 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/unit/test_mutation_engine.py</code>", styles["code"]), Paragraph("Deep copy isolation, 5 sales mutation operators, reproducibility seed, invalid targets", styles["td"]), Paragraph("8 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/unit/test_evaluator.py</code>", styles["code"]), Paragraph("Finding fingerprinting, baseline isolation, multi-point detection matching", styles["td"]), Paragraph("11 tests (100% pass)", styles["td"])],
        [Paragraph("<code>tests/test_domain_models.py</code>", styles["code"]), Paragraph("Pydantic v2 data models, validation contracts, domain enum serialization", styles["td"]), Paragraph("30 tests (100% pass)", styles["td"])],
    ]
    t_mod = Table(mod_breakdown_data, colWidths=[150, 254, 100])
    t_mod.setStyle(
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
    story.append(t_mod)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 14: SAMPLE DATASETS & DEMONSTRATION SCENARIOS
    # =========================================================================
    story.append(Paragraph("14. Sample Datasets & Demonstration Scenarios", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire includes curated, clean synthetic datasets organized under <code>data/samples/</code> "
            "for reproducibility and demonstration. All baseline datasets are pristine; faults are injected exclusively in memory:",
            styles["body"],
        )
    )

    ds_cat_data = [
        [Paragraph("<b>Dataset Filename</b>", styles["th"]), Paragraph("<b>Domain Profile</b>", styles["th"]), Paragraph("<b>Records / Cols</b>", styles["th"]), Paragraph("<b>Size</b>", styles["th"]), Paragraph("<b>Evaluation Purpose & Characteristics</b>", styles["th"])],
        [
            Paragraph("<code>ecommerce_showcase_2500.csv</code>", styles["code"]),
            Paragraph("E-Commerce Sales", styles["td"]),
            Paragraph("2,500 rows · 10 cols", styles["td"]),
            Paragraph("226 KB", styles["td"]),
            Paragraph("High-scale retail testing: duplicate orders, price/quantity corruptions, downstream revenue drift.", styles["td"]),
        ],
        [
            Paragraph("<code>manufacturing_iot_sensor_readings_5040.csv</code>", styles["code"]),
            Paragraph("Industrial IoT", styles["td"]),
            Paragraph("5,040 rows · 18 cols", styles["td"]),
            Paragraph("824 KB", styles["td"]),
            Paragraph("Industrial equipment telemetry: composite machine/timestamp uniqueness, sensor drift, energy kWh.", styles["td"]),
        ],
        [
            Paragraph("<code>realistic_sales_test.csv</code>", styles["code"]),
            Paragraph("E-Commerce Sales", styles["td"]),
            Paragraph("60 rows · 5 cols", styles["td"]),
            Paragraph("2.7 KB", styles["td"]),
            Paragraph("Compact deterministic sales fixture for rapid integration testing.", styles["td"]),
        ],
    ]
    t_dsc = Table(ds_cat_data, colWidths=[120, 80, 85, 45, 174])
    t_dsc.setStyle(
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
    story.append(t_dsc)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Dual End-to-End Demonstration Walkthrough", styles["h2"]))
    demo_steps = [
        [Paragraph("<b>Workflow Step</b>", styles["th"]), Paragraph("<b>E-Commerce Sales Scenario</b>", styles["th"]), Paragraph("<b>Manufacturing IoT Scenario</b>", styles["th"])],
        [
            Paragraph("1. Load Baseline", styles["td"]),
            Paragraph("Load 15-tx sales demo (Revenue: ₹19,000.00).", styles["td"]),
            Paragraph("Load 20-rdg IoT demo (Units: 156, Energy: 47.6 kWh).", styles["td"]),
        ],
        [
            Paragraph("2. Injected Fault", styles["td"]),
            Paragraph("Duplicate transaction ORD-101 (+₹1,000 revenue impact).", styles["td"]),
            Paragraph("Duplicate sensor frame RDG-01-0001 (telemetry replay).", styles["td"]),
        ],
        [
            Paragraph("3. Vulnerability Run", styles["td"]),
            Paragraph("Uniqueness OFF &rarr; <b>Score: 0% (Survived)</b> · Revenue drifts to ₹20,000 (+₹1,000 error).", styles["td"]),
            Paragraph("Composite Uniqueness OFF &rarr; <b>Score: 0% (Survived)</b> · Telemetry stream leaked undetected.", styles["td"]),
        ],
        [
            Paragraph("4. Recommendation", styles["td"]),
            Paragraph("Recommends: <code>check_unique_transaction_id</code>.", styles["td"]),
            Paragraph("Recommends: <code>check_machine_timestamp_unique</code>.", styles["td"]),
        ],
        [
            Paragraph("5. Hardened Run", styles["td"]),
            Paragraph("Click 'Test Safeguard' &rarr; <b>Score: 100% (Trapped ✓)</b> · Revenue protected at ₹19,000 (₹0 drift).", styles["td"]),
            Paragraph("Click 'Test Safeguard' &rarr; <b>Score: 100% (Trapped ✓)</b> · Telemetry frame blocked; 0 drift.", styles["td"]),
        ],
    ]
    t_demo = Table(demo_steps, colWidths=[80, 212, 212])
    t_demo.setStyle(
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
    story.append(t_demo)
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
            Paragraph("<b>Impact Measurement</b>", styles["td"]),
            Paragraph("Reports pass/fail counts; rarely quantifies financial or operational distortion.", styles["td"]),
            Paragraph("<b>Measures exact metric error</b> (e.g. INR revenue discrepancy or production delta).", styles["td"]),
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
                ("PADDING", (0, 0), (-1, -1), 3.8),
            ]
        )
    )
    story.append(t_diff)
    story.append(Spacer(1, 8))

    story.append(Paragraph("16. Security, Local Privacy & Architectural Boundaries", styles["h1"]))
    story.append(Paragraph("• <b>100% Local Processing & Zero External Telemetry:</b> No dataset contents, column names, or evaluation metrics are transmitted to cloud services, third-party APIs, or external LLMs.", styles["bullet"]))
    story.append(Paragraph("• <b>Strict Ingestion Guardrails:</b> File upload bounds (10 MB max default), extension enforcement (.csv only), UTF-8 / Latin-1 encoding detection, and boundary checks (50,000 rows max, 100 columns max).", styles["bullet"]))
    story.append(Paragraph("• <b>Safe Filesystem Repositories:</b> Storage paths are sanitized and isolated in <code>data/runtime/</code>; directory traversal via filenames is strictly prevented.", styles["bullet"]))

    story.append(Paragraph("Current Architectural Limitations (Honest Disclosure)", styles["h2"]))
    story.append(Paragraph("1. <b>Tabular CSV Scope:</b> The current engine parses tabular CSV files. Parquet, Delta Lake, Apache Iceberg, and direct SQL warehouse connectors are planned for future phases.", styles["bullet"]))
    story.append(Paragraph("2. <b>Configurable Testing Model, Not Industrial Safety DCS:</b> The manufacturing profile is a data-pipeline reliability testing tool, not a certified real-time SCADA/DCS plant shutdown safety system.", styles["bullet"]))
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
            Paragraph("• Parquet/JSON ingestion drivers.<br/>• Headless CLI command (<code>datatripwire run --ci</code>) for GitHub Actions / GitLab CI.<br/>• Additional domain adapters (Healthcare HL7, FinTech Fix/SWIFT).", styles["td"]),
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
                ("PADDING", (0, 0), (-1, -1), 3.8),
            ]
        )
    )
    story.append(t_road)
    story.append(Spacer(1, 6))

    story.append(Paragraph("18. Engineering Conclusion", styles["h1"]))
    story.append(
        Paragraph(
            "DataTripwire establishes that mutation testing is not only viable for data pipelines, but essential. "
            "By systematically introducing controlled data corruptions into isolated in-memory replicas across retail sales "
            "and industrial telemetry, data teams replace ungrounded assumptions with empirical confidence. The completed platform "
            "demonstrates that catching a data fault is only half the battle: understanding the exact financial and operational "
            "magnitude of silent escapes provides the business justification necessary to prioritize data reliability engineering.",
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
            Paragraph("Runs full test suite: <code>python scripts/run_tests.py</code> (140 pytest + oxlint + vite).", styles["td"]),
        ],
        [
            Paragraph("<code>data/samples/</code>", styles["code"]),
            Paragraph("Sample Datasets", styles["td"]),
            Paragraph("Catalog containing 2,500-row sales and 5,040-row manufacturing IoT CSV fixtures.", styles["td"]),
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
                ("PADDING", (0, 0), (-1, -1), 3.2),
            ]
        )
    )
    story.append(t_app)
    story.append(Spacer(1, 5))

    # Attestation Signature Box
    attest_box = (
        "<b>20. Document Attestation & Verification Record</b><br/>"
        "• <b>Repository:</b> https://github.com/rahulgoreofficial/DataTripwire-Data-Pipeline-Reliability-Mutation-Testing<br/>"
        "• <b>Verification Status:</b> 140 / 140 backend tests passed · 0 frontend lint warnings · 0 build errors<br/>"
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
