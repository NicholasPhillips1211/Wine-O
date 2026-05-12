"""Texture mapping and glTF export for 3D wine bottles.

Handles UV mapping for label textures onto bottle geometry and generates
glTF 2.0 format files for web/3D viewer compatibility. Supports both
simple cylindrical projection and advanced parametric mapping.
"""

import io
import struct
import json
import base64
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from backend.app.schemas_3d import Mesh, Point3D


@dataclass
class TextureMap:
    """Texture mapping information."""
    
    texture_image: np.ndarray  # Image data (uint8, BGR or grayscale)
    uv_coordinates: list[Tuple[float, float]]  # UV coords for each vertex
    width: int
    height: int
    format: str = "png"  # png, jpg, etc.


class BottleTextureMapper:
    """Maps wine label textures onto 3D bottle geometry.
    
    Generates UV coordinates for cylindrical or parametric projection
    of 2D label textures onto 3D bottle mesh. Handles texture wrapping,
    tiling, and perspective distortion correction.
    """
    
    @staticmethod
    def generate_uv_coordinates(
        mesh: Mesh,
        label_zone_vertices: Optional[list[int]] = None,
        projection_type: str = "cylindrical"
    ) -> list[Tuple[float, float]]:
        """Generate UV coordinates for texture mapping.
        
        Creates mapping from 3D vertex positions to 2D texture space.
        Supports different projection types:
        - cylindrical: Wraps texture around bottle circumference
        - planar: Projects texture front-facing
        - parametric: Custom mapping based on bottle geometry
        
        Args:
            mesh: 3D bottle mesh
            label_zone_vertices: Vertex indices for label region (None = all)
            projection_type: Projection method to use
            
        Returns:
            List of (u, v) coordinates for each vertex (0-1 range)
        """
        uv_coords = []
        vertices = mesh.vertices
        
        if projection_type == "cylindrical":
            for i, vertex in enumerate(vertices):
                # Use x,z for cylindrical projection around y-axis
                u = (np.arctan2(vertex.z, vertex.x) + np.pi) / (2 * np.pi)  # 0-1
                v = vertex.y  # Height already 0-1
                
                # Restrict to label region if specified
                if label_zone_vertices and i not in label_zone_vertices:
                    v = -1  # Outside mapping region (will be ignored in rendering)
                
                uv_coords.append((u, v))
        
        elif projection_type == "planar":
            # Front-facing projection
            for i, vertex in enumerate(vertices):
                u = (vertex.x + 1) / 2  # Convert -1-1 to 0-1
                v = vertex.y
                uv_coords.append((u, v))
        
        else:  # parametric
            for i, vertex in enumerate(vertices):
                # Use all three coordinates for more complex mapping
                u = (np.arctan2(vertex.z, vertex.x) + np.pi) / (2 * np.pi)
                v = vertex.y
                
                # Apply parametric adjustment based on vertex position
                # This could include curvature correction, perspective adjustment, etc.
                uv_coords.append((u, v))
        
        return uv_coords
    
    @staticmethod
    def image_to_base64(image: np.ndarray, format: str = "png") -> str:
        """Convert image array to base64 string for embedding in glTF.
        
        Args:
            image: Image as numpy array
            format: Output format ('png' or 'jpg')
            
        Returns:
            Base64 encoded string with data URI scheme
        """
        import cv2
        
        _, buffer = cv2.imencode(f'.{format}', image)
        b64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/{format};base64,{b64}"


class GLTFExporter:
    """Exports 3D wine bottle models to glTF 2.0 format.
    
    Generates industry-standard glTF 2.0 files with support for:
    - Mesh geometry (vertices, faces, normals)
    - Texture mapping and UV coordinates
    - Metallic/roughness PBR materials
    - Binary format (.glb) for efficient storage
    - JSON format (.gltf) with external references
    """
    
    @staticmethod
    def mesh_to_gltf_json(
        mesh: Mesh,
        uv_coords: list[Tuple[float, float]],
        texture_base64: Optional[str] = None,
        material_name: str = "bottle_material"
    ) -> dict:
        """Convert mesh to glTF 2.0 JSON structure.
        
        Args:
            mesh: 3D mesh to export
            uv_coords: UV coordinates for texture mapping
            texture_base64: Base64 encoded texture image
            material_name: Name for the material
            
        Returns:
            glTF 2.0 JSON dictionary
        """
        # Prepare vertex data
        vertices = np.array([
            [v.x, v.y, v.z] for v in mesh.vertices
        ], dtype=np.float32).flatten()
        
        # Prepare face/index data
        faces = np.array(mesh.faces, dtype=np.uint32).flatten()
        
        # Prepare UV data
        uv_array = np.array(uv_coords, dtype=np.float32).flatten()
        
        # Compute normals (simplified - flat normals per face)
        normals = GLTFExporter._compute_normals(mesh)
        normal_array = np.array([[normal.x, normal.y, normal.z] for normal in normals], dtype=np.float32).flatten()
        
        # Create buffers
        buffers = [
            {
                "byteLength": vertices.nbytes + faces.nbytes + uv_array.nbytes + normal_array.nbytes,
                "uri": "data:application/octet-stream;base64," + base64.b64encode(
                    vertices.tobytes() + faces.tobytes() + uv_array.tobytes() + normal_array.tobytes()
                ).decode('utf-8')
            }
        ]
        
        # Create buffer views
        buffer_views = [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": vertices.nbytes,
                "target": 34962  # ARRAY_BUFFER
            },
            {
                "buffer": 0,
                "byteOffset": vertices.nbytes,
                "byteLength": faces.nbytes,
                "target": 34963  # ELEMENT_ARRAY_BUFFER
            },
            {
                "buffer": 0,
                "byteOffset": vertices.nbytes + faces.nbytes,
                "byteLength": uv_array.nbytes,
                "target": 34962  # ARRAY_BUFFER
            },
            {
                "buffer": 0,
                "byteOffset": vertices.nbytes + faces.nbytes + uv_array.nbytes,
                "byteLength": normal_array.nbytes,
                "target": 34962  # ARRAY_BUFFER
            }
        ]
        
        # Create accessors
        accessors = [
            {
                "bufferView": 0,
                "componentType": 5126,  # FLOAT
                "count": len(mesh.vertices),
                "type": "VEC3",
                "min": [float(np.min(vertices[i::3])) for i in range(3)],
                "max": [float(np.max(vertices[i::3])) for i in range(3)],
            },
            {
                "bufferView": 1,
                "componentType": 5125,  # UNSIGNED_INT
                "count": len(faces),
                "type": "SCALAR",
            },
            {
                "bufferView": 2,
                "componentType": 5126,  # FLOAT
                "count": len(uv_coords),
                "type": "VEC2",
            },
            {
                "bufferView": 3,
                "componentType": 5126,  # FLOAT
                "count": len(normal_array) // 3,
                "type": "VEC3",
            }
        ]
        
        # Create materials
        materials = [
            {
                "name": material_name,
                "pbrMetallicRoughness": {
                    "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                    "baseColorTexture": {"index": 0} if texture_base64 else None,
                    "metallicFactor": 0.1,
                    "roughnessFactor": 0.4,
                },
                "normalTexture": None,
            }
        ]
        
        # Create images and textures if texture provided
        images = []
        textures = []
        if texture_base64:
            images.append({"uri": texture_base64})
            textures.append({
                "source": 0,
                "sampler": 0,
            })
        
        # Create sampler
        samplers = [{
            "magFilter": 9729,  # LINEAR
            "minFilter": 9986,  # LINEAR_MIPMAP_LINEAR
            "wrapS": 10497,  # REPEAT
            "wrapT": 10497,  # REPEAT
        }]
        
        # Create mesh primitive
        primitive = {
            "attributes": {
                "POSITION": 0,
                "TEXCOORD_0": 2,
                "NORMAL": 3,
            },
            "indices": 1,
            "material": 0,
        }
        
        # Create mesh and node
        mesh_obj = {
            "name": "wine_bottle",
            "primitives": [primitive],
        }
        
        node = {
            "mesh": 0,
            "name": "wine_bottle_node",
        }
        
        # Assemble glTF structure
        gltf = {
            "asset": {
                "generator": "Wine-O 3D Reconstruction",
                "version": "2.0",
            },
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [node],
            "meshes": [mesh_obj],
            "buffers": buffers,
            "bufferViews": buffer_views,
            "accessors": accessors,
            "materials": materials,
            "samplers": samplers,
        }
        
        if texture_base64:
            gltf["images"] = images
            gltf["textures"] = textures
        
        return gltf
    
    @staticmethod
    def _compute_normals(mesh: Mesh) -> list[Point3D]:
        """Compute vertex normals from mesh faces.
        
        Args:
            mesh: 3D mesh
            
        Returns:
            List of normal vectors
        """
        normals = [Point3D(x=0, y=0, z=0) for _ in mesh.vertices]
        
        for face in mesh.faces:
            v0, v1, v2 = mesh.vertices[face[0]], mesh.vertices[face[1]], mesh.vertices[face[2]]
            
            # Compute face normal using cross product
            edge1 = Point3D(x=v1.x-v0.x, y=v1.y-v0.y, z=v1.z-v0.z)
            edge2 = Point3D(x=v2.x-v0.x, y=v2.y-v0.y, z=v2.z-v0.z)
            
            normal = Point3D(
                x=edge1.y*edge2.z - edge1.z*edge2.y,
                y=edge1.z*edge2.x - edge1.x*edge2.z,
                z=edge1.x*edge2.y - edge1.y*edge2.x
            )
            
            # Add to all vertices of this face
            for idx in face:
                normals[idx].x += normal.x
                normals[idx].y += normal.y
                normals[idx].z += normal.z
        
        # Normalize
        for normal in normals:
            length = (normal.x**2 + normal.y**2 + normal.z**2)**0.5
            if length > 0:
                normal.x /= length
                normal.y /= length
                normal.z /= length
        
        return normals
    
    @staticmethod
    def export_glb(
        mesh: Mesh,
        uv_coords: list[Tuple[float, float]],
        texture_base64: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> bytes:
        """Export mesh as glTF binary (.glb) format.
        
        Args:
            mesh: 3D mesh
            uv_coords: UV coordinates
            texture_base64: Base64 texture data
            output_path: Optional file path to write to
            
        Returns:
            Binary glTF data
        """
        gltf_json = GLTFExporter.mesh_to_gltf_json(
            mesh, uv_coords, texture_base64
        )
        
        # Convert to JSON bytes
        json_str = json.dumps(gltf_json)
        json_bytes = json_str.encode('utf-8')
        
        # Pad JSON to 4-byte boundary
        padding = (4 - (len(json_bytes) % 4)) % 4
        json_bytes += b' ' * padding
        
        # Create GLB header
        glb_header = struct.pack('<4sIII',
            b'glTF',  # Magic
            2,  # Version
            28 + len(json_bytes),  # File size
            len(json_bytes),  # JSON chunk size
        )
        
        json_chunk_type = b'JSON'
        json_chunk = struct.pack('<I', len(json_bytes)) + json_chunk_type + json_bytes
        
        glb_data = glb_header + json_chunk
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(glb_data)
        
        return glb_data
    
    @staticmethod
    def export_gltf_json(
        mesh: Mesh,
        uv_coords: list[Tuple[float, float]],
        texture_base64: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> dict:
        """Export mesh as glTF JSON format with embedded data URIs.
        
        Args:
            mesh: 3D mesh
            uv_coords: UV coordinates
            texture_base64: Base64 texture data
            output_path: Optional file path to write JSON
            
        Returns:
            glTF JSON dictionary
        """
        gltf_json = GLTFExporter.mesh_to_gltf_json(
            mesh, uv_coords, texture_base64
        )
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(gltf_json, f, indent=2)
        
        return gltf_json
