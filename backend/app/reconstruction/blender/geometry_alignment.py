"""Geometry alignment contracts for perspective and depth fit."""


class GeometryAlignment:
    def align(self, mesh_uri: str, depth_map_uri: str | None = None) -> dict:
        return {"mesh_uri": mesh_uri, "depth_map_uri": depth_map_uri, "aligned": True}
