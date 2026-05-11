"""Tests for the 3D Reconstruction service and endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas_3d import ReconstructionRequest, MeshOptimizationRequest
from backend.app.services.reconstruction_service import ReconstructionService


client = TestClient(app)


class TestReconstructionService:
    """Test the reconstruction service layer."""

    @pytest.fixture
    def reconstruction_service(self):
        """Create reconstruction service instance."""
        return ReconstructionService()

    def test_reconstruct_from_images(self, reconstruction_service):
        """Test 3D reconstruction from images via service."""
        request = ReconstructionRequest(
            image_urls=["https://example.com/angle1.jpg", "https://example.com/angle2.jpg"],
            object_type="wine_bottle",
            quality="medium",
        )
        result = reconstruction_service.reconstruct_from_images(request)
        
        assert result.reconstruction_id is not None
        assert result.mesh is not None
        assert len(result.mesh.vertices) > 0
        assert len(result.mesh.faces) > 0
        assert 0 <= result.confidence_score <= 1

    def test_get_reconstruction_status(self, reconstruction_service):
        """Test getting reconstruction status via service."""
        status = reconstruction_service.get_reconstruction_status("test-id-123")
        
        assert status.reconstruction_id == "test-id-123"
        assert status.status == "completed"
        assert status.progress_percent == 100

    def test_compare_reconstructions(self, reconstruction_service):
        """Test comparing two reconstructions via service."""
        comparison = reconstruction_service.compare_reconstructions("id-1", "id-2")
        
        assert comparison.reconstruction_id_1 == "id-1"
        assert comparison.reconstruction_id_2 == "id-2"
        assert 0 <= comparison.similarity_score <= 1

    def test_get_bounding_box(self, reconstruction_service):
        """Test getting bounding box via service."""
        bbox = reconstruction_service.get_bounding_box("test-id")
        
        assert bbox.min_point is not None
        assert bbox.max_point is not None
        assert bbox.volume > 0

    def test_optimize_mesh(self, reconstruction_service):
        """Test mesh optimization via service."""
        request = MeshOptimizationRequest(
            reconstruction_id="test-id",
            target_vertex_count=10000,
            preserve_features=True,
        )
        result = reconstruction_service.optimize_mesh(request)
        
        assert result.original_vertex_count > 0
        assert result.optimized_vertex_count == request.target_vertex_count
        assert 0 <= result.quality_loss_percent <= 100

    def test_export_reconstruction(self, reconstruction_service):
        """Test exporting reconstruction via service."""
        export = reconstruction_service.export_reconstruction("test-id", "gltf")
        
        assert "download_url" in export
        assert "file_size_mb" in export
        assert export["format"] == "gltf"

    def test_batch_reconstruct(self, reconstruction_service):
        """Test batch reconstruction via service."""
        requests = [
            ReconstructionRequest(
                image_urls=["url1.jpg", "url2.jpg"],
                object_type="wine_bottle",
                quality="high",
            ),
            ReconstructionRequest(
                image_urls=["url3.jpg", "url4.jpg"],
                object_type="wine_bottle",
                quality="medium",
            ),
        ]
        results = reconstruction_service.batch_reconstruct(requests)
        
        assert len(results) == 2
        assert all(r.reconstruction_id is not None for r in results)


class TestReconstructionEndpoints:
    """Test the 3D Reconstruction API endpoints."""

    def test_reconstruct_endpoint(self):
        """Test POST /api/v1/3d/reconstruct."""
        response = client.post(
            "/api/v1/3d/reconstruct",
            json={
                "image_urls": ["https://example.com/angle1.jpg", "https://example.com/angle2.jpg"],
                "object_type": "wine_bottle",
                "quality": "high",
            },
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "reconstruction_id" in data
            assert "mesh" in data

    def test_get_status_endpoint(self):
        """Test GET /api/v1/3d/status/{id}."""
        response = client.get("/api/v1/3d/status/test-reconstruction-id")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "progress_percent" in data

    def test_compare_reconstructions_endpoint(self):
        """Test GET /api/v1/3d/compare/{id1}/{id2}."""
        response = client.get("/api/v1/3d/compare/id-1/id-2")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "similarity_score" in data

    def test_bounding_box_endpoint(self):
        """Test GET /api/v1/3d/bounding-box/{id}."""
        response = client.get("/api/v1/3d/bounding-box/test-id")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "min_point" in data
            assert "max_point" in data

    def test_optimize_mesh_endpoint(self):
        """Test POST /api/v1/3d/optimize."""
        response = client.post(
            "/api/v1/3d/optimize",
            json={
                "reconstruction_id": "test-id",
                "target_vertex_count": 10000,
                "preserve_features": True,
            },
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "optimized_vertex_count" in data

    def test_export_endpoint(self):
        """Test GET /api/v1/3d/export/{id}."""
        response = client.get("/api/v1/3d/export/test-id?format=gltf")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "download_url" in data

    def test_batch_reconstruct_endpoint(self):
        """Test POST /api/v1/3d/batch-reconstruct."""
        response = client.post(
            "/api/v1/3d/batch-reconstruct",
            json=[
                {
                    "image_urls": ["url1.jpg", "url2.jpg"],
                    "object_type": "wine_bottle",
                    "quality": "high",
                },
                {
                    "image_urls": ["url3.jpg", "url4.jpg"],
                    "object_type": "wine_bottle",
                    "quality": "medium",
                },
            ],
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_health_check_endpoint(self):
        """Test GET /api/v1/3d/status (health check)."""
        response = client.get("/api/v1/3d/status")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "3d"
        assert data["status"] == "operational"
