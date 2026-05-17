"""Texture baking interface for mobile-ready outputs."""


class TextureBaker:
    def bake(self, mesh_uri: str) -> dict:
        return {"mesh_uri": mesh_uri, "baked": True, "texture_profile": "mobile"}
