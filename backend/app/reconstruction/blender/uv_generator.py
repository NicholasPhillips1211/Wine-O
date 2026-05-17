"""UV generation interface for bottle assets."""


class UVGenerator:
    def generate(self, mesh_uri: str) -> dict:
        return {"mesh_uri": mesh_uri, "unwrap": "cylindrical", "atlas_packed": True}
