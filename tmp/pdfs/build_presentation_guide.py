from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf" / "cloudalloc_30_percent_four_person_guide.pdf"

NAVY = HexColor("#13213C")
BLUE = HexColor("#2563EB")
CYAN = HexColor("#06B6D4")
GREEN = HexColor("#16A36A")
AMBER = HexColor("#D97706")
RED = HexColor("#C2414A")
INK = HexColor("#172033")
MUTED = HexColor("#5F6B7A")
PALE = HexColor("#F3F6FA")
LIGHT_BLUE = HexColor("#EAF1FF")
LIGHT_GREEN = HexColor("#E9F8F1")
LIGHT_AMBER = HexColor("#FFF5E7")
LINE = HexColor("#D9E0EA")
WHITE = colors.white


def register_fonts():
    candidates = {
        "Inter": Path("C:/Windows/Fonts/arial.ttf"),
        "Inter-Bold": Path("C:/Windows/Fonts/arialbd.ttf"),
        "Mono": Path("C:/Windows/Fonts/consola.ttf"),
        "Mono-Bold": Path("C:/Windows/Fonts/consolab.ttf"),
    }
    for name, path in candidates.items():
        if path.exists():
            pdfmetrics.registerFont(TTFont(name, str(path)))


register_fonts()


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", fontName="Inter-Bold", fontSize=27, leading=32,
    textColor=WHITE, alignment=TA_LEFT, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CoverSub", fontName="Inter", fontSize=12, leading=18,
    textColor=HexColor("#D9E7FF"), spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="H1x", fontName="Inter-Bold", fontSize=20, leading=24,
    textColor=NAVY, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="H2x", fontName="Inter-Bold", fontSize=12.5, leading=16,
    textColor=BLUE, spaceBefore=6, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Bodyx", fontName="Inter", fontSize=9.4, leading=13.6,
    textColor=INK, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="Smallx", fontName="Inter", fontSize=7.7, leading=10.3,
    textColor=MUTED, spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="Bulletx", fontName="Inter", fontSize=9.2, leading=13.2,
    leftIndent=10, firstLineIndent=-8, textColor=INK, spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="Calloutx", fontName="Inter", fontSize=9.2, leading=13.2,
    textColor=INK,
))
styles.add(ParagraphStyle(
    name="Chipx", fontName="Inter-Bold", fontSize=8, leading=10,
    textColor=WHITE, alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    name="Codex", fontName="Mono", fontSize=7.3, leading=10.2,
    textColor=INK,
))
styles.add(ParagraphStyle(
    name="TableHead", fontName="Inter-Bold", fontSize=7.5, leading=9.5,
    textColor=WHITE,
))
styles.add(ParagraphStyle(
    name="TableBody", fontName="Inter", fontSize=7.15, leading=9.5,
    textColor=INK,
))
styles.add(ParagraphStyle(
    name="Quote", fontName="Inter-Bold", fontSize=11.5, leading=16,
    textColor=NAVY, alignment=TA_CENTER,
))


def P(text: str, style="Bodyx"):
    return Paragraph(text, styles[style])


def bullet(text: str):
    return P(f"- {text}", "Bulletx")


def heading(title: str, kicker: str | None = None):
    items = []
    if kicker:
        items.append(P(kicker.upper(), "Smallx"))
    items.extend([P(title, "H1x"), HRFlowable(width="100%", thickness=1.2, color=CYAN, spaceAfter=10)])
    return items


def speaker_chip(label: str, color=BLUE):
    return Table([[P(label, "Chipx")]], colWidths=[44 * mm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("BOX", (0, 0), (-1, -1), 0, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))


def callout(title: str, text: str, color=BLUE, background=LIGHT_BLUE):
    content = P(f"<b>{escape(title)}</b><br/>{text}", "Calloutx")
    return Table([[content]], colWidths=[174 * mm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.8, color),
        ("LINEBEFORE", (0, 0), (0, -1), 4, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))


def code_block(lines: str):
    block = XPreformatted(escape(lines), styles["Codex"])
    return Table([[block]], colWidths=[174 * mm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F7F9FC")),
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))


def info_table(headers, rows, widths, font_size=7.15):
    header = [P(escape(str(item)), "TableHead") for item in headers]
    body = [[P(str(item), "TableBody") for item in row] for row in rows]
    table = Table([header] + body, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def two_columns(left, right, widths=(85 * mm, 85 * mm)):
    table = Table([[left, right]], colWidths=list(widths), hAlign="LEFT")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 5),
        ("LEFTPADDING", (1, 0), (1, 0), 5),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    return table


class GuideDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=20 * mm,
            bottomMargin=17 * mm,
            title="CloudAlloc 30 Percent Milestone - Four Person Presentation Guide",
            author="CloudAlloc Project Team",
            subject="Presentation and live demonstration guide",
        )
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        self.addPageTemplates(PageTemplate(id="guide", frames=frame, onPage=self.decorate))

    def decorate(self, canvas, doc):
        width, height = A4
        if doc.page == 1:
            canvas.saveState()
            canvas.setFillColor(NAVY)
            canvas.rect(0, 0, width, height, fill=1, stroke=0)
            canvas.setFillColor(CYAN)
            canvas.rect(0, height - 11 * mm, width, 11 * mm, fill=1, stroke=0)
            canvas.setFillColor(BLUE)
            canvas.circle(width - 28 * mm, 34 * mm, 33 * mm, fill=1, stroke=0)
            canvas.setFillColor(CYAN)
            canvas.circle(width - 10 * mm, 13 * mm, 18 * mm, fill=1, stroke=0)
            canvas.restoreState()
            return
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, height - 10 * mm, width, 10 * mm, fill=1, stroke=0)
        canvas.setFont("Inter-Bold", 7.5)
        canvas.setFillColor(WHITE)
        canvas.drawString(18 * mm, height - 6.6 * mm, "CLOUDALLOC - 30% MILESTONE PRESENTATION GUIDE")
        canvas.setStrokeColor(LINE)
        canvas.line(18 * mm, 13 * mm, width - 18 * mm, 13 * mm)
        canvas.setFont("Inter", 7.2)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 8.5 * mm, "Predictive CPU and memory allocation research prototype")
        canvas.drawRightString(width - 18 * mm, 8.5 * mm, f"Page {doc.page}")
        canvas.restoreState()


story = []

# Cover
story.extend([
    Spacer(1, 43 * mm),
    P("CloudAlloc", "CoverTitle"),
    P("Predictive CPU and Memory Allocation for Cloud Workloads", "CoverTitle"),
    Spacer(1, 4 * mm),
    P("30% milestone - four-person explanation and live demonstration guide", "CoverSub"),
    Spacer(1, 15 * mm),
    Table([
        [P("PRESENTATION", "Chipx"), P("CURRENT BUILD", "Chipx"), P("DEMO READY", "Chipx")],
        [P("4 speakers / 18-22 min", "CoverSub"), P("Foundation milestone only", "CoverSub"), P("SQLite fixture workflow", "CoverSub")],
    ], colWidths=[55 * mm, 55 * mm, 55 * mm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("BOX", (0, 0), (-1, -1), 0.7, HexColor("#50617E")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, HexColor("#50617E")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ])),
    Spacer(1, 18 * mm),
    P("Use this document as speaking notes, a viva reference, and the exact runbook for demonstrating what is implemented today.", "CoverSub"),
    Spacer(1, 7 * mm),
    P("Important: generated fixture results prove software behavior. They are not empirical findings about real Google workloads.", "CoverSub"),
    PageBreak(),
])

# Session map
story.extend(heading("Presentation map and current scope", "Team overview"))
story.append(info_table(
    ["Speaker", "Time", "Primary responsibility", "Handoff line"],
    [
        ["Person 1", "4-5 min", "Problem, research gap, objectives, dataset, and methodology", "Now we will show how that research design becomes a system."],
        ["Person 2", "4-5 min", "Architecture, preprocessing, database, manifest, and reproducibility", "With clean data stored, the next question is what the current analysis can prove."],
        ["Person 3", "4-5 min", "EDA, persistence baseline, API, tests, results, and code walkthrough", "The final speaker will run the complete current workflow live."],
        ["Person 4", "5-7 min", "Live setup, commands, output interpretation, limitations, and next 70%", "That completes the implemented 30% foundation."],
    ],
    [25 * mm, 20 * mm, 91 * mm, 38 * mm],
))
story.append(Spacer(1, 8 * mm))
left = [P("What exists now", "H2x"),
        bullet("Google trace streaming preprocessor and normalized Parquet contract."),
        bullet("Checksum manifest and chronological train/validation/test labels."),
        bullet("PostgreSQL-ready relational schema with SQLite demonstration mode."),
        bullet("Idempotent ingestion, training-only EDA, persistence baseline."),
        bullet("Health and workload-summary endpoints plus 13 automated tests.")]
right = [P("What does not exist yet", "H2x"),
         bullet("Ridge, random forest, and gradient-boosting experiments."),
         bullet("Static/reactive/predictive/oracle allocation simulator."),
         bullet("Waste, deficit, utilization, churn, and confidence intervals."),
         bullet("Recommendation endpoint and final analytics dashboard."),
         bullet("Real-trace empirical conclusions.")]
story.append(two_columns(left, right))
story.append(Spacer(1, 8 * mm))
story.append(callout(
    "One-sentence project description",
    "CloudAlloc is a reproducible research prototype that prepares cloud workload traces and establishes a leakage-safe baseline before later converting CPU and memory forecasts into allocation recommendations.",
    GREEN, LIGHT_GREEN,
))
story.append(PageBreak())

# Person 1 page 1
story.extend(heading("Person 1 - problem, gap, and purpose", "Speaker section 1 of 4"))
story.append(speaker_chip("PERSON 1 - RESEARCH LEAD", BLUE))
story.append(Spacer(1, 6 * mm))
story.append(P("Suggested opening", "H2x"))
story.append(callout(
    "Say this first",
    "Cloud workloads do not use a constant amount of CPU or memory. If resources are fixed too high, capacity is wasted. If they are fixed too low, performance and reliability suffer. Reactive scaling also acts only after demand changes.",
    BLUE, LIGHT_BLUE,
))
story.append(P("Points to explain", "H2x"))
for text in [
    "Static allocation reserves capacity for a demand level that may not occur.",
    "Reactive threshold methods have a one-step delay: they observe pressure first and respond afterward.",
    "Forecasting alone is not enough. A model may have low average error but still under-predict peaks that matter for allocation.",
    "The research gap is the missing link between prediction quality and operational outcomes on the same public workload trace.",
    "The project therefore evaluates prediction and, in later milestones, allocation waste and shortage together.",
]:
    story.append(bullet(text))
story.append(P("Research questions", "H2x"))
story.append(info_table(
    ["#", "Question"],
    [
        ["1", "How accurately can next-interval maximum CPU and memory demand be predicted?"],
        ["2", "Can predictive allocation reduce waste relative to static requests?"],
        ["3", "Can it reduce under-provisioning relative to delayed reactive scaling?"],
        ["4", "Does the most accurate model also produce the best allocation outcome?"],
    ],
    [12 * mm, 162 * mm],
))
story.append(Spacer(1, 6 * mm))
story.append(P("Do not overclaim", "H2x"))
story.append(bullet("At 30%, only Question 1 has a persistence baseline implementation, and only on the validation split."))
story.append(bullet("Questions 2-4 require the allocation simulator and advanced models planned for later milestones."))
story.append(PageBreak())

# Person 1 page 2
story.extend(heading("Person 1 - dataset and experimental method", "Speaker section 1 of 4"))
story.append(P("Why Google Cluster Trace 2019?", "H2x"))
for text in [
    "Its instance-usage records include average and maximum CPU and memory signals.",
    "Its instance-event records include requested CPU and memory plus scheduling metadata.",
    "The same task intervals can therefore support forecasting and later allocation comparisons.",
    "The full trace is roughly 2.4 TiB compressed, so the design uses a deterministic laptop-sized sample rather than the full dataset.",
]:
    story.append(bullet(text))
story.append(Spacer(1, 4 * mm))
story.append(info_table(
    ["Design choice", "Decision", "Reason"],
    [
        ["Cell", "Google cell a", "Fixed scope and reproducibility."],
        ["Window", "One contiguous seven-day period", "Preserves temporal order and near-term patterns."],
        ["Cohort", "Up to 1,000 long-running tasks", "Feasible on an 8-16 GB laptop."],
        ["Coverage", "At least 80% expected intervals", "Avoids highly fragmented sequences."],
        ["Horizon", "Next five-minute interval", "Matches the trace sampling interval."],
        ["Split", "60% train / 20% validation / 20% test", "Prevents random time leakage."],
        ["Units", "Normalized capacity", "Public values are not physical vCPU or GB."],
    ],
    [28 * mm, 53 * mm, 93 * mm],
))
story.append(Spacer(1, 7 * mm))
story.append(callout(
    "Key methodological safeguard",
    "An event is joined only when its event time is no later than the usage sample. One missing interval can be filled only from the previous observation. Forecast pairs must be exactly five minutes apart.",
    GREEN, LIGHT_GREEN,
))
story.append(P("Handoff to Person 2", "H2x"))
story.append(P("The research design tells us what data is valid. Person 2 will now explain how the code turns raw trace records into a reproducible database.", "Quote"))
story.append(PageBreak())

# Person 2 page 1
story.extend(heading("Person 2 - architecture and data pipeline", "Speaker section 2 of 4"))
story.append(speaker_chip("PERSON 2 - DATA AND DATABASE", GREEN))
story.append(Spacer(1, 6 * mm))
story.append(P("Explain the pipeline from left to right", "H2x"))
pipeline = info_table(
    ["Stage", "Input", "Responsibility", "Output"],
    [
        ["1. Read", "Official JSON or JSON.GZ shards", "Stream records instead of loading the whole trace.", "Usage/event dictionaries"],
        ["2. Normalize", "Nested Google fields", "Rename and type CPU, memory, timestamps, IDs, request metadata.", "Standard tabular rows"],
        ["3. Select", "Candidate task rows", "Stable SHA-256 hash, time window, coverage threshold, task cap.", "Reproducible cohort"],
        ["4. Join", "Usage and events", "Attach only the latest request known at each sample time.", "Leakage-safe records"],
        ["5. Validate", "Normalized frame", "Reject missing required fields, negative values, bad times, duplicates.", "Clean frame"],
        ["6. Package", "Clean frame", "Write Zstandard Parquet and checksum manifest.", "Versioned dataset"],
        ["7. Ingest", "Manifest plus Parquet", "Verify checksum and insert only records not already present.", "Relational database"],
    ],
    [19 * mm, 36 * mm, 84 * mm, 35 * mm],
)
story.append(pipeline)
story.append(Spacer(1, 7 * mm))
story.append(callout(
    "Why a manifest matters",
    "It records the schema version, dataset version, source, cell, task rule, row/task counts, trace range, units, file path, and SHA-256. If the Parquet file changes, ingestion rejects it.",
    BLUE, LIGHT_BLUE,
))
story.append(P("Core code to mention", "H2x"))
story.append(bullet("<b>cloudalloc/preprocessing.py</b> owns streaming, validation, splits, Parquet, and manifest logic."))
story.append(bullet("<b>cloudalloc/ingestion.py</b> maps trace identities to database task IDs and performs idempotent inserts."))
story.append(bullet("<b>cloudalloc/sample_data.py</b> generates the deterministic four-task fixture used for a safe demo."))
story.append(PageBreak())

# Person 2 page 2
story.extend(heading("Person 2 - relational model and reproducibility", "Speaker section 2 of 4"))
story.append(P("Database entities", "H2x"))
story.append(info_table(
    ["Table", "Purpose now", "Purpose later"],
    [
        ["tasks", "One row per trace task identity and scheduling metadata.", "Groups histories and bootstrap units."],
        ["workload_samples", "Timestamped requests and CPU/memory usage with split label.", "Feature and allocation inputs."],
        ["experiments", "Registers the persistence baseline and artifact path.", "Registers each model/version/configuration."],
        ["predictions", "Stores validation persistence predictions and actual targets.", "Stores all model forecasts."],
        ["evaluation_metrics", "Stores MAE, RMSE, sMAPE, and R2.", "Stores policy metrics and confidence intervals."],
        ["allocation_decisions", "Scaffolded and intentionally empty.", "Stores static, reactive, predictive, and oracle decisions."],
    ],
    [40 * mm, 66 * mm, 68 * mm],
))
story.append(Spacer(1, 7 * mm))
left = [P("Integrity controls", "H2x"),
        bullet("Unique task trace identity."),
        bullet("Unique task plus timestamp sample."),
        bullet("Unique experiment prediction target."),
        bullet("Timestamp and lookup indexes."),
        bullet("Alembic migration at revision 0001.")]
right = [P("Reproducibility controls", "H2x"),
         bullet("Stable task hash and fixed random behavior."),
         bullet("Content checksum and schema version."),
         bullet("Chronological split labels stored with samples."),
         bullet("Raw data and generated artifacts excluded from Git."),
         bullet("Synthetic fixture clearly labelled non-research.")]
story.append(two_columns(left, right))
story.append(Spacer(1, 8 * mm))
story.append(callout(
    "Idempotency demonstration",
    "The first seed creates 4 tasks and inserts 143 samples. Running the same command again creates 0 tasks and inserts 0 samples. This proves that duplicate ingestion is safely ignored.",
    GREEN, LIGHT_GREEN,
))
story.append(P("Handoff to Person 3", "H2x"))
story.append(P("Once the data is validated and stored, Person 3 can explain what analysis, baseline forecasting, APIs, and tests are working today.", "Quote"))
story.append(PageBreak())

# Person 3 page 1
story.extend(heading("Person 3 - EDA and persistence baseline", "Speaker section 3 of 4"))
story.append(speaker_chip("PERSON 3 - ANALYSIS AND BACKEND", AMBER))
story.append(Spacer(1, 6 * mm))
story.append(P("Exploratory data analysis", "H2x"))
for text in [
    "EDA defaults to the training split, so the test period is not inspected during model development.",
    "It writes eda_summary.json for reproducible statistics and eda.html for interactive Plotly charts.",
    "It covers distributions, missingness, correlations, temporal CPU/memory behavior, and request-versus-usage gaps.",
]:
    story.append(bullet(text))
story.append(P("Persistence forecast", "H2x"))
story.append(callout(
    "Definition",
    "For task i, the predicted maximum CPU or memory at t+1 equals the observed maximum at t. This simple method is important because stable workloads can make it difficult for more complex models to show genuine improvement.",
    AMBER, LIGHT_AMBER,
))
story.append(Spacer(1, 5 * mm))
story.append(info_table(
    ["Metric", "What it answers", "Direction"],
    [
        ["MAE", "What is the typical absolute prediction error?", "Lower is better"],
        ["RMSE", "How strongly are larger errors penalized?", "Lower is better"],
        ["sMAPE", "How large is relative error with zero-safe handling?", "Lower is better"],
        ["R2", "How much target variation is explained?", "Higher is better"],
    ],
    [25 * mm, 114 * mm, 35 * mm],
))
story.append(Spacer(1, 6 * mm))
story.append(P("Current fixture output - demonstration only", "H2x"))
story.append(info_table(
    ["Resource", "Validation MAE", "Validation RMSE", "Validation sMAPE", "Validation R2"],
    [
        ["CPU", "0.00985", "0.01169", "0.04771", "0.98317"],
        ["Memory", "0.00400", "0.00478", "0.01573", "0.99014"],
    ],
    [30 * mm, 36 * mm, 36 * mm, 38 * mm, 34 * mm],
))
story.append(Spacer(1, 5 * mm))
story.append(P("These values describe generated periodic data. Do not use them to argue that the model performs well on Google workloads.", "Smallx"))
story.append(PageBreak())

# Person 3 page 2
story.extend(heading("Person 3 - API, tests, and code responsibilities", "Speaker section 3 of 4"))
story.append(P("Current web interface", "H2x"))
story.append(info_table(
    ["Route", "Responsibility", "What to point out"],
    [
        ["GET /", "Shows the 30% milestone landing page.", "It openly labels later features as future work."],
        ["GET /api/health", "Checks application and database availability.", "Returns status, database state, and milestone label."],
        ["GET /api/workloads/summary", "Aggregates task/sample counts, trace range, requests, and usage.", "Values are labelled normalized capacity."],
        ["GET /api/workloads/summary?start=...&end=...", "Applies trace-time filters.", "Invalid or reversed ranges return JSON 400 errors."],
    ],
    [52 * mm, 65 * mm, 57 * mm],
))
story.append(Spacer(1, 7 * mm))
story.append(P("Automated evidence", "H2x"))
for text in [
    "13 tests pass in the current environment.",
    "Preprocessing tests cover stable hashing, negative-value rejection, gap filling, chronological splits, checksum tampering, and prior-event joins.",
    "Integration tests prove idempotent ingestion and database-to-JSON API behavior.",
    "Baseline tests prove no prediction crosses a gap, perfect metrics are handled, and experiments/predictions/metrics are persisted.",
    "CLI tests run the seed and EDA workflows end to end.",
]:
    story.append(bullet(text))
story.append(Spacer(1, 4 * mm))
story.append(callout(
    "Best code explanation order",
    "Start at wsgi.py and create_app(), then follow CLI commands into preprocessing/ingestion, models, analysis/baseline, and finally API responses. This mirrors the real data flow and is easier to understand than explaining files alphabetically.",
    BLUE, LIGHT_BLUE,
))
story.append(P("Handoff to Person 4", "H2x"))
story.append(P("The implementation is testable and produces stored results. Person 4 will now reproduce that full current-state workflow live.", "Quote"))
story.append(PageBreak())

# Person 4 demo setup
story.extend(heading("Person 4 - live demo: setup and database", "Speaker section 4 of 4 - dedicated run section"))
story.append(speaker_chip("PERSON 4 - DEMO AND ROADMAP", RED))
story.append(Spacer(1, 6 * mm))
story.append(callout(
    "Recommended demo mode",
    "Use SQLite and the deterministic fixture. It avoids Docker, network, PostgreSQL credentials, and the multi-terabyte trace while exercising the same application, models, tables, CLI, EDA, baseline, and API paths.",
    GREEN, LIGHT_GREEN,
))
story.append(P("Before the presentation", "H2x"))
for text in [
    "Open PowerShell in D:\\projects\\dbms.",
    "Confirm Python 3.11 or newer is available.",
    "Close any process already using port 5000.",
    "Keep reports/generated/eda.html ready as a backup if live Plotly generation is slow.",
    "Increase terminal font size and browser zoom for the audience.",
]:
    story.append(bullet(text))
story.append(P("Step 1 - install once", "H2x"))
story.append(code_block('cd D:\\projects\\dbms\npython -m pip install -e ".[dev]"'))
story.append(P("Step 2 - select the app and a local SQLite database", "H2x"))
story.append(code_block('$env:FLASK_APP = "wsgi.py"\n$env:DATABASE_URL = "sqlite:///cloudalloc-demo.sqlite3"'))
story.append(P("Step 3 - apply the relational migration", "H2x"))
story.append(code_block("python -m flask db upgrade\npython -m flask db current"))
story.append(P("Expected explanation", "H2x"))
story.append(bullet("Revision 0001 creates all planned tables and constraints. SQLite is only the demo database; PostgreSQL is the intended deployment database."))
story.append(PageBreak())

# Person 4 demo run
story.extend(heading("Person 4 - live demo: generate, analyze, and test", "Dedicated current-state run section"))
story.append(P("Step 4 - seed the deterministic fixture twice", "H2x"))
story.append(code_block("python -m flask demo seed\npython -m flask demo seed"))
story.append(bullet("First run: expect 4 tasks and 143 inserted samples."))
story.append(bullet("Second run: expect 0 created tasks and 0 inserted samples. Say: 'This demonstrates idempotency.'"))
story.append(P("Step 5 - generate training-only EDA", "H2x"))
story.append(code_block("python -m flask analysis eda --output reports/generated\nStart-Process reports/generated/eda.html"))
story.append(bullet("Show the CPU and memory distributions, temporal lines, and request-versus-maximum scatter plots."))
story.append(bullet("Point out that the fixture is generated and that real findings require the prepared Google sample."))
story.append(P("Step 6 - run the validation persistence baseline", "H2x"))
story.append(code_block("python -m flask baseline run `\n  --dataset-version synthetic-fixture `\n  --output reports/generated/persistence_baseline.json\nGet-Content reports/generated/persistence_baseline.json"))
story.append(bullet("Explain that validation metrics are stored in the database and JSON artifact."))
story.append(bullet("Do not add --include-test during development; that option is reserved for final frozen evaluation."))
story.append(P("Step 7 - run automated verification", "H2x"))
story.append(code_block("python -m pytest"))
story.append(bullet("Expected current result: 13 passed."))
story.append(PageBreak())

# Person 4 server demo
story.extend(heading("Person 4 - live demo: start the app and explain outputs", "Dedicated current-state run section"))
story.append(P("Step 8 - start Flask", "H2x"))
story.append(code_block("python -m flask run"))
story.append(P("Step 9 - open these pages in order", "H2x"))
story.append(info_table(
    ["Address", "What to show", "What to say"],
    [
        ["http://127.0.0.1:5000/", "Milestone landing page", "The UI honestly lists what is implemented and what is deferred."],
        ["http://127.0.0.1:5000/api/health", "JSON health response", "The Flask process can query its configured database."],
        ["http://127.0.0.1:5000/api/workloads/summary", "Counts and average resource values", "The API reads actual persisted workload rows, not hard-coded JSON."],
        [".../summary?start=0&end=3600000000", "Filtered summary", "Trace-relative microsecond filters are validated server-side."],
    ],
    [61 * mm, 48 * mm, 65 * mm],
))
story.append(Spacer(1, 8 * mm))
story.append(callout(
    "If something fails live",
    "Keep the terminal visible and explain the error. Then show the already generated eda.html, persistence_baseline.json, and the latest pytest output. Do not substitute synthetic results for real-trace claims.",
    RED, HexColor("#FDECEE"),
))
story.append(P("Close the demo with three statements", "H2x"))
story.append(bullet("The data path is reproducible and rejects corruption or invalid values."))
story.append(bullet("The database and API are operational, and duplicate ingestion is safe."))
story.append(bullet("The persistence baseline is the comparison point for the advanced models in the next milestone."))
story.append(PageBreak())

# Code map page 1
story.extend(heading("Code responsibility reference - application and data", "Use during explanation or viva"))
story.append(info_table(
    ["File or area", "Responsibility", "Called by / visible in demo"],
    [
        ["wsgi.py", "Creates the Flask application object used by the development server.", "python -m flask run"],
        ["cloudalloc/__init__.py", "Application factory: loads configuration, initializes database/migrations, registers API, dashboard, and CLI.", "Every Flask command and request"],
        ["cloudalloc/config.py", "Reads secret, database URL, artifact directory, and SQLAlchemy settings.", "DATABASE_URL environment variable"],
        ["cloudalloc/extensions.py", "Owns shared SQLAlchemy and Flask-Migrate objects without creating import cycles.", "Application startup and migrations"],
        ["cloudalloc/constants.py", "Defines normalized schema columns, interval length, later model/policy names.", "Preprocessing and baseline"],
        ["cloudalloc/models.py", "Defines tasks, samples, experiments, predictions, decisions, and metric tables plus indexes/constraints.", "Migration, seed, baseline, API"],
        ["cloudalloc/preprocessing.py", "Streams Google JSONL/GZIP, normalizes fields, validates data, fills one gap, assigns splits, writes/verifies manifest.", "flask data prepare / ingest"],
        ["cloudalloc/ingestion.py", "Creates missing tasks and inserts only unseen task-time samples.", "flask data ingest and demo seed"],
        ["cloudalloc/sample_data.py", "Builds deterministic periodic fixture and its Parquet/manifest artifacts.", "flask demo seed"],
        ["scripts/extract_sample.sql", "Optional BigQuery extraction for the same seven-day/hash/coverage design.", "Not required for fixture demo"],
    ],
    [49 * mm, 84 * mm, 41 * mm],
))
story.append(PageBreak())

# Code map page 2
story.extend(heading("Code responsibility reference - analysis, interface, and quality", "Use during explanation or viva"))
story.append(info_table(
    ["File or area", "Responsibility", "Called by / visible in demo"],
    [
        ["cloudalloc/analysis.py", "Queries stored samples and creates descriptive JSON plus six interactive Plotly views; defaults to train split.", "flask analysis eda"],
        ["cloudalloc/baseline.py", "Builds exact t to t+1 persistence pairs, calculates four forecast metrics, stores experiment/predictions/metrics.", "flask baseline run"],
        ["cloudalloc/api.py", "Implements database health and workload summary routes with time-filter validation.", "/api/health and /api/workloads/summary"],
        ["cloudalloc/dashboard.py", "Serves the current milestone landing page.", "GET /"],
        ["cloudalloc/templates/index.html", "Explains current capability and deferred work in the browser.", "Landing page"],
        ["cloudalloc/cli.py", "Connects human-readable Flask commands to preparation, ingestion, EDA, baseline, and demo services.", "All demo commands"],
        ["migrations/versions/0001_initial_schema.py", "Creates and reverses the initial relational schema reproducibly.", "flask db upgrade / current"],
        ["tests/test_preprocessing.py", "Verifies hash, validation, gaps, splits, checksum, and no future-event join.", "pytest"],
        ["tests/test_ingestion_api.py", "Verifies idempotency, health, summary, and invalid query responses.", "pytest"],
        ["tests/test_baseline.py", "Verifies contiguous forecasts, metric correctness, and persistence of results.", "pytest"],
        ["tests/test_cli.py", "Runs fixture seed and EDA through Flask's CLI runner.", "pytest"],
        ["docker-compose.yml / .env.example", "Provides the intended PostgreSQL service and example runtime configuration.", "PostgreSQL setup, not quick demo"],
        ["pyproject.toml", "Declares Python version, runtime libraries, development tests, and package metadata.", "pip install -e .[dev]"],
    ],
    [49 * mm, 84 * mm, 41 * mm],
))
story.append(PageBreak())

# Viva and next steps
story.extend(heading("Likely questions, limitations, and next 70%", "Shared closing and viva preparation"))
story.append(P("Short answers to likely questions", "H2x"))
story.append(info_table(
    ["Question", "Recommended answer"],
    [
        ["Why not use the full Google trace?", "It is roughly 2.4 TiB compressed. Deterministic sampling makes the experiment feasible and reproducible on student hardware."],
        ["Why is persistence necessary?", "Many workloads are temporally stable. A complex model must beat a strong simple baseline, not only a weak random guess."],
        ["Why predict maximum rather than average?", "Allocation must cover short peaks; average demand alone can hide under-provisioning risk."],
        ["Why is EDA train-only?", "Inspecting test behavior can influence model choices. Keeping it unseen makes final evaluation more credible."],
        ["Why SQLite in the demo?", "It minimizes operational risk while exercising the same ORM schema and services. PostgreSQL remains the documented deployment target."],
        ["Are the current metrics research results?", "No. They are fixture-based software validation. Real claims begin only after official trace ingestion."],
        ["What proves there is no temporal leakage?", "Chronological splits, latest-prior event joins, past-only gap fill, and exact five-minute forecast pairing are implemented and tested."],
    ],
    [63 * mm, 111 * mm],
))
story.append(Spacer(1, 7 * mm))
story.append(P("Remaining work", "H2x"))
for text in [
    "30-50%: construct lag/rolling features and train Ridge, random forest, and histogram gradient boosting.",
    "50-70%: simulate static, reactive, predictive, and oracle allocations; calculate waste, deficit, utilization, churn, and confidence intervals.",
    "70-85%: add experiment, comparison, and recommendation APIs plus the final analytics dashboard.",
    "85-100%: execute the frozen test evaluation, robustness checks, final report, slides, and final demonstration.",
]:
    story.append(bullet(text))
story.append(Spacer(1, 7 * mm))
story.append(callout(
    "Final team closing",
    "At 30%, we have not proven that predictive allocation is better. We have built the reproducible data, database, analysis, baseline, API, and testing foundation needed to answer that question correctly in the remaining work.",
    GREEN, LIGHT_GREEN,
))
story.append(PageBreak())

# Sources and final checklist
story.extend(heading("Final checklist and references", "One minute before presenting"))
story.append(P("Team checklist", "H2x"))
check_rows = [
    ["Person 1", "Can state problem, gap, four research questions, dataset choice, and non-overclaim boundary."],
    ["Person 2", "Can trace one row from raw JSON to Parquet manifest to relational sample and explain idempotency."],
    ["Person 3", "Can define persistence and all four metrics, explain the two API routes, and summarize test coverage."],
    ["Person 4", "Has run every demo command once, has backup artifacts open, and can explain synthetic versus real data."],
    ["All", "Use normalized capacity units; never call them vCPU or GB. Say 30% foundation, not completed predictive allocator."],
]
story.append(info_table(["Owner", "Ready when..."], check_rows, [35 * mm, 139 * mm]))
story.append(Spacer(1, 9 * mm))
story.append(P("Primary project references", "H2x"))
refs = [
    '<link href="https://github.com/google/cluster-data/blob/master/ClusterData2019.md" color="#2563EB">Google Cluster Trace 2019 documentation and access notes</link>',
    '<link href="https://research.google/pubs/borg-the-next-generation/" color="#2563EB">Tirmazi et al. (2020), Borg: the Next Generation</link>',
    '<link href="https://www.microsoft.com/en-us/research/publication/resource-central-understanding-predicting-workloads-improved-resource-management-large-cloud-platforms/" color="#2563EB">Cortez et al. (2017), Resource Central</link>',
    '<link href="https://www.usenix.org/conference/osdi20/presentation/hadary" color="#2563EB">Hadary et al. (2020), Protean</link>',
    'Full 13-study matrix: docs/literature_matrix.md',
    'Research design: docs/research_design.md',
    '30% progress report: reports/30_percent_progress.md',
]
for ref in refs:
    story.append(bullet(ref))
story.append(Spacer(1, 10 * mm))
story.append(P("Recommended final sentence", "H2x"))
story.append(P("The current milestone makes later comparisons trustworthy because every future model and allocation policy will use the same validated records, chronological boundaries, database, and evaluation pipeline.", "Quote"))


OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc = GuideDoc(str(OUTPUT))
doc.build(story)
print(OUTPUT)

