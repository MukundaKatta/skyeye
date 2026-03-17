"""Tests for detection modules."""

import numpy as np
import pytest

from skyeye.detection.defect_detector import DefectDetector
from skyeye.detection.classifier import SeverityClassifier
from skyeye.detection.segmenter import DefectSegmenter
from skyeye.models import BoundingBox, DefectType, Detection, SeverityLevel


class TestDefectDetector:
    def test_initialization(self):
        detector = DefectDetector(confidence_threshold=0.3, base_filters=16)
        assert detector.confidence_threshold == 0.3
        assert len(detector.DEFECT_CLASSES) == 5

    def test_detect_returns_list(self):
        detector = DefectDetector(confidence_threshold=0.0, base_filters=16)
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        results = detector.detect(image)
        assert isinstance(results, list)
        for det in results:
            assert isinstance(det, Detection)
            assert 0 <= det.confidence <= 1

    def test_detect_respects_threshold(self):
        detector = DefectDetector(confidence_threshold=0.99, base_filters=16)
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        results = detector.detect(image)
        for det in results:
            assert det.confidence >= 0.99

    def test_detect_batch(self):
        detector = DefectDetector(confidence_threshold=0.0, base_filters=16)
        images = [np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8) for _ in range(3)]
        batch_results = detector.detect_batch(images)
        assert len(batch_results) == 3

    def test_preprocess_grayscale(self):
        detector = DefectDetector(base_filters=16)
        gray = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        tensor = detector._preprocess(gray)
        assert tensor.shape == (1, 3, 64, 64)

    def test_preprocess_float_input(self):
        detector = DefectDetector(base_filters=16)
        img = np.random.rand(64, 64, 3).astype(np.float32)
        tensor = detector._preprocess(img)
        assert tensor.shape == (1, 3, 64, 64)


class TestSeverityClassifier:
    def test_initialization(self):
        classifier = SeverityClassifier(patch_size=32)
        assert classifier.patch_size == 32
        assert len(classifier.SEVERITY_LEVELS) == 4

    def test_classify_returns_severity(self):
        classifier = SeverityClassifier(patch_size=32)
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        severity = classifier.classify(image)
        assert isinstance(severity, SeverityLevel)

    def test_classify_with_detection(self):
        classifier = SeverityClassifier(patch_size=32)
        image = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        detection = Detection(
            defect_type=DefectType.CRACK,
            confidence=0.9,
            bounding_box=BoundingBox(x_min=10, y_min=10, x_max=60, y_max=60),
        )
        severity = classifier.classify(image, detection)
        assert isinstance(severity, SeverityLevel)

    def test_classify_with_confidence(self):
        classifier = SeverityClassifier(patch_size=32)
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        severity, confidence = classifier.classify_with_confidence(image)
        assert isinstance(severity, SeverityLevel)
        assert 0 <= confidence <= 1


class TestDefectSegmenter:
    def test_initialization(self):
        segmenter = DefectSegmenter(base_filters=8)
        assert len(segmenter.CLASS_NAMES) == 6

    def test_segment_returns_label_map(self):
        segmenter = DefectSegmenter(base_filters=8)
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        label_map = segmenter.segment(image)
        assert label_map.shape == (64, 64)
        assert label_map.dtype == np.int32

    def test_segment_to_masks(self):
        segmenter = DefectSegmenter(base_filters=8)
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        masks = segmenter.segment_to_masks(image)
        assert isinstance(masks, list)

    def test_preprocess_padding(self):
        segmenter = DefectSegmenter(base_filters=8)
        # Image not divisible by 16
        image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        tensor = segmenter._preprocess(image)
        _, _, h, w = tensor.shape
        assert h % 16 == 0
        assert w % 16 == 0
