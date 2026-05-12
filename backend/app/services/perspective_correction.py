"""Perspective-correct label warping and camera pose estimation.

Handles homography-based perspective correction of wine labels to match
the angle and position they appear in the captured image. Estimates camera
pose relative to the bottle to enable photo-realistic 3D rendering.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class CameraIntrinsics:
    """Camera intrinsic parameters."""
    fx: float  # Focal length X
    fy: float  # Focal length Y
    cx: float  # Principal point X
    cy: float  # Principal point Y
    width: int
    height: int
    
    def to_matrix(self) -> np.ndarray:
        """Return as 3x3 camera matrix K."""
        return np.array([
            [self.fx, 0, self.cx],
            [0, self.fy, self.cy],
            [0, 0, 1]
        ], dtype=np.float32)


@dataclass
class CameraPose:
    """Camera extrinsic parameters (pose in 3D space)."""
    position: Tuple[float, float, float]  # (x, y, z) camera location
    rotation: np.ndarray  # 3x3 rotation matrix (world-to-camera)
    quaternion: Tuple[float, float, float, float]  # (qx, qy, qz, qw)
    
    def to_matrix(self) -> np.ndarray:
        """Return as 4x4 transformation matrix."""
        T = np.eye(4, dtype=np.float32)
        T[:3, :3] = self.rotation
        T[:3, 3] = self.position
        return T


class PerspectiveCorrector:
    """Corrects label perspective using homography.
    
    Detects wine label in image, computes homography transformation
    that "flattens" the label to frontal view. This perspective-corrected
    label texture can then be applied to the 3D bottle model to match
    the original photo's lighting and angle.
    """
    
    @staticmethod
    def detect_label_quadrilateral(image: np.ndarray, label_mask: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
        """Detect wine label as a quadrilateral (4 corner points).
        
        Uses contour detection to find label boundary, fits a rotated rectangle,
        and extracts 4 corner points.
        
        Args:
            image: Input image (BGR)
            label_mask: Optional pre-computed binary mask of label region
            
        Returns:
            Array of 4 corner points (x,y) or None if detection failed
        """
        if label_mask is None:
            # Convert to HSV and create mask for label colors
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            # Common label color ranges
            lower_label = np.array([0, 30, 50])
            upper_label = np.array([180, 200, 255])
            label_mask = cv2.inRange(hsv, lower_label, upper_label)
        
        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        label_mask = cv2.morphologyEx(label_mask, cv2.MORPH_CLOSE, kernel)
        label_mask = cv2.morphologyEx(label_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(label_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        
        # Get largest contour
        largest = max(contours, key=cv2.contourArea)
        
        # Fit rotated rectangle
        rect = cv2.minAreaRect(largest)
        box = cv2.boxPoints(rect)
        box = np.int32(box)
        
        return np.float32(box)
    
    @staticmethod
    def compute_homography(src_corners: np.ndarray, dst_size: Tuple[int, int] = (512, 256)) -> Tuple[np.ndarray, np.ndarray]:
        """Compute homography from perspective label to frontal view.
        
        Args:
            src_corners: 4 corner points of label in image
            dst_size: Output texture dimensions (width, height)
            
        Returns:
            Tuple of (homography matrix, warped image mask)
        """
        # Destination is a perfect rectangle
        dst_corners = np.float32([
            [0, 0],
            [dst_size[0], 0],
            [dst_size[0], dst_size[1]],
            [0, dst_size[1]]
        ])
        
        # Compute homography
        H, _ = cv2.findHomography(src_corners, dst_corners)
        return H, dst_corners
    
    @staticmethod
    def warp_label_perspective(image: np.ndarray, corners: np.ndarray, dst_size: Tuple[int, int] = (512, 256)) -> np.ndarray:
        """Warp label from perspective to frontal view.
        
        Args:
            image: Input image
            corners: 4 corner points of label
            dst_size: Output texture resolution
            
        Returns:
            Warped (flattened) label texture
        """
        H, _ = PerspectiveCorrector.compute_homography(corners, dst_size)
        warped = cv2.warpPerspective(image, H, dst_size)
        return warped
    
    @staticmethod
    def estimate_camera_pose_from_label(
        image_corners: np.ndarray,
        intrinsics: CameraIntrinsics,
        bottle_3d_corners: Optional[np.ndarray] = None,
        bottle_height_mm: float = 750.0
    ) -> CameraPose:
        """Estimate camera pose relative to bottle using detected label corners.
        
        Uses PnP (Perspective-n-Point) algorithm to estimate camera position/rotation
        from 2D image points and known 3D bottle model points.
        
        Args:
            image_corners: 2D label corners in image (4 points)
            intrinsics: Camera intrinsic parameters
            bottle_3d_corners: Known 3D coordinates of bottle label corners. If None, uses default.
            bottle_height_mm: Bottle height in mm (for scaling 3D model)
            
        Returns:
            CameraPose with camera position, rotation, and quaternion
        """
        # Default 3D label corner positions on parametric bottle model
        if bottle_3d_corners is None:
            # Assuming label is on front of bottle, normalized coords
            scale = bottle_height_mm / 1000.0  # Convert mm to scene units
            bottle_3d_corners = np.float32([
                [-0.5*scale, 0.2*scale, 0.35*scale],  # Top-left
                [0.5*scale, 0.2*scale, 0.35*scale],   # Top-right
                [0.5*scale, 0.2*scale, 0.6*scale],    # Bottom-right
                [-0.5*scale, 0.2*scale, 0.6*scale],   # Bottom-left
            ])
        
        K = intrinsics.to_matrix()
        
        # PnP to get rotation and translation
        success, rvec, tvec = cv2.solvePnP(
            bottle_3d_corners,
            image_corners,
            K,
            distCoeffs=np.zeros(4),
            useExtrinsicGuess=False,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            # Return default pose if estimation fails
            return CameraPose(
                position=(0, 0, 1.5),
                rotation=np.eye(3, dtype=np.float32),
                quaternion=(0, 0, 0, 1)
            )
        
        # Convert rotation vector to rotation matrix
        R, _ = cv2.Rodrigues(rvec)
        
        # Camera position: -R.T @ t
        position = tuple(-R.T @ tvec.flatten())
        
        # Convert rotation matrix to quaternion
        quat = PerspectiveCorrector._rotation_matrix_to_quaternion(R)
        
        return CameraPose(
            position=position,
            rotation=R,
            quaternion=quat
        )
    
    @staticmethod
    def _rotation_matrix_to_quaternion(R: np.ndarray) -> Tuple[float, float, float, float]:
        """Convert 3x3 rotation matrix to quaternion (x, y, z, w)."""
        trace = np.trace(R)
        
        if trace > 0:
            s = 0.5 / np.sqrt(trace + 1.0)
            w = 0.25 / s
            x = (R[2, 1] - R[1, 2]) * s
            y = (R[0, 2] - R[2, 0]) * s
            z = (R[1, 0] - R[0, 1]) * s
        elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            w = (R[2, 1] - R[1, 2]) / s
            x = 0.25 * s
            y = (R[0, 1] + R[1, 0]) / s
            z = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            w = (R[0, 2] - R[2, 0]) / s
            x = (R[0, 1] + R[1, 0]) / s
            y = 0.25 * s
            z = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            w = (R[1, 0] - R[0, 1]) / s
            x = (R[0, 2] + R[2, 0]) / s
            y = (R[1, 2] + R[2, 1]) / s
            z = 0.25 * s
        
        return (x, y, z, w)
    
    @staticmethod
    def create_intrinsics_from_image(
        image_width: int,
        image_height: int,
        fov_degrees: float = 50.0
    ) -> CameraIntrinsics:
        """Create camera intrinsics assuming a standard mobile camera.
        
        Args:
            image_width: Image width in pixels
            image_height: Image height in pixels
            fov_degrees: Field of view in degrees (typical: 50-70 for mobile)
            
        Returns:
            CameraIntrinsics object
        """
        # Estimate focal length from FOV
        fov_rad = np.radians(fov_degrees)
        f = (image_width / 2.0) / np.tan(fov_rad / 2.0)
        
        return CameraIntrinsics(
            fx=f,
            fy=f,
            cx=image_width / 2.0,
            cy=image_height / 2.0,
            width=image_width,
            height=image_height
        )


class LabelTextureEnhancer:
    """Enhances perspective-corrected label texture for realism."""
    
    @staticmethod
    def enhance_with_specular_highlights(
        texture: np.ndarray,
        light_direction: Tuple[float, float, float] = (0.5, 0.5, 1.0)
    ) -> np.ndarray:
        """Add specular highlights to match lighting in original image.
        
        Args:
            texture: Corrected label texture
            light_direction: Normalized light direction vector
            
        Returns:
            Enhanced texture with subtle highlights
        """
        # Convert to LAB for better contrast control
        lab = cv2.cvtColor(texture, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)
        
        # Create highlight map based on light direction and surface normals
        h, w = texture.shape[:2]
        y, x = np.mgrid[0:h, 0:w]
        
        # Simple radial falloff for highlights (assume center is highest)
        center_y, center_x = h / 2, w / 2
        dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        highlight_mask = np.exp(-dist / (max_dist * 0.5))
        
        # Apply highlight to luminance
        highlight_strength = 15
        l_channel = np.clip(l_channel.astype(np.float32) + highlight_mask * highlight_strength, 0, 255)
        l_channel = l_channel.astype(np.uint8)
        
        lab = cv2.merge([l_channel, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    @staticmethod
    def apply_color_correction(
        texture: np.ndarray,
        reference_image: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Apply color correction to match original image lighting.
        
        Args:
            texture: Corrected label texture
            reference_image: Original image (for color statistics)
            
        Returns:
            Color-corrected texture
        """
        if reference_image is None:
            return texture
        
        # Compute color statistics
        ref_mean = cv2.mean(reference_image)[:3]
        tex_mean = cv2.mean(texture)[:3]
        
        # Simple color correction: scale each channel
        corrected = texture.copy().astype(np.float32)
        for i in range(3):
            if tex_mean[i] > 0:
                corrected[:, :, i] *= ref_mean[i] / tex_mean[i]
        
        return np.clip(corrected, 0, 255).astype(np.uint8)
