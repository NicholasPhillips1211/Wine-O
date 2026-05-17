"""Scene construction contracts for bottle refinement."""


class SceneBuilder:
    def build(self, scaffold_uri: str) -> dict:
        return {"scene": "built", "scaffold_uri": scaffold_uri}
