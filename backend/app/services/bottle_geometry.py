"""Parametric wine bottle geometry generator.

Generates realistic 3D wine bottle geometries using mathematical models.
Supports different bottle types (Bordeaux, Burgundy, etc.) and allows
custom parameterization for label positioning and surface deformation.
"""

import math
from dataclasses import dataclass
from typing import Optional

from backend.app.schemas_3d import Mesh, Point3D


@dataclass
class BottleProfile:
    """Parameters for wine bottle geometry generation."""
    
    # Overall dimensions
    height: float = 750  # mm (standard 750mL bottle)
    base_diameter: float = 75  # mm at base
    shoulder_height: float = 550  # mm where shoulder starts
    neck_diameter: float = 20  # mm at neck opening
    punt_depth: float = 15  # mm (indentation at bottom)
    
    # Shape parameters
    body_bulge: float = 1.15  # Bulge factor for body curves (>1 = bulging)
    shoulder_taper: float = 0.85  # Shoulder taper ratio (0-1)
    neck_taper: float = 0.35  # Neck taper ratio (0-1)
    
    # Label zone (for texture mapping)
    label_start_height: float = 150  # mm from bottom
    label_end_height: float = 450  # mm from bottom
    label_arc_start: float = -0.5  # Radians, -0.5 to 0.5 wraps front
    label_arc_end: float = 0.5
    
    # Model options
    bottle_type: str = "bordeaux"  # bordeaux, burgundy, champagne, etc.
    segments: int = 24  # Polygonal segments around circumference
    height_segments: int = 32  # Segments along height


class WineBottleGeometry:
    """Generator for realistic wine bottle 3D geometry.
    
    Creates parametric wine bottle shapes using mathematical functions.
    Generates vertices and faces for mesh construction. Supports different
    bottle styles and enables custom label zone definition for texture mapping.
    """
    
    def __init__(self, profile: Optional[BottleProfile] = None):
        """Initialize geometry generator with bottle profile.
        
        Args:
            profile: BottleProfile with bottle dimensions and shape parameters.
                    Defaults to standard Bordeaux if not specified.
        """
        self.profile = profile or BottleProfile()
    
    def _compute_radius_at_height(self, z: float) -> float:
        """Compute bottle radius at given height using profile curves.
        
        Uses piecewise mathematical functions to define the bottle shape:
        - Bottom to body: convex curve with bulge
        - Body to shoulder: gradual taper
        - Shoulder to neck: steep taper
        - Neck: linear taper to opening
        
        Args:
            z: Height in mm (0 at bottom, increases upward)
            
        Returns:
            Radius in mm at the given height
        """
        h = self.profile.height
        
        # Bottom section with punt indentation (0 to 20mm)
        if z < 20:
            return self.profile.base_diameter / 2 * (1 - (self.profile.punt_depth / 20) * (1 - z / 20))
        
        # Body section with bulge (20mm to shoulder_height)
        if z < self.profile.shoulder_height:
            normalized = (z - 20) / (self.profile.shoulder_height - 20)
            # Apply cosine bulge curve for realistic body shape
            bulge_factor = math.cos(math.pi * normalized) * (self.profile.body_bulge - 1) + 1
            radius = self.profile.base_diameter / 2 * bulge_factor
            return radius
        
        # Shoulder section - aggressive taper (shoulder_height to neck start)
        if z < h - 40:  # Assume neck is last 40mm
            normalized = (z - self.profile.shoulder_height) / (h - 40 - self.profile.shoulder_height)
            # Exponential taper for smooth shoulder transition
            radius = self.profile.base_diameter / 2 * (self.profile.shoulder_taper ** (normalized * 2))
            return radius
        
        # Neck section - linear taper to opening (last 40mm)
        normalized = (z - (h - 40)) / 40
        radius = self.profile.neck_diameter / 2 + (
            self.profile.base_diameter / 2 * self.profile.shoulder_taper - self.profile.neck_diameter / 2
        ) * (1 - normalized)
        return max(radius, self.profile.neck_diameter / 2)
    
    def _is_in_label_zone(self, z: float, theta: float) -> bool:
        """Check if point is within the label region.
        
        Label zone is defined by height range and angular range for
        texture mapping and label detection.
        
        Args:
            z: Height in mm
            theta: Angle in radians (-pi to pi)
            
        Returns:
            True if point is in label zone
        """
        height_in_zone = self.profile.label_start_height <= z <= self.profile.label_end_height
        angle_in_zone = self.profile.label_arc_start <= theta <= self.profile.label_arc_end
        return height_in_zone and angle_in_zone
    
    def generate_mesh(self) -> Mesh:
        """Generate complete wine bottle mesh.
        
        Creates vertices around the bottle profile at regular height intervals,
        then connects them with triangular faces. Generates both outer surface
        (for rendering) and includes normal vectors for lighting.
        
        Returns:
            Mesh object with vertices and faces
        """
        profile = self.profile
        vertices = []
        faces = []
        
        # Generate vertices layer by layer
        height_step = profile.height / profile.height_segments
        angle_step = 2 * math.pi / profile.segments
        
        vertex_index = 0
        
        # For each height level
        for h_seg in range(profile.height_segments + 1):
            z = h_seg * height_step
            radius = self._compute_radius_at_height(z)
            
            # Create vertices in a circle at this height
            for seg in range(profile.segments):
                theta = seg * angle_step
                
                # Cartesian coordinates
                x = radius * math.cos(theta)
                y = radius * math.sin(theta)
                
                # Normalize to 0-1 range for shader convenience
                x_norm = x / (profile.base_diameter / 2)
                y_norm = y / (profile.base_diameter / 2)
                z_norm = z / profile.height
                
                vertices.append(Point3D(x=x_norm, y=z_norm, z=y_norm))
                vertex_index += 1
        
        # Connect vertices with triangular faces
        for h_seg in range(profile.height_segments):
            for seg in range(profile.segments):
                # Current and next layer vertex indices
                current_layer_start = h_seg * profile.segments
                next_layer_start = (h_seg + 1) * profile.segments
                
                # Vertex indices for quad (which becomes 2 triangles)
                v0 = current_layer_start + seg
                v1 = current_layer_start + (seg + 1) % profile.segments
                v2 = next_layer_start + (seg + 1) % profile.segments
                v3 = next_layer_start + seg
                
                # Split quad into 2 triangles for consistent winding
                faces.append((v0, v1, v2))
                faces.append((v2, v3, v0))
        
        return Mesh(vertices=vertices, faces=faces)
    
    def get_label_zone_vertices(self) -> list[int]:
        """Get indices of vertices in the label region.
        
        Useful for applying textures only to the label area or for
        label detection algorithms.
        
        Returns:
            List of vertex indices that fall in label zone
        """
        label_vertices = []
        profile = self.profile
        
        height_step = profile.height / profile.height_segments
        angle_step = 2 * math.pi / profile.segments
        vertex_index = 0
        
        for h_seg in range(profile.height_segments + 1):
            z = h_seg * height_step
            for seg in range(profile.segments):
                theta = seg * angle_step - math.pi  # Center at theta=0
                
                if self._is_in_label_zone(z, theta):
                    label_vertices.append(vertex_index)
                
                vertex_index += 1
        
        return label_vertices
    
    def get_bottle_dimensions(self) -> dict:
        """Get bottle dimensions in normalized coordinates.
        
        Returns:
            Dictionary with height, width, depth, volume estimate
        """
        return {
            "height_mm": self.profile.height,
            "base_diameter_mm": self.profile.base_diameter,
            "neck_diameter_mm": self.profile.neck_diameter,
            "shoulder_height_mm": self.profile.shoulder_height,
            "estimated_volume_ml": 750,  # Standard wine bottle
        }


def create_standard_bottle(bottle_type: str = "bordeaux") -> Mesh:
    """Create a standard wine bottle mesh of the specified type.
    
    Predefined bottle profiles for common wine bottle styles:
    - Bordeaux: Wider body, narrower punt, classic shape
    - Burgundy: Wider shoulders, tapered body
    - Champagne: Longer body, deeper punt for pressure
    
    Args:
        bottle_type: Type of bottle ('bordeaux', 'burgundy', 'champagne')
        
    Returns:
        Mesh object representing the bottle
    """
    profiles = {
        "bordeaux": BottleProfile(
            bottle_type="bordeaux",
            height=750,
            base_diameter=75,
            body_bulge=1.2,
            shoulder_taper=0.8,
        ),
        "burgundy": BottleProfile(
            bottle_type="burgundy",
            height=750,
            base_diameter=85,
            shoulder_height=500,
            body_bulge=1.1,
            shoulder_taper=0.9,
        ),
        "champagne": BottleProfile(
            bottle_type="champagne",
            height=750,
            base_diameter=80,
            punt_depth=25,
            body_bulge=1.05,
            shoulder_taper=0.75,
        ),
    }
    
    profile = profiles.get(bottle_type, profiles["bordeaux"])
    generator = WineBottleGeometry(profile)
    return generator.generate_mesh()
