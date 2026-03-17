# SKYEYE - Drone Inspection Analyzer

SKYEYE is an AI-powered drone inspection analysis platform for detecting and classifying infrastructure defects. It leverages convolutional neural networks and U-Net segmentation to identify cracks, corrosion, spalling, deformation, and vegetation growth across bridges, buildings, and powerlines.

## Features

- **Defect Detection**: CNN-based detection of five defect categories (cracks, corrosion, spalling, deformation, vegetation growth)
- **Severity Classification**: Automated grading of defects as minor, moderate, severe, or critical
- **Pixel-Level Segmentation**: U-Net architecture for precise defect boundary mapping
- **Flight Planning**: Configurable inspection flight plans with waypoints, altitude, and overlap settings
- **Defect Tracking**: Monitor defect progression over time across repeated inspections
- **Infrastructure Standards**: Built-in inspection protocols for bridges, buildings, and powerlines
- **Report Generation**: Automated inspection reports with findings, recommendations, and priority levels
- **Simulation**: Built-in simulator for testing detection pipelines without physical drone hardware

## Installation

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Usage

### CLI

```bash
# Run inspection analysis on captured images
skyeye analyze --input ./images --output ./report --type bridge

# Plan an inspection flight
skyeye plan --structure bridge --lat 40.7128 --lon -74.0060 --altitude 30

# Generate an inspection report
skyeye report --input ./results --format pdf

# Run the simulator
skyeye simulate --defects cracks,corrosion --count 50

# Track defect progression
skyeye track --project my-bridge --inspection ./results
```

### Python API

```python
from skyeye.detection.defect_detector import DefectDetector
from skyeye.detection.classifier import SeverityClassifier
from skyeye.inspection.report import InspectionReport

detector = DefectDetector()
classifier = SeverityClassifier()

detections = detector.detect(image)
for det in detections:
    severity = classifier.classify(det)
```

## Project Structure

```
src/skyeye/
    cli.py                  # Click-based CLI interface
    models.py               # Pydantic data models
    simulator.py            # Inspection simulator
    report.py               # Report generation
    detection/
        defect_detector.py  # CNN defect detection
        classifier.py       # Severity classification
        segmenter.py        # U-Net segmentation
    inspection/
        flight.py           # Flight planning
        report.py           # Inspection report builder
        tracker.py          # Defect progression tracking
    infrastructure/
        bridges.py          # Bridge inspection standards
        buildings.py        # Building inspection standards
        powerlines.py       # Powerline inspection standards
```

## Author

Mukunda Katta

## License

MIT
