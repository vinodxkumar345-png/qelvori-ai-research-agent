import os
import re
from datetime import datetime
from xml.sax.saxutils import escape, quoteattr

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    KeepTogether
)


class ReportGenerator:

    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.styles = getSampleStyleSheet()

        self.styles.add(ParagraphStyle(
            name="QelvoriTitle",
            parent=self.styles["Title"],
            fontSize=25,
            leading=31,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#172554"),
            spaceAfter=12
        ))

        self.styles.add(ParagraphStyle(
            name="QelvoriSubtitle",
            parent=self.styles["Normal"],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=8
        ))

        self.styles.add(ParagraphStyle(
            name="QelvoriHeading",
            parent=self.styles["Heading2"],
            fontSize=15,
            leading=20,
            textColor=colors.HexColor("#1d4ed8"),
            spaceBefore=15,
            spaceAfter=8
        ))

        self.styles.add(ParagraphStyle(
            name="QelvoriBody",
            parent=self.styles["BodyText"],
            fontSize=9.5,
            leading=15,
            alignment=TA_LEFT,
            spaceAfter=7
        ))

        self.styles.add(ParagraphStyle(
            name="QelvoriSmall",
            parent=self.styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
            spaceAfter=4
        ))

        self.styles.add(ParagraphStyle(
            name="QelvoriBullet",
            parent=self.styles["BodyText"],
            fontSize=9.5,
            leading=14,
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=5
        ))

    def clean_markdown(self, text):
        text = str(text)

        text = re.sub(
            r"\*\*(.*?)\*\*",
            r"<b>\1</b>",
            text
        )

        text = re.sub(
            r"`(.*?)`",
            r"<font name='Courier'>\1</font>",
            text
        )

        return text

    def add_analysis(self, story, analysis):

        lines = str(analysis).splitlines()

        for line in lines:

            line = line.strip()

            if not line:
                story.append(Spacer(1, 4))
                continue

            if line.startswith("#"):
                heading = line.lstrip("#").strip()

                story.append(Paragraph(
                    escape(heading),
                    self.styles["QelvoriHeading"]
                ))

            elif line.startswith(("- ", "* ", "â€¢ ")):
                content = line[2:].strip()

                content = self.clean_markdown(content)

                story.append(Paragraph(
                    "â€¢ " + content,
                    self.styles["QelvoriBullet"]
                ))

            else:
                content = self.clean_markdown(line)

                story.append(Paragraph(
                    content,
                    self.styles["QelvoriBody"]
                ))

    def add_sources(self, story, research_data):

        story.append(Paragraph(
            "Research Sources",
            self.styles["QelvoriHeading"]
        ))

        if not research_data:
            story.append(Paragraph(
                "No source metadata available.",
                self.styles["QelvoriBody"]
            ))
            return

        for index, source in enumerate(research_data, start=1):

            title = escape(str(
                source.get("title", f"Source {index}")
            ))

            url = str(source.get("url", "")).strip()

            source_type = escape(str(
                source.get("source_type", "Unknown")
            ))

            quality = source.get("quality_score", "N/A")

            publication_date = escape(str(
                source.get("publication_date") or "Not verified"
            ))

            creation_date = escape(str(
                source.get("document_creation_date") or "Unavailable"
            ))

            modified_date = escape(str(
                source.get("modified_date") or "Unavailable"
            ))

            date_source = escape(str(
                source.get("date_source") or "Unavailable"
            ))

            date_status = escape(str(
                source.get("date_status") or "Unknown"
            ))

            story.append(Paragraph(
                f"<b>{index}. {title}</b>",
                self.styles["QelvoriBody"]
            ))

            if url:
                safe_url = escape(url)

                story.append(Paragraph(
                    f'<link href={quoteattr(url)} color="#2563eb">'
                    f"{safe_url}</link>",
                    self.styles["QelvoriSmall"]
                ))

            details = [
                ["Source Type", source_type],
                ["Quality Score", str(quality)],
                ["Publication Date", publication_date],
                ["Document Creation Date", creation_date],
                ["Modified Date", modified_date],
                ["Date Source", date_source],
                ["Date Status", date_status]
            ]

            table = Table(
                details,
                colWidths=[43 * mm, 115 * mm]
            )

            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1),
                 colors.HexColor("#eff6ff")),

                ("TEXTCOLOR", (0, 0), (-1, -1),
                 colors.HexColor("#334155")),

                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),

                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.4,
                 colors.HexColor("#cbd5e1")),

                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
            ]))

            story.append(table)
            story.append(Spacer(1, 12))

    def add_methodology_notes(self, story):

        story.append(Paragraph(
            "Research Methodology & Limitations",
            self.styles["QelvoriHeading"]
        ))

        notes = [
            "Source quality scores are heuristic indicators, not proof of credibility.",

            "A PDF creation date does not necessarily represent its publication date.",

            "Evidence verification evaluates claims against the collected source text; it is not independent proof.",

            "A claim supported by one source should not be treated as independently confirmed by multiple sources.",

            "Claims marked as partially supported or insufficiently supported require further investigation."
        ]

        for note in notes:
            story.append(Paragraph(
                "â€¢ " + escape(note),
                self.styles["QelvoriBullet"]
            ))

    def add_page_number(self, canvas, document):

        canvas.saveState()

        page_number = canvas.getPageNumber()

        canvas.setStrokeColor(
            colors.HexColor("#cbd5e1")
        )

        canvas.line(
            20 * mm,
            15 * mm,
            190 * mm,
            15 * mm
        )

        canvas.setFont("Helvetica", 8)

        canvas.setFillColor(
            colors.HexColor("#64748b")
        )

        canvas.drawString(
            20 * mm,
            10 * mm,
            "QELVORI AI Research Agent"
        )

        canvas.drawRightString(
            190 * mm,
            10 * mm,
            f"Page {page_number}"
        )

        canvas.restoreState()

    def generate(self, topic, analysis, research_data):

        safe_topic = re.sub(
            r"[^a-zA-Z0-9_-]+",
            "_",
            str(topic)
        ).strip("_")

        filename = (
            f"QELVORI_Report_{safe_topic}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        filepath = os.path.join(
            self.output_dir,
            filename
        )

        document = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=25 * mm,
            title=f"QELVORI Research Report - {topic}",
            author="QELVORI AI Research Agent"
        )

        story = []

        story.append(Spacer(1, 25 * mm))

        story.append(Paragraph(
            "QELVORI",
            self.styles["QelvoriTitle"]
        ))

        story.append(Paragraph(
            "AUTONOMOUS AI RESEARCH REPORT",
            self.styles["QelvoriSubtitle"]
        ))

        story.append(Spacer(1, 12 * mm))

        story.append(Paragraph(
            escape(str(topic)),
            self.styles["Heading1"]
        ))

        story.append(Spacer(1, 5 * mm))

        story.append(Paragraph(
            f"Generated on: "
            f"{datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            self.styles["QelvoriSubtitle"]
        ))

        story.append(Spacer(1, 12 * mm))

        story.append(Paragraph(
            "Research Analysis",
            self.styles["QelvoriHeading"]
        ))

        self.add_analysis(story, analysis)

        story.append(PageBreak())

        self.add_sources(story, research_data)

        story.append(Spacer(1, 8))

        self.add_methodology_notes(story)

        document.build(
            story,
            onFirstPage=self.add_page_number,
            onLaterPages=self.add_page_number
        )

        return filepath
