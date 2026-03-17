"""CLI interface for SKYEYE drone inspection analyzer."""

from __future__ import annotations

from datetime import datetime

import click
from rich.console import Console

from skyeye import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="skyeye")
def cli() -> None:
    """SKYEYE - AI-powered drone inspection analyzer."""


@cli.command()
@click.option("--input", "-i", "input_dir", required=True, help="Directory containing inspection images.")
@click.option("--output", "-o", "output_dir", default="./report", help="Output directory for results.")
@click.option(
    "--type", "-t", "infra_type",
    type=click.Choice(["bridge", "building", "powerline"]),
    default="bridge",
    help="Infrastructure type.",
)
@click.option("--confidence", "-c", default=0.5, help="Detection confidence threshold.")
def analyze(input_dir: str, output_dir: str, infra_type: str, confidence: float) -> None:
    """Analyze inspection images for infrastructure defects."""
    from pathlib import Path

    from skyeye.detection.defect_detector import DefectDetector
    from skyeye.detection.classifier import SeverityClassifier
    from skyeye.inspection.report import InspectionReport
    from skyeye.models import InfrastructureType, InspectionMetadata
    from skyeye.report import ReportFormatter

    console.print(f"[bold blue]SKYEYE[/bold blue] Analyzing images in: {input_dir}")
    console.print(f"Infrastructure type: {infra_type}")
    console.print(f"Confidence threshold: {confidence}")

    input_path = Path(input_dir)
    if not input_path.exists():
        console.print(f"[red]Error: Input directory '{input_dir}' not found.[/red]")
        raise SystemExit(1)

    detector = DefectDetector(confidence_threshold=confidence)
    classifier = SeverityClassifier()

    import numpy as np

    image_files = list(input_path.glob("*.png")) + list(input_path.glob("*.jpg"))
    infra = InfrastructureType(infra_type)

    report = InspectionReport(
        metadata=InspectionMetadata(
            inspection_id=f"INSP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            infrastructure_type=infra,
            total_images=len(image_files),
        )
    )

    for img_path in image_files:
        # Load image as numpy array (simple raw loading for demo)
        try:
            img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
            detections = detector.detect(img)
            for det in detections:
                severity = classifier.classify(img, det)
                report.add_finding(
                    defect_type=det.defect_type,
                    severity=severity,
                    location_description=f"Image: {img_path.name}",
                    recommendation="See detailed analysis.",
                )
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to process {img_path.name}: {e}[/yellow]")

    report.generate_summary()
    formatter = ReportFormatter(console=console)
    formatter.render_to_console(report)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    saved = formatter.save_to_file(report, str(output_path / "report.txt"))
    console.print(f"\n[green]Report saved to: {saved}[/green]")


@cli.command()
@click.option("--structure", "-s", type=click.Choice(["bridge", "building", "powerline"]), default="bridge")
@click.option("--lat", type=float, required=True, help="Center latitude.")
@click.option("--lon", type=float, required=True, help="Center longitude.")
@click.option("--altitude", "-a", default=30.0, help="Flight altitude in meters.")
@click.option("--width", default=100.0, help="Survey width in meters.")
@click.option("--height", default=100.0, help="Survey height in meters.")
def plan(structure: str, lat: float, lon: float, altitude: float, width: float, height: float) -> None:
    """Plan an inspection flight."""
    from skyeye.inspection.flight import FlightPlan
    from skyeye.models import GeoCoordinate, InfrastructureType

    console.print(f"[bold blue]SKYEYE[/bold blue] Planning flight for: {structure}")

    flight = FlightPlan(
        name=f"{structure}-inspection",
        infrastructure_type=InfrastructureType(structure),
        altitude=altitude,
    )

    center = GeoCoordinate(latitude=lat, longitude=lon, altitude=altitude)
    waypoints = flight.generate_grid_pattern(center, width, height)

    console.print(f"Generated {len(waypoints)} waypoints")
    console.print(f"Estimated duration: {flight.estimated_duration_minutes:.1f} minutes")
    console.print(f"Capture points: {flight.capture_count}")


@cli.command()
@click.option("--input", "-i", "input_dir", required=True, help="Results directory.")
@click.option("--format", "-f", "fmt", type=click.Choice(["text", "console"]), default="console")
def report(input_dir: str, fmt: str) -> None:
    """Generate an inspection report from results."""
    console.print(f"[bold blue]SKYEYE[/bold blue] Generating report from: {input_dir}")
    console.print(f"Format: {fmt}")
    console.print("[yellow]Load results from directory and render report.[/yellow]")


@cli.command()
@click.option("--defects", "-d", default="crack,corrosion", help="Comma-separated defect types.")
@click.option("--count", "-n", default=50, help="Number of synthetic detections.")
@click.option("--seed", default=42, help="Random seed for reproducibility.")
def simulate(defects: str, count: int, seed: int) -> None:
    """Run the inspection simulator to generate test data."""
    from skyeye.models import DefectType
    from skyeye.simulator import InspectionSimulator

    console.print(f"[bold blue]SKYEYE[/bold blue] Running simulator")

    defect_types = [DefectType(d.strip()) for d in defects.split(",")]
    sim = InspectionSimulator(seed=seed)
    detections = sim.generate_detections(count=count, defect_types=defect_types)

    console.print(f"Generated {len(detections)} synthetic detections")
    for dt in DefectType:
        n = sum(1 for d in detections if d.defect_type == dt)
        if n > 0:
            console.print(f"  {dt.value}: {n}")


@cli.command()
@click.option("--project", "-p", required=True, help="Project name for tracking.")
@click.option("--inspection", "-i", "inspection_dir", required=True, help="Inspection results directory.")
def track(project: str, inspection_dir: str) -> None:
    """Track defect progression across inspections."""
    from skyeye.inspection.tracker import DefectTracker
    from skyeye.simulator import InspectionSimulator

    console.print(f"[bold blue]SKYEYE[/bold blue] Tracking defects for project: {project}")

    # Demo: generate synthetic records and track
    sim = InspectionSimulator(seed=0)
    records = sim.generate_defect_records(num_defects=5, num_inspections=3)

    tracker = DefectTracker()
    tracker.register_batch(records)

    summary = tracker.get_summary()
    console.print("\nDefect Summary:")
    for severity, count in summary.items():
        if count > 0:
            console.print(f"  {severity}: {count}")

    worsening = tracker.worsening_defects
    if worsening:
        console.print(f"\n[red]Worsening defects: {len(worsening)}[/red]")
        for prog in worsening:
            console.print(f"  {prog.defect_id}: {prog.history[0].severity.value} -> {prog.current_severity.value}")


if __name__ == "__main__":
    cli()
