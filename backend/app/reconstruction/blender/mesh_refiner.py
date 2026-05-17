"""Mesh refinement contracts for Blender worker."""


class MeshRefiner:
    def refine(self, mesh_uri: str) -> dict:
        return {
            "mesh_uri": mesh_uri,
            "operations": ["subdivision", "smoothing", "shrinkwrap", "solidify"],
        }
