"""PBR material build interface for Blender worker."""


class MaterialBuilder:
    def build(self, mesh_uri: str) -> dict:
        return {
            "mesh_uri": mesh_uri,
            "maps": ["albedo", "roughness", "metallic", "normal", "ao", "opacity"],
        }
