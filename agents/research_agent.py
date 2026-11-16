import os
import traceback

from tools.search_tool import SearchTool
from tools.content_extractor import ContentExtractor
from core.ai_analyzer import AIAnalyzer
from core.evidence_verifier import EvidenceVerifier
from core.report_generator import ReportGenerator


class ResearchAgent:

    def __init__(self):

        self.name = "QELVORI AI Research Agent"

        self.search_tool = SearchTool()
        self.extractor = ContentExtractor()
        self.analyzer = AIAnalyzer()
        self.verifier = EvidenceVerifier()
        self.report_generator = ReportGenerator()

    # --------------------------------------------------
    # PROGRESS CALLBACK
    # --------------------------------------------------

    def update_progress(
        self,
        callback,
        stage,
        progress,
        message
    ):

        if not callable(callback):
            return

        try:
            callback({
                "stage": stage,
                "progress": progress,
                "message": message
            })

        except Exception as error:
            print("\nProgress callback warning:", str(error))

    # --------------------------------------------------
    # METADATA HELPER
    # --------------------------------------------------

    def get_metadata_value(
        self,
        extracted,
        key,
        *aliases
    ):

        if not isinstance(extracted, dict):
            return None

        metadata = extracted.get("metadata", {})
        containers = [metadata, extracted]

        for container in containers:
            if not isinstance(container, dict):
                continue

            for candidate in (key,) + aliases:
                value = container.get(candidate)
                if value is not None:
                    return value

        return None

    # --------------------------------------------------
    # EVIDENCE VERIFICATION FORMATTER
    # --------------------------------------------------

    def format_verification(self, verification):

        lines = [
            "",
            "=" * 65,
            "QELVORI FACTUAL EVIDENCE VERIFICATION",
            "=" * 65
        ]

        if not isinstance(verification, dict):
            lines.append("Verification result unavailable.")
            return "\n".join(lines)

        if not verification.get("success"):
            lines.append("STATUS: VERIFICATION UNAVAILABLE")
            lines.append(
                str(
                    verification.get(
                        "error",
                        "No verification details available."
                    )
                )
            )
            lines.append("Research analysis has not been verified.")
            return "\n".join(lines)

        claims = verification.get("claims", [])

        if not isinstance(claims, list) or not claims:
            lines.append(
                "No factual claims were returned for verification."
            )
            return "\n".join(lines)

        for index, claim in enumerate(claims, start=1):
            if not isinstance(claim, dict):
                continue

            lines.append("")
            lines.append(
                f"CLAIM {index}: {claim.get('claim', 'Unavailable')}"
            )
            lines.append(
                f"STATUS: {claim.get('status', 'UNCLEAR')}"
            )

            supporting = claim.get("supporting_sources", [])
            conflicting = claim.get("conflicting_sources", [])

            lines.append(
                "Supporting Sources: "
                + (
                    ", ".join(map(str, supporting))
                    if isinstance(supporting, list) and supporting
                    else "None"
                )
            )
            lines.append(
                "Conflicting Sources: "
                + (
                    ", ".join(map(str, conflicting))
                    if isinstance(conflicting, list) and conflicting
                    else "None"
                )
            )

            evidence = claim.get("evidence", [])
            if not isinstance(evidence, list):
                evidence = []

            for item in evidence:
                if not isinstance(item, dict):
                    continue

                # EvidenceVerifier emits "source". Retain source_id
                # as a compatibility fallback for older result formats.
                source_id = (
                    item.get("source")
                    or item.get("source_id")
                    or "Unknown"
                )

                lines.append("")
                lines.append("Evidence Source: " + str(source_id))
                lines.append(
                    "Relation: "
                    + str(item.get("relation", "Unknown"))
                )
                lines.append(
                    "Quote: "
                    + str(item.get("quote", "Unavailable"))
                )

                explanation = item.get("explanation")
                if explanation:
                    lines.append("Explanation: " + str(explanation))

        lines.append("")
        lines.append("=" * 65)
        lines.append(
            "IMPORTANT: This is AI-assisted evidence verification."
        )
        lines.append(
            "It is not a guarantee of factual correctness "
            "or a substitute for human review."
        )
        lines.append("=" * 65)

        return "\n".join(lines)

    # --------------------------------------------------
    # MAIN RESEARCH PIPELINE
    # --------------------------------------------------

    def run(self, topic, progress_callback=None):

        try:
            if topic is None:
                return {
                    "success": False,
                    "topic": "",
                    "error": "Please enter a valid research topic."
                }

            topic = str(topic).strip()

            if len(topic) < 3:
                return {
                    "success": False,
                    "topic": topic,
                    "error": "Please enter a valid research topic."
                }

            print("\n" + "=" * 55)
            print("             QELVORI AI RESEARCH AGENT")
            print("=" * 55)
            print("\nResearch Topic:", topic)

            # STEP 1: WEB SEARCH
            self.update_progress(
                progress_callback,
                "searching",
                10,
                "Searching the web for research sources..."
            )

            print("\n[1] Searching the web...")
            results = self.search_tool.search(topic)

            if not isinstance(results, list) or not results:
                print("No search results found.")
                return {
                    "success": False,
                    "topic": topic,
                    "error": "No search results found."
                }

            print("\nSearch results:", len(results))

            # STEP 2: CONTENT EXTRACTION
            self.update_progress(
                progress_callback,
                "extracting",
                25,
                "Extracting research content and metadata..."
            )

            print("\n[2] Extracting research content and metadata...")

            research_data = []
            selected_results = results[:5]

            for index, result in enumerate(selected_results, start=1):
                if not isinstance(result, dict):
                    continue

                url = result.get("url")
                if not url:
                    continue

                try:
                    extracted = self.extractor.extract_with_metadata(url)
                except Exception as error:
                    print(
                        "\nSource extraction failed:",
                        url,
                        str(error)
                    )
                    continue

                if not isinstance(extracted, dict):
                    continue

                content = extracted.get("content")
                if not isinstance(content, str) or not content.strip():
                    continue

                source_data = {
                    "source_id": f"S{len(research_data) + 1}",
                    "title": result.get("title", "Untitled Source"),
                    "url": url,
                    "content": content,
                    "source_type": result.get(
                        "source_type",
                        "General Web"
                    ),
                    "quality_score": result.get("quality_score", 0),
                    "publication_date": self.get_metadata_value(
                        extracted,
                        "publication_date",
                        "datePublished"
                    ),
                    "document_creation_date": self.get_metadata_value(
                        extracted,
                        "document_creation_date",
                        "creation_date",
                        "dateCreated"
                    ),
                    "modified_date": self.get_metadata_value(
                        extracted,
                        "modified_date",
                        "dateModified"
                    ),
                    "date_source": self.get_metadata_value(
                        extracted,
                        "date_source"
                    ),
                    "date_status": self.get_metadata_value(
                        extracted,
                        "date_status"
                    )
                }

                research_data.append(source_data)

                print("\nSource collected:")
                print("Title:", source_data["title"])
                print("Type:", source_data["source_type"])
                print("Quality Score:", source_data["quality_score"])
                print("Publication Date:", source_data["publication_date"])
                print(
                    "Document Creation Date:",
                    source_data["document_creation_date"]
                )
                print("Date Status:", source_data["date_status"])

                self.update_progress(
                    progress_callback,
                    "extracting",
                    25 + int(index / len(selected_results) * 20),
                    f"Extracted {len(research_data)} usable sources..."
                )

            if not research_data:
                print("\nNo research content collected.")
                return {
                    "success": False,
                    "topic": topic,
                    "error": (
                        "No usable research content could be extracted."
                    )
                }

            print(
                "\nSources successfully collected:",
                len(research_data)
            )

            # STEP 3: AI RESEARCH ANALYSIS
            self.update_progress(
                progress_callback,
                "analyzing",
                50,
                "Analyzing research using Qwen3:4B..."
            )

            print("\n[3] Analyzing research using Qwen3:4B...")
            analysis = self.analyzer.analyze(research_data, topic)

            if (
                not isinstance(analysis, str)
                or not analysis.strip()
                or analysis.startswith("AI analysis error:")
            ):
                print("\nAI analysis failed.")
                print(analysis)
                return {
                    "success": False,
                    "topic": topic,
                    "error": "AI research analysis failed."
                }

            print("\n" + "=" * 55)
            print("             AI RESEARCH ANALYSIS")
            print("=" * 55)
            print(analysis)

            # STEP 4: FACTUAL EVIDENCE VERIFICATION
            self.update_progress(
                progress_callback,
                "verifying",
                68,
                "Verifying research claims against collected sources..."
            )

            print("\n[4] Starting factual evidence verification...")

            try:
                verification = self.verifier.verify(
                    research_data,
                    analysis
                )

                if not isinstance(verification, dict):
                    verification = {
                        "success": False,
                        "claims": [],
                        "error": "Invalid verification response."
                    }

            except Exception as error:
                print("\nEvidence verification failed:", str(error))
                traceback.print_exc()
                verification = {
                    "success": False,
                    "claims": [],
                    "error": (
                        "Evidence verification encountered an internal error."
                    )
                }

            verification_report = self.format_verification(verification)
            final_analysis = analysis + "\n\n" + verification_report

            # STEP 5: PDF REPORT GENERATION
            self.update_progress(
                progress_callback,
                "generating",
                85,
                "Generating your professional PDF report..."
            )

            print("\n[5] Generating professional PDF report...")

            pdf_path = self.report_generator.generate(
                topic,
                final_analysis,
                research_data
            )

            if not pdf_path:
                print("\nPDF generation failed.")
                return {
                    "success": False,
                    "topic": topic,
                    "error": "PDF report generation failed."
                }

            pdf_path = os.fspath(pdf_path)

            if not os.path.isfile(pdf_path):
                print("\nPDF file was not found:", pdf_path)
                return {
                    "success": False,
                    "topic": topic,
                    "error": (
                        "PDF generation returned a path, "
                        "but the report file does not exist."
                    )
                }

            report_filename = os.path.basename(pdf_path)

            if not report_filename.lower().endswith(".pdf"):
                return {
                    "success": False,
                    "topic": topic,
                    "error": "Invalid PDF report filename."
                }

            # STEP 6: COMPLETION
            self.update_progress(
                progress_callback,
                "completed",
                100,
                "Research completed successfully!"
            )

            print("\n" + "=" * 55)
            print("             RESEARCH COMPLETED")
            print("=" * 55)
            print("\nResearch Topic:", topic)
            print("Sources Collected:", len(research_data))
            print(
                "Evidence Verification:",
                "Completed"
                if verification.get("success")
                else "Unavailable or unsuccessful"
            )
            print("PDF Report:", pdf_path)
            print("\nQELVORI research pipeline completed successfully.")

            # STEP 7: STRUCTURED API RESULT
            return {
                "success": True,
                "topic": topic,
                "analysis": final_analysis,
                "verification": verification,
                "verification_success": bool(
                    verification.get("success")
                ),
                "sources": research_data,
                "source_count": len(research_data),
                "report_filename": report_filename
            }

        except Exception as error:
            print("\n========== RESEARCH PIPELINE ERROR ==========")
            print("Topic:", topic)
            print("Error:", str(error))
            traceback.print_exc()
            print("=============================================\n")

            return {
                "success": False,
                "topic": topic,
                "error": (
                    "An unexpected error occurred during research."
                )
            }


# ------------------------------------------------------
# DIRECT EXECUTION
# ------------------------------------------------------

if __name__ == "__main__":

    agent = ResearchAgent()

    topic = input("\nEnter your research topic: ").strip()

    if topic:
        result = agent.run(topic)

        if result.get("success"):
            print("\nResearch completed successfully.")
            print("Report:", result.get("report_filename"))
        else:
            print("\nResearch failed:", result.get("error"))
    else:
        print("Please enter a valid research topic.")

