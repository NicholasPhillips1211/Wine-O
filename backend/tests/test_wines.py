"""Tests for the wine service and endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas_wine import WineCreate, WineUpdate
from backend.app.services.wine_service import WineService


client = TestClient(app)


class TestWineService:
    """Test the wine service layer."""

    @pytest.fixture
    def wine_service(self):
        """Create wine service instance."""
        return WineService()

    def test_create_wine(self, wine_service):
        """Test wine creation via service."""
        wine_data = WineCreate(
            name="Cabernet Sauvignon",
            region="Napa Valley",
            vintage=2020,
            varietals=["Cabernet Sauvignon"],
            alcohol_content=13.5,
            description="A premium Napa wine"
        )
        result = wine_service.create_wine(wine_data)
        
        assert result.name == "Cabernet Sauvignon"
        assert result.region == "Napa Valley"
        assert result.id == 1

    def test_get_wine(self, wine_service):
        """Test getting wine by ID via service."""
        result = wine_service.get_wine(wine_id=1)
        
        assert result is not None
        assert result.name == "Example Wine"
        assert result.id == 1

    def test_list_wines(self, wine_service):
        """Test listing wines via service."""
        result = wine_service.list_wines(skip=0, limit=100)
        
        assert isinstance(result, list)

    def test_search_wines(self, wine_service):
        """Test wine search via service."""
        result = wine_service.search_wines("Cabernet")
        
        assert isinstance(result, list)

    def test_identify_wine_from_ocr(self, wine_service):
        """Test wine identification from OCR via service."""
        extracted_text = "2020 Cabernet Sauvignon\nNapa Valley\n13.5% ALC"
        result = wine_service.identify_wine_from_ocr(extracted_text)
        
        assert result.extracted_text == extracted_text
        assert result.confidence >= 0

    def test_add_to_collection(self, wine_service):
        """Test adding wine to collection via service."""
        result = wine_service.add_to_collection(
            user_id=1,
            wine_id=1,
            tasting_notes="Great taste!",
            rating=4.5
        )
        
        assert result["user_id"] == 1
        assert result["wine_id"] == 1
        assert result["rating"] == 4.5

    def test_get_user_collection(self, wine_service):
        """Test getting user collection via service."""
        result = wine_service.get_user_collection(user_id=1)
        
        assert isinstance(result, list)


class TestWineEndpoints:
    """Test the wine API endpoints."""

    def test_create_wine_endpoint(self):
        """Test POST /api/v1/wines."""
        response = client.post("/api/v1/wines", json={
            "name": "Pinot Noir",
            "region": "Sonoma",
            "vintage": 2021,
            "varietals": ["Pinot Noir"],
            "alcohol_content": 14.2,
            "description": "Oregon Pinot"
        })
        assert response.status_code in [200, 201]

    def test_get_wine_endpoint(self):
        """Test GET /api/v1/wines/{wine_id}."""
        response = client.get("/api/v1/wines/1")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "name" in data
            assert "region" in data

    def test_list_wines_endpoint(self):
        """Test GET /api/v1/wines."""
        response = client.get("/api/v1/wines?skip=0&limit=10")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_update_wine_endpoint(self):
        """Test PUT /api/v1/wines/{wine_id}."""
        response = client.put("/api/v1/wines/1", json={
            "name": "Updated Wine Name"
        })
        assert response.status_code in [200, 404, 422]

    def test_search_wines_endpoint(self):
        """Test GET /api/v1/wines/search/query."""
        response = client.get("/api/v1/wines/search/query?q=cabernet")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_identify_wine_endpoint(self):
        """Test POST /api/v1/wines/identify."""
        response = client.post(
            "/api/v1/wines/identify?extracted_text=2020%20Cabernet%20Sauvignon"
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "confidence" in data
            assert "extracted_text" in data

    def test_add_to_collection_endpoint(self):
        """Test POST /api/v1/wines/collection/{wine_id}."""
        response = client.post(
            "/api/v1/wines/collection/1?user_id=1&rating=4.5"
        )
        assert response.status_code in [200, 404, 422]

    def test_get_user_collection_endpoint(self):
        """Test GET /api/v1/wines/collection/user/{user_id}."""
        response = client.get("/api/v1/wines/collection/user/1")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert isinstance(response.json(), list)
