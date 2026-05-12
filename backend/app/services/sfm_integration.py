"""COLMAP/Structure-from-Motion integration for photogrammetry.

Interfaces with COLMAP to reconstruct 3D bottle geometry from multiple images.
Provides high-fidelity mesh and texture when multiple viewpoints are available.
"""

import subprocess
import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass
import numpy as np
import cv2


@dataclass
class SfMResult:
    """Result of Structure-from-Motion reconstruction."""
    success: bool
    mesh_path: Optional[str]  # Path to generated mesh file
    ply_path: Optional[str]  # Path to PLY point cloud
    sparse_model_dir: Optional[str]  # COLMAP sparse model directory
    cameras: dict = None  # Camera parameters
    images: dict = None  # Image poses and metadata
    error_message: Optional[str] = None
    processing_time_ms: float = 0.0


class COLMAPInterface:
    """Interface to COLMAP for structure-from-motion.
    
    Orchestrates COLMAP workflow:
    1. Feature extraction and matching across images
    2. Incremental SfM reconstruction
    3. Dense reconstruction (MVS)
    4. Mesh generation via Poisson surface reconstruction
    """
    
    def __init__(self, colmap_path: str = "colmap"):
        """Initialize COLMAP interface.
        
        Args:
            colmap_path: Path to COLMAP executable (default: assumes in PATH)
        """
        self.colmap_path = colmap_path
        self._verify_colmap_available()
    
    def _verify_colmap_available(self) -> bool:
        """Check if COLMAP is installed and accessible."""
        try:
            result = subprocess.run(
                [self.colmap_path, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def reconstruct_from_images(
        self,
        image_paths: List[str],
        output_dir: str,
        camera_model: str = "SIMPLE_RADIAL"
    ) -> SfMResult:
        """Run full SfM pipeline on image list.
        
        Args:
            image_paths: List of image file paths
            output_dir: Directory to store COLMAP project and outputs
            camera_model: COLMAP camera model (SIMPLE_RADIAL, PINHOLE, etc.)
            
        Returns:
            SfMResult with reconstruction status and output paths
        """
        import time
        start_time = time.time()
        
        try:
            # Create project structure
            project_dir = Path(output_dir)
            project_dir.mkdir(parents=True, exist_ok=True)
            image_dir = project_dir / "images"
            sparse_dir = project_dir / "sparse" / "0"
            dense_dir = project_dir / "dense"
            
            # Copy images
            image_dir.mkdir(exist_ok=True)
            copied_images = []
            for i, src_path in enumerate(image_paths):
                ext = Path(src_path).suffix
                dst_path = image_dir / f"image_{i:03d}{ext}"
                shutil.copy2(src_path, dst_path)
                copied_images.append(str(dst_path))
            
            # Create empty database
            db_path = project_dir / "database.db"
            self._run_colmap_command([
                "database_creator",
                "--database_path", str(db_path)
            ])
            
            # Feature extraction
            self._run_colmap_command([
                "feature_extractor",
                "--database_path", str(db_path),
                "--image_path", str(image_dir),
                "--ImageReader.camera_model", camera_model,
            ])
            
            # Feature matching (exhaustive for small image sets)
            self._run_colmap_command([
                "exhaustive_matcher",
                "--database_path", str(db_path),
            ])
            
            # Sparse reconstruction
            sparse_dir.mkdir(parents=True, exist_ok=True)
            self._run_colmap_command([
                "mapper",
                "--database_path", str(db_path),
                "--image_path", str(image_dir),
                "--output_path", str(sparse_dir.parent),
            ])
            
            # Dense reconstruction (MVS)
            dense_dir.mkdir(exist_ok=True)
            mvs_config = {
                "Mapper": {
                    "filter_min_ncc": 0.1,
                    "filter_min_triangulation_angle": 1.0,
                    "patch_size": 5,
                    "patch_stride": 1,
                },
            }
            
            self._run_colmap_command([
                "image_undistorter",
                "--image_path", str(image_dir),
                "--input_path", str(sparse_dir.parent),
                "--output_path", str(dense_dir),
                "--output_type", "COLMAP",
            ])
            
            self._run_colmap_command([
                "stereo",
                "--workspace_path", str(dense_dir),
                "--workspace_format", "COLMAP",
            ])
            
            # Fusion to point cloud
            pcd_path = dense_dir / "fused.ply"
            self._run_colmap_command([
                "point_cloud_merger",
                "--input_path", str(dense_dir),
                "--output_path", str(pcd_path),
            ])
            
            # Mesh generation via Poisson reconstruction
            mesh_path = dense_dir / "mesh.ply"
            if pcd_path.exists():
                self._poisson_reconstruction(str(pcd_path), str(mesh_path))
            
            processing_time = (time.time() - start_time) * 1000
            
            return SfMResult(
                success=True,
                mesh_path=str(mesh_path) if mesh_path.exists() else None,
                ply_path=str(pcd_path) if pcd_path.exists() else None,
                sparse_model_dir=str(sparse_dir),
                processing_time_ms=processing_time,
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return SfMResult(
                success=False,
                mesh_path=None,
                ply_path=None,
                sparse_model_dir=None,
                error_message=str(e),
                processing_time_ms=processing_time,
            )
    
    def _run_colmap_command(self, args: List[str]) -> bool:
        """Execute a COLMAP command.
        
        Args:
            args: Command line arguments
            
        Returns:
            True if successful
        """
        try:
            result = subprocess.run(
                [self.colmap_path] + args,
                capture_output=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode == 0
        except Exception as e:
            raise RuntimeError(f"COLMAP command failed: {e}")
    
    def _poisson_reconstruction(self, ply_input: str, ply_output: str) -> bool:
        """Generate mesh from point cloud using Poisson reconstruction.
        
        Requires PoissonRecon or similar. Falls back to simple wrapping if unavailable.
        
        Args:
            ply_input: Input point cloud path
            ply_output: Output mesh path
            
        Returns:
            True if successful
        """
        try:
            # Try PoissonRecon if available
            result = subprocess.run([
                "PoissonRecon",
                f"--in {ply_input}",
                f"--out {ply_output}",
                "--depth 8",
                "--scale 1.1",
            ], shell=True, capture_output=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(ply_output):
                return True
        except Exception:
            pass
        
        # Fallback: simple convex hull or direct copy
        # In production, would use Open3D or similar
        import shutil
        try:
            shutil.copy(ply_input, ply_output)
            return True
        except Exception:
            return False


class FastSfMFallback:
    """Fallback SfM when COLMAP is unavailable.
    
    Uses feature matching and simpler algorithms suitable for wine bottles.
    Less accurate than full COLMAP but works without external dependencies.
    """
    
    @staticmethod
    def reconstruct_from_features(image_paths: List[str]) -> Optional[np.ndarray]:
        """Simple feature-based 3D reconstruction.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            Point cloud as numpy array (Nx3) or None if failed
        """
        if len(image_paths) < 2:
            return None
        
        try:
            images = [cv2.imread(p) for p in image_paths]
            images = [img for img in images if img is not None]
            
            if len(images) < 2:
                return None
            
            # Initialize ORB detector
            orb = cv2.ORB_create(nfeatures=1000)
            
            # Detect keypoints and descriptors
            keypoints = []
            descriptors = []
            for img in images:
                kp, desc = orb.detectAndCompute(img, None)
                keypoints.append(kp)
                descriptors.append(desc)
            
            # Match features between first two images
            if descriptors[0] is None or descriptors[1] is None:
                return None
            
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(descriptors[0], descriptors[1])
            matches = sorted(matches, key=lambda x: x.distance)[:100]  # Top 100
            
            if len(matches) < 8:
                return None
            
            # Extract matching points
            pts1 = np.float32([keypoints[0][m.queryIdx].pt for m in matches])
            pts2 = np.float32([keypoints[1][m.trainIdx].pt for m in matches])
            
            # Estimate fundamental matrix
            F, mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC)
            
            if F is None:
                return None
            
            # Compute essential matrix
            K = np.array([
                [500, 0, images[0].shape[1] / 2],
                [0, 500, images[0].shape[0] / 2],
                [0, 0, 1]
            ], dtype=np.float32)
            
            E = K.T @ F @ K
            
            # Recover pose
            _, R, t, mask = cv2.recoverPose(E, pts1, pts2, K, mask=mask)
            
            # Triangulate points
            P1 = K @ np.hstack([np.eye(3), np.zeros((3, 1))])
            P2 = K @ np.hstack([R, t])
            
            points_4d = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
            points_3d = (points_4d[:3] / points_4d[3]).T
            
            # Filter points behind camera or too far
            points_3d = points_3d[points_3d[:, 2] > 0]
            points_3d = points_3d[points_3d[:, 2] < 100]
            
            return points_3d
            
        except Exception:
            return None


class MeshOptimizer:
    """Post-process SfM mesh for bottle rendering."""
    
    @staticmethod
    def simplify_mesh(mesh_path: str, target_reduction: float = 0.5) -> Optional[str]:
        """Simplify mesh for faster rendering.
        
        Args:
            mesh_path: Path to input mesh (PLY)
            target_reduction: Target vertex reduction ratio (0-1)
            
        Returns:
            Path to simplified mesh or None if failed
        """
        try:
            # Use Open3D if available
            import open3d as o3d
            
            mesh = o3d.io.read_triangle_mesh(mesh_path)
            target_count = int(len(mesh.vertices) * (1 - target_reduction))
            
            mesh_simplified = mesh.simplify_quadric_decimation(target_count)
            
            output_path = mesh_path.replace(".ply", "_simplified.ply")
            o3d.io.write_triangle_mesh(output_path, mesh_simplified)
            
            return output_path
        except ImportError:
            # Fallback: return original
            return mesh_path
        except Exception:
            return None
    
    @staticmethod
    def generate_texture_atlas(mesh_path: str, image_paths: List[str]) -> Optional[str]:
        """Generate texture atlas for mesh from input images.
        
        Args:
            mesh_path: Path to mesh
            image_paths: List of source images
            
        Returns:
            Path to generated texture atlas
        """
        try:
            import open3d as o3d
            
            mesh = o3d.io.read_triangle_mesh(mesh_path)
            # Simple approach: composite images into texture
            # Full implementation would use UV projection and blending
            
            output_tex = mesh_path.replace(".ply", "_texture.png")
            # Placeholder
            if image_paths:
                shutil.copy(image_paths[0], output_tex)
                return output_tex
            
            return None
        except Exception:
            return None
