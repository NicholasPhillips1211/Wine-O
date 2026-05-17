"""Wine label detection and extraction from bottle images.

Provides functionality to detect wine label regions in bottle photographs,
extract the label texture, and prepare it for mapping onto 3D bottle geometry.
Uses image processing and contour detection to isolate label regions.
"""

import io
import base64
from typing import Optional, Tuple
from dataclasses import dataclass

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency fallback
    cv2 = None
import numpy as np
from PIL import Image


@dataclass
class LabelDetectionResult:
    """Result of wine label detection."""
    
    detected: bool  # Whether a label was detected
    label_image: Optional[np.ndarray] = None  # Extracted label image
    confidence: float = 0.0  # Detection confidence 0-1
    bounding_box: Optional[Tuple[int, int, int, int]] = None  # (x, y, w, h)
    label_mask: Optional[np.ndarray] = None  # Binary mask of label region
    orientation_angle: float = 0.0  # Rotation angle in degrees
    dominant_colors: Optional[list[Tuple[int, int, int]]] = None  # Top 3 colors


class LabelDetector:
    """Detects and extracts wine labels from bottle photographs.
    
    Uses contour detection and color analysis to locate wine label regions
    in bottle images. Handles various lighting conditions and bottle angles.
    Extracts and preprocesses label texture for 3D mapping.
    """
    
    def __init__(self):
        """Initialize label detector."""
        # Color ranges for common label materials (HSV format)
        self.label_color_ranges = [
            # Green/gold labels (common in white wines)
            ((20, 50, 100), (40, 255, 255)),
            # Red/burgundy labels (Bordeaux, Burgundy wines)
            ((0, 100, 100), (10, 255, 255)),
            ((170, 100, 100), (180, 255, 255)),
            # White/cream labels (common background)
            ((0, 0, 150), (180, 50, 255)),
            # Dark labels (black text, logos)
            ((0, 0, 0), (180, 255, 100)),
        ]
    
    def detect_label(self, image: np.ndarray) -> LabelDetectionResult:
        """Detect wine label region in bottle image.
        
        Analyzes image to find label location using:
        - Color range filtering
        - Contour detection
        - Shape analysis
        - Confidence scoring
        
        Args:
            image: Input image as numpy array (BGR format from OpenCV)
            
        Returns:
            LabelDetectionResult with detection status and label region
        """
        if image is None or image.size == 0:
            return LabelDetectionResult(detected=False)
        if cv2 is None:
            return LabelDetectionResult(detected=False)
        
        # Convert to HSV for better color-based detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, w, _ = image.shape
        
        # Create composite mask from all label color ranges
        mask = np.zeros((h, w), dtype=np.uint8)
        for lower, upper in self.label_color_ranges:
            range_mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            mask = cv2.bitwise_or(mask, range_mask)
        
        # Clean up mask with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return LabelDetectionResult(detected=False)
        
        # Find largest contour (likely the label)
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        # Label should be significant portion of image
        if area < (h * w * 0.05):  # At least 5% of image
            return LabelDetectionResult(detected=False)
        
        # Get bounding rectangle and rotated rectangle
        x, y, bw, bh = cv2.boundingRect(largest_contour)
        rect = cv2.minAreaRect(largest_contour)
        angle = rect[2]
        
        # Extract label region
        label_image = image[y:y+bh, x:x+bw]
        
        # Create label mask
        label_mask = np.zeros((bh, bw), dtype=np.uint8)
        contour_offset = largest_contour - np.array([x, y])
        cv2.drawContours(label_mask, [contour_offset], 0, 255, -1)
        
        # Calculate confidence based on contour properties
        rect_area = bw * bh
        fill_ratio = area / rect_area if rect_area > 0 else 0
        confidence = min(0.99, fill_ratio * 0.8 + 0.2)  # Weight towards 0.2-0.99
        
        # Extract dominant colors
        dominant_colors = self._extract_dominant_colors(label_image, 3)
        
        return LabelDetectionResult(
            detected=True,
            label_image=label_image,
            confidence=confidence,
            bounding_box=(x, y, bw, bh),
            label_mask=label_mask,
            orientation_angle=angle,
            dominant_colors=dominant_colors,
        )
    
    def _extract_dominant_colors(self, image: np.ndarray, num_colors: int = 3) -> list[Tuple[int, int, int]]:
        """Extract dominant colors from label image.
        
        Useful for identifying brand colors and verifying label authenticity.
        
        Args:
            image: Label image (BGR)
            num_colors: Number of dominant colors to extract
            
        Returns:
            List of (B, G, R) tuples for top colors
        """
        if image.size == 0:
            return [(0, 0, 0)] * num_colors
        
        # Reshape image to 2D array of pixels
        pixels = image.reshape((-1, 3))
        pixels = np.float32(pixels)
        
        # K-means clustering for dominant colors
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, _, centers = cv2.kmeans(
            pixels, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
        )
        
        centers = np.uint8(centers)
        return [tuple(color) for color in centers]
    
    def extract_label_texture(
        self, 
        image: np.ndarray, 
        target_size: Tuple[int, int] = (512, 256)
    ) -> Optional[np.ndarray]:
        """Extract and prepare label texture for 3D mapping.
        
        Detects label, extracts it, and resizes to standard texture size.
        Applies perspective correction if needed.
        
        Args:
            image: Input bottle image (BGR)
            target_size: Target texture resolution (width, height)
            
        Returns:
            Extracted label texture or None if detection failed
        """
        if cv2 is None:
            return None

        result = self.detect_label(image)
        
        if not result.detected or result.label_image is None:
            return None
        
        # Resize to target dimensions
        texture = cv2.resize(result.label_image, target_size, interpolation=cv2.INTER_CUBIC)
        
        # Enhance contrast for better texture quality
        lab = cv2.cvtColor(texture, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)
        enhanced = cv2.merge([l_channel, a, b])
        texture = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return texture
    
    def batch_extract_labels(
        self, 
        images: list[np.ndarray],
        target_size: Tuple[int, int] = (512, 256)
    ) -> list[Optional[np.ndarray]]:
        """Extract labels from multiple images.
        
        Args:
            images: List of bottle images
            target_size: Target texture resolution
            
        Returns:
            List of extracted label textures (None for failed detections)
        """
        return [self.extract_label_texture(img, target_size) for img in images]
    
    def image_to_base64(self, image: np.ndarray) -> str:
        """Convert image to base64 string for storage/transmission.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Base64 encoded string
        """
        if image is None or image.size == 0:
            return ""
        if cv2 is None:
            return ""
        
        _, buffer = cv2.imencode('.png', image)
        return base64.b64encode(buffer).decode('utf-8')
    
    def base64_to_image(self, b64_string: str) -> Optional[np.ndarray]:
        """Convert base64 string back to image.
        
        Args:
            b64_string: Base64 encoded image string
            
        Returns:
            Image as numpy array or None if decoding failed
        """
        try:
            if cv2 is None:
                return None
            image_data = base64.b64decode(b64_string)
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception:
            return None


async def download_and_extract_label(image_url: str) -> Tuple[bool, Optional[np.ndarray]]:
    """Download bottle image from URL and extract label.
    
    Fetches image from web and processes it for label extraction.
    Useful for OCR integration - download images from OCR results.
    
    Args:
        image_url: URL to bottle image
        
    Returns:
        Tuple of (success, label_texture or None)
    """
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(image_url, follow_redirects=True)
            if response.status_code != 200:
                return False, None
            
            image_data = np.frombuffer(response.content, dtype=np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            
            detector = LabelDetector()
            texture = detector.extract_label_texture(image)
            return texture is not None, texture
            
    except Exception:
        return False, None
