"""CNN-based defect detector for infrastructure inspection imagery."""

from __future__ import annotations

from typing import Optional

import numpy as np
import torch
import torch.nn as nn

from skyeye.models import BoundingBox, DefectType, Detection


class _DefectDetectorBackbone(nn.Module):
    """Convolutional neural network backbone for defect detection.

    Architecture: a multi-scale feature extractor with region proposal
    capability for localizing infrastructure defects.
    """

    NUM_CLASSES = len(DefectType)

    def __init__(self, in_channels: int = 3, base_filters: int = 64) -> None:
        super().__init__()
        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(in_channels, base_filters, kernel_size=3, padding=1),
            nn.BatchNorm2d(base_filters),
            nn.ReLU(inplace=True),
            nn.Conv2d(base_filters, base_filters, kernel_size=3, padding=1),
            nn.BatchNorm2d(base_filters),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            # Block 2
            nn.Conv2d(base_filters, base_filters * 2, kernel_size=3, padding=1),
            nn.BatchNorm2d(base_filters * 2),
            nn.ReLU(inplace=True),
            nn.Conv2d(base_filters * 2, base_filters * 2, kernel_size=3, padding=1),
            nn.BatchNorm2d(base_filters * 2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            # Block 3
            nn.Conv2d(base_filters * 2, base_filters * 4, kernel_size=3, padding=1),
            nn.BatchNorm2d(base_filters * 4),
            nn.ReLU(inplace=True),
            nn.Conv2d(base_filters * 4, base_filters * 4, kernel_size=3, padding=1),
            nn.BatchNorm2d(base_filters * 4),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((7, 7)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(base_filters * 4 * 7 * 7, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, self.NUM_CLASSES),
        )
        self.box_regressor = nn.Sequential(
            nn.Flatten(),
            nn.Linear(base_filters * 4 * 7 * 7, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, 4),  # x_min, y_min, x_max, y_max
            nn.Sigmoid(),
        )

    def forward(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass returning class logits and bounding box predictions.

        Args:
            x: Input image tensor of shape (B, C, H, W).

        Returns:
            Tuple of (class_logits [B, NUM_CLASSES], boxes [B, 4]).
        """
        features = self.features(x)
        class_logits = self.classifier(features)
        boxes = self.box_regressor(features)
        return class_logits, boxes


class DefectDetector:
    """High-level defect detection interface.

    Wraps the CNN backbone and provides methods for running inference
    on drone-captured images, returning structured Detection results.

    Detectable defect types:
        - Cracks
        - Corrosion
        - Spalling
        - Deformation
        - Vegetation growth
    """

    DEFECT_CLASSES: list[DefectType] = list(DefectType)

    def __init__(
        self,
        weights_path: Optional[str] = None,
        device: Optional[str] = None,
        confidence_threshold: float = 0.5,
        base_filters: int = 64,
    ) -> None:
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.confidence_threshold = confidence_threshold
        self.model = _DefectDetectorBackbone(base_filters=base_filters).to(self.device)
        if weights_path:
            state_dict = torch.load(weights_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
        self.model.eval()

    def detect(self, image: np.ndarray) -> list[Detection]:
        """Detect defects in a single image.

        Args:
            image: Input image as a numpy array of shape (H, W, 3) with
                   values in [0, 255] (uint8) or [0.0, 1.0] (float).

        Returns:
            List of Detection objects exceeding the confidence threshold.
        """
        tensor = self._preprocess(image)
        with torch.no_grad():
            class_logits, boxes = self.model(tensor)

        probabilities = torch.softmax(class_logits, dim=-1).squeeze(0)
        box_coords = boxes.squeeze(0).cpu().numpy()
        h, w = image.shape[:2]

        detections: list[Detection] = []
        for class_idx, prob in enumerate(probabilities):
            conf = prob.item()
            if conf >= self.confidence_threshold:
                detections.append(
                    Detection(
                        defect_type=self.DEFECT_CLASSES[class_idx],
                        confidence=round(conf, 4),
                        bounding_box=BoundingBox(
                            x_min=float(box_coords[0] * w),
                            y_min=float(box_coords[1] * h),
                            x_max=float(box_coords[2] * w),
                            y_max=float(box_coords[3] * h),
                        ),
                    )
                )
        return detections

    def detect_batch(self, images: list[np.ndarray]) -> list[list[Detection]]:
        """Run detection on a batch of images.

        Args:
            images: List of input images.

        Returns:
            List of detection lists, one per input image.
        """
        return [self.detect(img) for img in images]

    def _preprocess(self, image: np.ndarray) -> torch.Tensor:
        """Convert a numpy image to a model-ready tensor."""
        if image.dtype == np.uint8:
            image = image.astype(np.float32) / 255.0
        if image.ndim == 2:
            image = np.stack([image] * 3, axis=-1)
        # HWC -> CHW, add batch dim
        tensor = torch.from_numpy(image.transpose(2, 0, 1)).unsqueeze(0).float()
        return tensor.to(self.device)
