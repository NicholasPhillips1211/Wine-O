"""Glass shader abstraction used by Blender material workflows."""


class GlassShader:
    def build(self, tint: str = "neutral") -> dict:
        return {"shader": "glass", "features": ["fresnel", "refraction", "reflection"], "tint": tint}
