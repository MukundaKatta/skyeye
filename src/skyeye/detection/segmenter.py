"""U-Net based segmenter for pixel-level defect mapping."""

from __future__ import annotations

from typing import Optional

import numpy as np
import torch
import torch.nn as nn

from skyeye.models import DefectType, SegmentationMask


class _DoubleConv(nn.Module):
    """Two consecutive conv-bn-relu blocks."""

    def __init__(self, in_ch: int, out_ch: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class _UNet(nn.Module):
    """U-Net architecture for semantic segmentation of defect regions.

    Encoder-decoder with skip connections for preserving spatial detail.
    Output channels correspond to defect type classes plus background.
    """

    def __init__(self, in_channels: int = 3, num_classes: int = 6, base_filters: int = 64) -> None:
        super().__init__()
        f = base_filters

        # Encoder
        self.enc1 = _DoubleConv(in_channels, f)
        self.pool1 = nn.MaxPool2d(2, 2)
        self.enc2 = _DoubleConv(f, f * 2)
        self.pool2 = nn.MaxPool2d(2, 2)
        self.enc3 = _DoubleConv(f * 2, f * 4)
        self.pool3 = nn.MaxPool2d(2, 2)
        self.enc4 = _DoubleConv(f * 4, f * 8)
        self.pool4 = nn.MaxPool2d(2, 2)

        # Bottleneck
        self.bottleneck = _DoubleConv(f * 8, f * 16)

        # Decoder
        self.up4 = nn.ConvTranspose2d(f * 16, f * 8, 2, stride=2)
        self.dec4 = _DoubleConv(f * 16, f * 8)
        self.up3 = nn.ConvTranspose2d(f * 8, f * 4, 2, stride=2)
        self.dec3 = _DoubleConv(f * 8, f * 4)
        self.up2 = nn.ConvTranspose2d(f * 4, f * 2, 2, stride=2)
        self.dec2 = _DoubleConv(f * 4, f * 2)
        self.up1 = nn.ConvTranspose2d(f * 2, f, 2, stride=2)
        self.dec1 = _DoubleConv(f * 2, f)

        self.final = nn.Conv2d(f, num_classes, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning per-pixel class logits.

        Args:
            x: Input tensor of shape (B, C, H, W). H and W must be
               divisible by 16.

        Returns:
            Logits tensor of shape (B, num_classes, H, W).
        """
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))
        e4 = self.enc4(self.pool3(e3))

        b = self.bottleneck(self.pool4(e4))

        d4 = self.dec4(torch.cat([self.up4(b), e4], dim=1))
        d3 = self.dec3(torch.cat([self.up3(d4), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))

        return self.final(d1)


class DefectSegmenter:
    """Pixel-level defect segmentation using U-Net.

    Produces a segmentation mask where each pixel is classified as
    background or one of the five defect types, enabling precise
    measurement of defect area and boundaries.
    """

    CLASS_NAMES: list[str] = ["background"] + [dt.value for dt in DefectType]

    def __init__(
        self,
        weights_path: Optional[str] = None,
        device: Optional[str] = None,
        base_filters: int = 64,
    ) -> None:
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        num_classes = len(self.CLASS_NAMES)
        self.model = _UNet(num_classes=num_classes, base_filters=base_filters).to(
            self.device
        )
        if weights_path:
            state_dict = torch.load(weights_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
        self.model.eval()

    def segment(self, image: np.ndarray) -> np.ndarray:
        """Produce a per-pixel defect class map.

        Args:
            image: Input image of shape (H, W, 3).

        Returns:
            Integer label map of shape (H, W) where 0 = background
            and 1..5 correspond to DefectType enum members.
        """
        tensor = self._preprocess(image)
        with torch.no_grad():
            logits = self.model(tensor)
        pred = torch.argmax(logits, dim=1).squeeze(0).cpu().numpy()
        return pred.astype(np.int32)

    def segment_to_masks(self, image: np.ndarray) -> list[SegmentationMask]:
        """Segment image and return structured mask metadata per defect class.

        Returns:
            List of SegmentationMask objects for each defect type found.
        """
        label_map = self.segment(image)
        h, w = label_map.shape
        total_pixels = h * w
        masks: list[SegmentationMask] = []

        for class_idx, defect_type in enumerate(DefectType, start=1):
            pixel_count = int(np.sum(label_map == class_idx))
            if pixel_count > 0:
                masks.append(
                    SegmentationMask(
                        width=w,
                        height=h,
                        defect_type=defect_type,
                        pixel_count=pixel_count,
                        coverage_ratio=round(pixel_count / total_pixels, 6),
                    )
                )
        return masks

    def _preprocess(self, image: np.ndarray) -> torch.Tensor:
        """Prepare image for U-Net inference.

        Pads the image so dimensions are divisible by 16.
        """
        if image.dtype == np.uint8:
            image = image.astype(np.float32) / 255.0
        if image.ndim == 2:
            image = np.stack([image] * 3, axis=-1)

        h, w = image.shape[:2]
        pad_h = (16 - h % 16) % 16
        pad_w = (16 - w % 16) % 16
        if pad_h > 0 or pad_w > 0:
            image = np.pad(image, ((0, pad_h), (0, pad_w), (0, 0)), mode="reflect")

        tensor = torch.from_numpy(image.transpose(2, 0, 1)).unsqueeze(0).float()
        return tensor.to(self.device)
