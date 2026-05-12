"""Normal map generation and PBR material estimation.

Generates normal maps from shading and estimated surface properties
for physically-based rendering. Creates roughness and metallic maps
to reproduce specular highlights and surface details.
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class PBRMaterial:
    """Physically-based rendering material."""
    base_color: np.ndarray  # (H, W, 3) BGR texture
    normal_map: np.ndarray  # (H, W, 3) normal map in tangent space
    roughness_map: np.ndarray  # (H, W, 1) roughness 0-1
    metallic_map: np.ndarray  # (H, W, 1) metallic 0-1
    ambient_occlusion: Optional[np.ndarray] = None  # (H, W, 1) AO


class NormalMapGenerator:
    """Generates normal maps from image using multiple techniques."""
    
    @staticmethod
    def from_sobel_edges(image: np.ndarray) -> np.ndarray:
        """Generate normal map using Sobel derivatives.
        
        Treats the image luminance as a height field and computes
        surface normals from local gradients. Simple but fast.
        
        Args:
            image: Input image (BGR)
            
        Returns:
            Normal map in tangent space (H, W, 3) with Z-up convention
        """
        # Convert to grayscale luminance
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        
        # Compute gradients
        sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        
        h, w = gray.shape
        normal_map = np.zeros((h, w, 3), dtype=np.float32)
        
        # Normal from height field: N = (-dh/dx, -dh/dy, 1) normalized
        normal_map[:, :, 0] = -sobelx * 2.0  # X component (scale for visibility)
        normal_map[:, :, 1] = -sobely * 2.0  # Y component
        normal_map[:, :, 2] = 1.0  # Z component (up)
        
        # Normalize to unit vectors
        norm = np.linalg.norm(normal_map, axis=2, keepdims=True)
        norm[norm == 0] = 1
        normal_map /= norm
        
        # Convert from [-1, 1] to [0, 1] for texture (standard)
        normal_map = (normal_map + 1.0) / 2.0
        
        return (normal_map * 255).astype(np.uint8)
    
    @staticmethod
    def from_laplacian(image: np.ndarray) -> np.ndarray:
        """Generate normal map using Laplacian (captures finer details).
        
        Uses Laplacian as a measure of curvature to highlight surface variations.
        
        Args:
            image: Input image
            
        Returns:
            Normal map in tangent space
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        
        # Apply Gaussian blur for smoothness
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
        
        # Compute gradients
        gx = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
        
        # Laplacian for detail
        laplacian = cv2.Laplacian(blurred, cv2.CV_32F)
        
        h, w = gray.shape
        normal_map = np.zeros((h, w, 3), dtype=np.float32)
        
        # Combine Sobel and Laplacian
        normal_map[:, :, 0] = gx
        normal_map[:, :, 1] = gy
        normal_map[:, :, 2] = 1.0 + np.abs(laplacian) * 0.5  # Emphasize curvature
        
        # Normalize
        norm = np.linalg.norm(normal_map, axis=2, keepdims=True)
        norm[norm == 0] = 1
        normal_map /= norm
        
        normal_map = (normal_map + 1.0) / 2.0
        return (normal_map * 255).astype(np.uint8)
    
    @staticmethod
    def from_alpha_blend(image: np.ndarray, strength: float = 0.5) -> np.ndarray:
        """Blend multiple normal map methods for better results.
        
        Args:
            image: Input image
            strength: Blend strength (0-1)
            
        Returns:
            Blended normal map
        """
        map1 = NormalMapGenerator.from_sobel_edges(image).astype(np.float32)
        map2 = NormalMapGenerator.from_laplacian(image).astype(np.float32)
        
        blended = cv2.addWeighted(map1, 1 - strength, map2, strength, 0)
        return np.clip(blended, 0, 255).astype(np.uint8)


class RoughnessMapGenerator:
    """Generates roughness maps from image texture analysis."""
    
    @staticmethod
    def from_variance(image: np.ndarray, window_size: int = 5) -> np.ndarray:
        """Generate roughness map from local pixel variance.
        
        High variance (detail, speckling) = high roughness.
        Smooth regions = low roughness (more specular).
        
        Args:
            image: Input image
            window_size: Local window for variance computation
            
        Returns:
            Roughness map (H, W, 1) in range [0, 1]
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        
        h, w = gray.shape
        roughness = np.zeros((h, w), dtype=np.float32)
        
        half_win = window_size // 2
        
        for y in range(half_win, h - half_win):
            for x in range(half_win, w - half_win):
                window = gray[y-half_win:y+half_win+1, x-half_win:x+half_win+1]
                variance = np.var(window)
                roughness[y, x] = min(1.0, variance * 10)  # Scale variance to [0, 1]
        
        # Smooth the result
        roughness = cv2.GaussianBlur(roughness, (5, 5), 1.0)
        
        return (roughness * 255).astype(np.uint8)
    
    @staticmethod
    def from_luminance_gradient(image: np.ndarray) -> np.ndarray:
        """Generate roughness from luminance gradients.
        
        Sharp luminance changes indicate surface details/roughness.
        
        Args:
            image: Input image
            
        Returns:
            Roughness map
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        
        # Compute magnitude of gradients
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(gx**2 + gy**2)
        
        # Normalize to [0, 1]
        grad_max = np.max(gradient_mag)
        if grad_max > 0:
            gradient_mag /= grad_max
        
        # Higher gradient = higher roughness, but inverted (smooth regions are glossy)
        roughness = 1.0 - np.clip(gradient_mag, 0, 1)
        
        return (roughness * 255).astype(np.uint8)


class MetallicMapGenerator:
    """Generates metallic/specular maps."""
    
    @staticmethod
    def from_color_saturation(image: np.ndarray) -> np.ndarray:
        """Generate metallic map from color saturation.
        
        High saturation = less metallic (colored plastic/paper).
        Low saturation = more metallic (reflective foil/ink).
        
        Args:
            image: Input image
            
        Returns:
            Metallic map (H, W, 1) in range [0, 1]
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        saturation = hsv[:, :, 1] / 255.0
        
        # Invert: low saturation = high metallic
        metallic = 1.0 - saturation
        
        # Most labels are not very metallic, so scale down
        metallic = metallic * 0.3  # Cap at 0.3 metallic
        
        return (metallic * 255).astype(np.uint8)
    
    @staticmethod
    def from_brightness(image: np.ndarray) -> np.ndarray:
        """Generate metallic map from brightness.
        
        Very bright regions might be specular highlights (metallic ink).
        
        Args:
            image: Input image
            
        Returns:
            Metallic map
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        
        # High brightness = potentially metallic ink
        metallic = gray * 0.2  # Keep mostly non-metallic
        
        return (metallic * 255).astype(np.uint8)


class AOGenerator:
    """Ambient occlusion map generation."""
    
    @staticmethod
    def from_edges(image: np.ndarray) -> np.ndarray:
        """Generate AO map highlighting edges and crevices.
        
        Edges and corners cast shadows, reducing ambient light.
        
        Args:
            image: Input image
            
        Returns:
            AO map (H, W, 1)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate edges to create soft shadows
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        ao_mask = cv2.dilate(edges.astype(np.float32), kernel, iterations=2)
        
        # Invert: edges = dark (low AO)
        ao = 1.0 - np.clip(ao_mask / 255.0, 0, 1)
        
        # Smooth
        ao = cv2.GaussianBlur(ao, (9, 9), 2.0)
        
        return (ao * 255).astype(np.uint8)


def generate_pbr_material(label_texture: np.ndarray) -> PBRMaterial:
    """Generate complete PBR material from label texture.
    
    Creates normal, roughness, metallic, and AO maps suitable for
    physically-based rendering in Three.js.
    
    Args:
        label_texture: Input label texture (BGR)
        
    Returns:
        Complete PBRMaterial object
    """
    # Generate all maps
    normal_map = NormalMapGenerator.from_alpha_blend(label_texture, strength=0.5)
    roughness_map = RoughnessMapGenerator.from_variance(label_texture)
    metallic_map = MetallicMapGenerator.from_color_saturation(label_texture)
    ao_map = AOGenerator.from_edges(label_texture)
    
    return PBRMaterial(
        base_color=label_texture,
        normal_map=normal_map,
        roughness_map=roughness_map,
        metallic_map=metallic_map,
        ambient_occlusion=ao_map
    )
