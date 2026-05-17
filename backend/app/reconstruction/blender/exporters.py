"""Blender export contracts for GLB and USDZ artifacts."""


class BlenderExporters:
    def export_glb(self, mesh_uri: str) -> dict:
        return {"mesh_uri": mesh_uri, "format": "glb", "ok": True}

    def export_usdz(self, mesh_uri: str) -> dict:
        return {"mesh_uri": mesh_uri, "format": "usdz", "ok": True}
