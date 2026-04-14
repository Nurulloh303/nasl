from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.models import Profile
from apps.ai_requests.models import GenerationRequest
from django.utils import timezone

User = get_user_model()


class ProfileTests(TestCase):
    """Profile model tests."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.profile = self.user.profile

    def test_profile_creation(self):
        """Test profile auto-creation on user creation."""
        self.assertIsNotNone(self.profile)
        self.assertEqual(self.profile.plan, Profile.PLAN_FREE)
        self.assertEqual(self.profile.credits, 0)

    def test_can_generate_free_user_first_request(self):
        """Test that free user can make first generation."""
        self.assertTrue(self.profile.can_generate())

    def test_can_generate_free_user_limit_exceeded(self):
        """Test that free user limit is enforced."""
        # Create one completed generation (Free limit is 1)
        GenerationRequest.objects.create(
            user=self.user,
            module="test",
            provider="mock",
            prompt="test",
            status=GenerationRequest.STATUS_COMPLETED
        )
        self.assertFalse(self.profile.can_generate())

    def test_can_generate_pro_user_daily_limit(self):
        """Test pro user daily limit."""
        self.profile.plan = Profile.PLAN_PRO
        self.profile.save()
        
        # Create daily limit number of generations
        for i in range(24):  # PRO_DAILY_LIMIT = 24
            GenerationRequest.objects.create(
                user=self.user,
                module="test",
                provider="mock",
                prompt="test",
                status=GenerationRequest.STATUS_COMPLETED,
                created_at=timezone.now()
            )
        
        self.assertFalse(self.profile.can_generate())

    def test_deduct_credits(self):
        """Test credit deduction."""
        self.profile.credits = 100
        self.profile.save()
        
        result = self.profile.deduct_credits(30)
        self.profile.refresh_from_db()
        
        self.assertTrue(result)
        self.assertEqual(self.profile.credits, 70)

    def test_deduct_credits_insufficient(self):
        """Test credit deduction with insufficient credits."""
        self.profile.credits = 10
        self.profile.save()
        
        result = self.profile.deduct_credits(30)
        self.profile.refresh_from_db()
        
        self.assertFalse(result)
        self.assertEqual(self.profile.credits, 10)
