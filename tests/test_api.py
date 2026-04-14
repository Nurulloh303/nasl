from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.ai_requests.models import GenerationRequest

User = get_user_model()


class GenerationAPITests(TestCase):
    """Generation API tests."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)
        self.prompt_preview_url = "/api/ai/prompt-preview/"
        self.generation_submit_url = "/api/ai/submit/"
        self.generation_list_url = "/api/ai/my-generations/"

    def test_prompt_preview(self):
        """Test prompt preview endpoint."""
        data = {
            "module": "smart_text",
            "data": {
                "text": "test text",
                "tone": "professional"
            }
        }
        response = self.client.post(self.prompt_preview_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("prompt", response.data)

    def test_prompt_preview_invalid_module(self):
        """Test prompt preview with invalid module."""
        data = {
            "module": "invalid_module",
            "data": {}
        }
        response = self.client.post(self.prompt_preview_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generation_submit(self):
        """Test generation submission."""
        data = {
            "module": "smart_text",
            "data": {
                "text": "test text",
                "tone": "professional"
            }
        }
        response = self.client.post(self.generation_submit_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_generation_list_pagination(self):
        """Test generation list with pagination."""
        # Create 25 generations
        for i in range(25):
            GenerationRequest.objects.create(
                user=self.user,
                module="test",
                provider="mock",
                prompt="test"
            )
        
        response = self.client.get(self.generation_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 20)  # Default page size is 20
        self.assertIsNotNone(response.data["next"])

    def test_generation_list_authentication_required(self):
        """Test that generation list requires authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.generation_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_generation_detail(self):
        """Test generation detail endpoint."""
        gen = GenerationRequest.objects.create(
            user=self.user,
            module="test",
            provider="mock",
            prompt="test"
        )
        response = self.client.get(f"/api/ai/my-generations/{gen.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(gen.id))

    def test_generation_detail_not_found(self):
        """Test generation detail with non-existent ID."""
        response = self.client.get("/api/ai/my-generations/00000000-0000-0000-0000-000000000000/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
