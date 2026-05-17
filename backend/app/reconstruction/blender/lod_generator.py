"""LOD generation contracts for runtime optimization."""


class LODGenerator:
    def generate(self, mesh_uri: str) -> dict:
        return {
            "mesh_uri": mesh_uri,
            "lods": ["LOD0", "LOD1", "LOD2", "thumbnail"],
        }
