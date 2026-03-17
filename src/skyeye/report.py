"""Report generation utilities for formatting and outputting inspection results."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from skyeye.inspection.report import InspectionReport
from skyeye.models import PriorityLevel, SeverityLevel


class ReportFormatter:
    """Format and render inspection reports for display or file output.

    Supports console rendering via Rich and plain-text export.
    """

    SEVERITY_COLORS: dict[SeverityLevel, str] = {
        SeverityLevel.MINOR: "green",
        SeverityLevel.MODERATE: "yellow",
        SeverityLevel.SEVERE: "red",
        SeverityLevel.CRITICAL: "bold red",
    }

    PRIORITY_COLORS: dict[PriorityLevel, str] = {
        PriorityLevel.LOW: "dim",
        PriorityLevel.MEDIUM: "yellow",
        PriorityLevel.HIGH: "red",
        PriorityLevel.URGENT: "bold red blink",
    }

    def __init__(self, console: Optional[Console] = None) -> None:
        self.console = console or Console()

    def render_to_console(self, report: InspectionReport) -> None:
        """Render the inspection report to the terminal using Rich."""
        meta = report.metadata

        # Header
        self.console.print(
            Panel(
                f"[bold]Inspection Report[/bold]\n"
                f"ID: {meta.inspection_id}\n"
                f"Type: {meta.infrastructure_type.value}\n"
                f"Date: {meta.date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Total Images: {meta.total_images}",
                title="SKYEYE Report",
                border_style="blue",
            )
        )

        # Findings table
        if report.findings:
            table = Table(title="Findings", show_lines=True)
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Type", width=18)
            table.add_column("Severity", width=10)
            table.add_column("Priority", width=8)
            table.add_column("Location", width=25)
            table.add_column("Recommendation", width=40)

            for finding in report.findings:
                sev_color = self.SEVERITY_COLORS.get(finding.severity, "white")
                pri_color = self.PRIORITY_COLORS.get(finding.priority, "white")
                table.add_row(
                    finding.id,
                    finding.defect_type.value,
                    f"[{sev_color}]{finding.severity.value}[/{sev_color}]",
                    f"[{pri_color}]{finding.priority.value}[/{pri_color}]",
                    finding.location_description,
                    finding.recommendation,
                )
            self.console.print(table)
        else:
            self.console.print("[green]No defects detected.[/green]")

        # Summary
        if report.summary:
            self.console.print(Panel(report.summary, title="Summary", border_style="green"))

        # Recommendations
        recs = report.get_recommendations()
        if recs:
            self.console.print("\n[bold]Recommendations (by priority):[/bold]")
            for rec in recs:
                self.console.print(f"  - {rec}")

    def render_to_text(self, report: InspectionReport) -> str:
        """Render the report as plain text.

        Returns:
            Plain-text report string.
        """
        lines: list[str] = []
        meta = report.metadata

        lines.append("=" * 60)
        lines.append("SKYEYE INSPECTION REPORT")
        lines.append("=" * 60)
        lines.append(f"ID:               {meta.inspection_id}")
        lines.append(f"Type:             {meta.infrastructure_type.value}")
        lines.append(f"Date:             {meta.date.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Total Images:     {meta.total_images}")
        if meta.inspector:
            lines.append(f"Inspector:        {meta.inspector}")
        lines.append("")

        lines.append("-" * 60)
        lines.append("FINDINGS")
        lines.append("-" * 60)

        if not report.findings:
            lines.append("No defects detected.")
        else:
            for finding in report.findings:
                lines.append(f"\n  [{finding.id}] {finding.defect_type.value}")
                lines.append(f"    Severity: {finding.severity.value}")
                lines.append(f"    Priority: {finding.priority.value}")
                lines.append(f"    Location: {finding.location_description}")
                lines.append(f"    Action:   {finding.recommendation}")

        lines.append("")
        lines.append("-" * 60)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 60)
        for rec in report.get_recommendations():
            lines.append(f"  {rec}")

        if report.summary:
            lines.append("")
            lines.append("-" * 60)
            lines.append("SUMMARY")
            lines.append("-" * 60)
            lines.append(report.summary)

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    def save_to_file(self, report: InspectionReport, path: str) -> Path:
        """Save the report as a text file.

        Args:
            report: The inspection report to save.
            path: Output file path.

        Returns:
            Path to the saved file.
        """
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.render_to_text(report))
        return output
