"""Lighting estimation from captured image.

Analyzes the image to estimate light direction, intensity, and color.
Returns lighting parameters suitable for Three.js scene setup.
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class LightingEstimate:
    """Estimated lighting parameters."""
    
    # Dominant directional light
    light_direction: Tuple[float, float, float]  # Normalized direction (x, y, z)
    light_intensity: float  # 0-1 scale
    light_color: Tuple[float, float, float]  # RGB (0-1)
    
    # Environment
    ambient_intensity: float  # Ambient light level
    ambient_color: Tuple[float, float, float]  # RGB
    
    # Shadows
    shadow_intensity: float  # How prominent are shadows
    
    def to_dict(self) -> dict:
        """Convert to serializable dict for JSON."""
        return {
            "light_direction": list(self.light_direction),
            "light_intensity": float(self.light_intensity),
            "light_color": list(self.light_color),
            "ambient_intensity": float(self.ambient_intensity),
            "ambient_color": list(self.ambient_color),
            "shadow_intensity": float(self.shadow_intensity),
        }


class LightingEstimator:
    """Estimates lighting conditions from image."""
    
    @staticmethod
    def estimate_from_image(image: np.ndarray, bottle_normal: Optional[np.ndarray] = None) -> LightingEstimate:
        """Estimate lighting from image.
        
        Analyzes brightness distribution and shadows to infer light direction,
        intensity, and color temperature.
        
        Args:
            image: Input bottle image (BGR)
            bottle_normal: Estimated bottle surface normal (unused in simple version)
            
        Returns:
            LightingEstimate with scene lighting parameters
        """
        # Convert to different color spaces for analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
        
        h, w = image.shape[:2]
        
        # Extract brightness (V from HSV)
        brightness = hsv[:, :, 2]
        
        # Find brightest regions (likely highlight areas)
        bright_threshold = np.percentile(brightness, 90)
        bright_mask = brightness > bright_threshold
        
        # Find darkest regions (likely shadows)
        dark_threshold = np.percentile(brightness, 20)
        dark_mask = brightness < dark_threshold
        
        # Estimate light direction from brightness gradient
        light_dir = LightingEstimator._estimate_light_direction(brightness)
        
        # Estimate light intensity from average brightness
        light_intensity = np.mean(brightness) / 255.0
        
        # Estimate light color from average color of bright regions
        if np.any(bright_mask):
            bright_pixels = image[bright_mask]
            avg_color = np.mean(bright_pixels, axis=0)  # BGR
            # Convert to RGB and normalize
            light_color = (avg_color[2] / 255.0, avg_color[1] / 255.0, avg_color[0] / 255.0)
        else:
            light_color = (1.0, 1.0, 1.0)  # Default white
        
        # Estimate ambient from average brightness in shadows
        if np.any(dark_mask):
            ambient_intensity = np.mean(brightness[dark_mask]) / 255.0
        else:
            ambient_intensity = np.mean(brightness) / 255.0 * 0.3
        
        # Ambient color: slightly warm (typical indoor lighting)
        ambient_color = LightingEstimator._estimate_ambient_color(image)
        
        # Shadow intensity: contrast between light and dark
        contrast = np.std(brightness)
        shadow_intensity = np.clip(contrast / 100.0, 0.2, 1.0)
        
        return LightingEstimate(
            light_direction=light_dir,
            light_intensity=float(np.clip(light_intensity, 0.5, 1.0)),
            light_color=light_color,
            ambient_intensity=float(np.clip(ambient_intensity, 0.1, 0.6)),
            ambient_color=ambient_color,
            shadow_intensity=float(shadow_intensity),
        )
    
    @staticmethod
    def _estimate_light_direction(brightness_map: np.ndarray) -> Tuple[float, float, float]:
        """Estimate light direction from brightness gradient.
        
        Assumes light comes from direction of highest brightness gradient.
        
        Args:
            brightness_map: Single-channel brightness/luminance
            
        Returns:
            Normalized direction vector (x, y, z)
        """
        # Compute gradients
        gx = cv2.Sobel(brightness_map, cv2.CV_32F, 1, 0, ksize=5)
        gy = cv2.Sobel(brightness_map, cv2.CV_32F, 0, 1, ksize=5)
        
        # Average gradient
        avg_gx = np.mean(gx)
        avg_gy = np.mean(gy)
        
        # Light comes from direction opposite to gradient
        # (gradient points toward darker, light points away)
        light_x = -avg_gx / 1000.0  # Scale for reasonable values
        light_y = -avg_gy / 1000.0
        light_z = 1.0  # Assume light generally comes from above
        
        # Normalize
        norm = np.sqrt(light_x**2 + light_y**2 + light_z**2)
        if norm > 0:
            light_x, light_y, light_z = light_x / norm, light_y / norm, light_z / norm
        else:
            light_x, light_y, light_z = 0.5, 0.5, 1.0
        
        return (float(light_x), float(light_y), float(light_z))
    
    @staticmethod
    def _estimate_ambient_color(image: np.ndarray) -> Tuple[float, float, float]:
        """Estimate ambient light color from image.
        
        Analyzes overall color cast to determine lighting color temperature.
        
        Args:
            image: BGR image
            
        Returns:
            Ambient color in RGB (0-1)
        """
        # Compute average color
        b_avg = np.mean(image[:, :, 0]) / 255.0
        g_avg = np.mean(image[:, :, 1]) / 255.0
        r_avg = np.mean(image[:, :, 2]) / 255.0
        
        # Normalize to reasonable intensity
        max_val = max(r_avg, g_avg, b_avg)
        if max_val > 0:
            r_avg, g_avg, b_avg = r_avg / max_val, g_avg / max_val, b_avg / max_val
        
        # Return as RGB (opposite of BGR)
        return (r_avg, g_avg, b_avg)
    
    @staticmethod
    def estimate_shadow_intensity(image: np.ndarray) -> float:
        """Estimate how strong shadows are in the image.
        
        Args:
            image: Input image
            
        Returns:
            Shadow intensity (0-1)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
        
        # Compute local contrast (shadow indicator)
        contrast_map = cv2.Laplacian(gray, cv2.CV_32F)
        contrast = np.std(contrast_map)
        
        # Normalize to 0-1
        shadow_intensity = np.clip(contrast / 50.0, 0, 1)
        
        return float(shadow_intensity)


class ThreeJSLightingConfig:
    """Converts lighting estimate to Three.js scene configuration."""
    
    @staticmethod
    def generate_threejs_config(lighting: LightingEstimate) -> dict:
        """Generate Three.js lighting setup.
        
        Args:
            lighting: LightingEstimate from image analysis
            
        Returns:
            Dict with directional light and ambient light config
        """
        return {
            "directionalLight": {
                "position": list(np.array(lighting.light_direction) * 5.0),  # Place at distance
                "intensity": lighting.light_intensity,
                "color": {
                    "r": lighting.light_color[0],
                    "g": lighting.light_color[1],
                    "b": lighting.light_color[2],
                },
                "castShadow": True,
                "shadowMapSize": 1024,
            },
            "ambientLight": {
                "intensity": lighting.ambient_intensity,
                "color": {
                    "r": lighting.ambient_color[0],
                    "g": lighting.ambient_color[1],
                    "b": lighting.ambient_color[2],
                },
            },
            "shadowIntensity": lighting.shadow_intensity,
            "exposure": 1.0 + (lighting.light_intensity - 0.5),  # Adjust exposure
        }
    
    @staticmethod
    def generate_ibl_config(image: np.ndarray) -> dict:
        """Generate image-based lighting config (for future use with IBL).
        
        Args:
            image: Original image (can be used to generate environment map)
            
        Returns:
            IBL configuration dict
        """
        # This is a placeholder for future IBL/environment mapping support
        # Would generate or reference an environment map texture
        return {
            "useIBL": False,
            "environmentMap": None,
            "environmentIntensity": 0.5,
        }
