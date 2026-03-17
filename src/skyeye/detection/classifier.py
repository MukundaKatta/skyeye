"""Severity classifier for grading detected infrastructure defects."""

from __future__ import annotations

from typing import Optional

import numpy as np
import torch
import torch.nn as nn

from skyeye.models import Detection, SeverityLevel


class _SeverityNet(nn.Module):
    """CNN for classifying defect severity from cropped image patches."""

    NUM_LEVELS = len(SeverityLevel)

    def __init__(self, in_channels: int = 3, base_filters: int = 32) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, base_filters, 3, padding=1),
            nn.BatchNorm2d(base_filters),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(base_filters, base_filters * 2, 3, padding=1),
            nn.BatchNorm2d(base_filters * 2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(base_filters * 2, base_filters * 4, 3, padding=1),
            nn.BatchNorm2d(base_filters * 4),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(base_filters * 4 * 4 * 4, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, self.NUM_LEVELS),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Return severity class logits of shape (B, NUM_LEVELS)."""
        return self.classifier(self.features(x))


class SeverityClassifier:
    """Classify the severity of a detected defect.

    Grades defects into four levels:
        - minor: cosmetic or surface-level damage, no structural concern
        - moderate: noticeable degradation requiring monitoring
        - severe: significant damage requiring near-term repair
        - critical: immediate safety hazard, urgent action required
    """

    SEVERITY_LEVELS: list[SeverityLevel] = list(SeverityLevel)

    def __init__(
        self,
        weights_path: Optional[str] = None,
        device: Optional[str] = None,
        patch_size: int = 64,
    ) -> None:
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.patch_size = patch_size
        self.model = _SeverityNet().to(self.device)
        if weights_path:
            state_dict = torch.load(weights_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
        self.model.eval()

    def classify(self, image: np.ndarray, detection: Optional[Detection] = None) -> SeverityLevel:
        """Classify the severity of a defect.

        Args:
            image: Full image or pre-cropped defect patch (H, W, 3).
            detection: Optional detection with bounding box. If provided,
                       the defect region is cropped from the image.

        Returns:
            The predicted SeverityLevel.
        """
        patch = self._extract_patch(image, detection)
        tensor = self._preprocess(patch)
        with torch.no_grad():
            logits = self.model(tensor)
        pred_idx = torch.argmax(logits, dim=-1).item()
        return self.SEVERITY_LEVELS[pred_idx]

    def classify_with_confidence(
        self, image: np.ndarray, detection: Optional[Detection] = None
    ) -> tuple[SeverityLevel, float]:
        """Classify severity and return the confidence score.

        Returns:
            Tuple of (SeverityLevel, confidence).
        """
        patch = self._extract_patch(image, detection)
        tensor = self._preprocess(patch)
        with torch.no_grad():
            logits = self.model(tensor)
        probs = torch.softmax(logits, dim=-1).squeeze(0)
        pred_idx = torch.argmax(probs).item()
        return self.SEVERITY_LEVELS[pred_idx], round(probs[pred_idx].item(), 4)

    def _extract_patch(self, image: np.ndarray, detection: Optional[Detection]) -> np.ndarray:
        """Crop the defect region from the image if detection is provided."""
        if detection is None:
            return image
        bb = detection.bounding_box
        h, w = image.shape[:2]
        x1 = max(0, int(bb.x_min))
        y1 = max(0, int(bb.y_min))
        x2 = min(w, int(bb.x_max))
        y2 = min(h, int(bb.y_max))
        return image[y1:y2, x1:x2]

    def _preprocess(self, patch: np.ndarray) -> torch.Tensor:
        """Resize and normalize a patch for the severity network."""
        if patch.dtype == np.uint8:
            patch = patch.astype(np.float32) / 255.0
        if patch.ndim == 2:
            patch = np.stack([patch] * 3, axis=-1)
        # Simple resize via nearest-neighbor interpolation
        h, w = patch.shape[:2]
        if h != self.patch_size or w != self.patch_size:
            y_indices = np.linspace(0, h - 1, self.patch_size).astype(int)
            x_indices = np.linspace(0, w - 1, self.patch_size).astype(int)
            patch = patch[np.ix_(y_indices, x_indices)]
        tensor = torch.from_numpy(patch.transpose(2, 0, 1)).unsqueeze(0).float()
        return tensor.to(self.device)
