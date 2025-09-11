from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date, timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Address, UserProfile
from apps.authentication.models import UserSession

User = get_user_model()

class UserAddressTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="user1@example.com",
            password="testpass123",
            phone="+212600123456"
        )
        
        self.user2 = User.objects.create_user(
            username="testuser2", 
            email="user2@example.com",
            password="testpass123"
        )
        
        # Create addresses for user1
        self.home_address = Address.objects.create(
            user=self.user1,
            kind=Address.Kind.SHIPPING,
            full_name="John Doe",
            line1="123 Main St",
            city="Casablanca",
            country="MA",
            phone="+212600123456",
            label="Home"
        )
        
        self.work_address = Address.objects.create(
            user=self.user1,
            kind=Address.Kind.BILLING,
            full_name="John Doe",
            line1="456 Office Blvd",
            line2="Suite 789",
            city="Rabat",
            region="Rabat-Salé-Kénitra",
            postal_code="10000",
            country="MA",
            label="Work"
        )
        
        self.other_address = Address.objects.create(
            user=self.user2,
            kind=Address.Kind.OTHER,
            full_name="Jane Smith",
            line1="789 Friend Ave",
            city="Marrakech",
            country="MA",
            label="Friend's Place"
        )

    def test_user_can_have_multiple_addresses(self):
        """Test that a user can have multiple addresses"""
        # user1 already has home_address and work_address from setUp
        self.assertEqual(self.user1.addresses.count(), 2)
        self.assertTrue(self.user1.addresses.filter(kind=Address.Kind.SHIPPING).exists())
        self.assertTrue(self.user1.addresses.filter(kind=Address.Kind.BILLING).exists())

    def test_default_address_functionality(self):
        """Test default address behavior"""
        # Set home address as default
        self.home_address.is_default = True
        self.home_address.save()
        
        # Set work address as default (should override previous default)
        self.work_address.is_default = True
        self.work_address.save()
        
        # Check that work address is now the default
        default_address = self.user1.default_address
        self.assertEqual(default_address, self.work_address)
        
        # Check that home address is no longer default
        self.home_address.refresh_from_db()
        self.assertFalse(self.home_address.is_default)

    def test_address_filtering_by_kind(self):
        """Test filtering addresses by kind"""
        # Create additional address for user1
        Address.objects.create(
            user=self.user1,
            kind=Address.Kind.OTHER,
            full_name="John Doe",
            line1="789 Other St",
            city="Marrakech",
            country="MA",
            label="Other"
        )
        
        # Test filtering
        shipping_addresses = self.user1.get_addresses_by_kind(Address.Kind.SHIPPING)
        billing_addresses = self.user1.get_addresses_by_kind(Address.Kind.BILLING)
        other_addresses = self.user1.get_addresses_by_kind(Address.Kind.OTHER)
        
        self.assertEqual(shipping_addresses.count(), 1)
        self.assertEqual(billing_addresses.count(), 1) 
        self.assertEqual(other_addresses.count(), 1)
        
        self.assertEqual(shipping_addresses.first(), self.home_address)
        self.assertEqual(billing_addresses.first(), self.work_address)

    def test_users_have_separate_addresses(self):
        """Test that each user has their own addresses (no sharing in OneToMany)"""
        # user1 has 2 addresses, user2 has 1 address
        self.assertEqual(self.user1.addresses.count(), 2)
        self.assertEqual(self.user2.addresses.count(), 1)
        
        # Check that addresses belong to correct users
        self.assertTrue(self.user1.addresses.filter(id=self.home_address.id).exists())
        self.assertTrue(self.user1.addresses.filter(id=self.work_address.id).exists())
        self.assertTrue(self.user2.addresses.filter(id=self.other_address.id).exists())
        
        # user2 should not have access to user1's addresses
        self.assertFalse(self.user2.addresses.filter(id=self.home_address.id).exists())

    def test_address_belongs_to_single_user(self):
        """Test that addresses belong to one user only in OneToMany relationship"""
        # Each address can only belong to one user
        self.assertEqual(self.home_address.user, self.user1)
        self.assertEqual(self.work_address.user, self.user1)
        self.assertEqual(self.other_address.user, self.user2)
        
        # Cannot change address ownership without explicit reassignment
        # This is the nature of OneToMany relationship

    def test_address_string_representation(self):
        """Test address string representation"""
        expected = "John Doe — 123 Main St, Casablanca"
        self.assertEqual(str(self.home_address), expected)

    def test_user_without_addresses(self):
        """Test user with no addresses"""
        empty_user = User.objects.create_user(
            username="emptyuser",
            email="empty@example.com",
            password="testpass123"
        )
        
        self.assertEqual(empty_user.addresses.count(), 0)
        self.assertIsNone(empty_user.default_address)

    def test_address_deletion_cascade(self):
        """Test that deleting an address removes it from user's addresses"""
        initial_count = self.user1.addresses.count()
        address_id = self.home_address.id
        
        # Delete the address
        self.home_address.delete()
        
        # Check that address is deleted and user's address count decreased
        self.assertFalse(Address.objects.filter(id=address_id).exists())
        self.assertEqual(self.user1.addresses.count(), initial_count - 1)


class UserProfileTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe"
        )
        
        # Create profile
        self.profile = UserProfile.objects.create(
            user=self.user,
            date_of_birth=date(1990, 5, 15),
            gender=UserProfile.Gender.MALE,
            bio="Test bio for user",
            website="https://example.com",
            loyalty_points=1500,
            marketing_emails=True
        )

    def test_profile_creation(self):
        """Test UserProfile creation and basic fields"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.gender, UserProfile.Gender.MALE)
        self.assertEqual(self.profile.loyalty_points, 1500)
        self.assertEqual(self.profile.membership_tier, UserProfile.MembershipTier.SILVER)
        self.assertTrue(self.profile.marketing_emails)

    def test_profile_str_method(self):
        """Test profile string representation"""
        expected = f"{self.user.username}'s Profile"
        self.assertEqual(str(self.profile), expected)

    def test_full_name_property(self):
        """Test full_name property"""
        self.assertEqual(self.profile.full_name, "John Doe")
        
        # Test with user without names
        user_no_names = User.objects.create_user(
            username="testuser",
            email="test@example.com", 
            password="testpass123"
        )
        profile_no_names = UserProfile.objects.create(user=user_no_names)
        self.assertEqual(profile_no_names.full_name, "testuser")

    def test_age_calculation(self):
        """Test age property calculation"""
        expected_age = date.today().year - 1990
        # Adjust if birthday hasn't occurred this year
        if (date.today().month, date.today().day) < (5, 15):
            expected_age -= 1
        
        self.assertEqual(self.profile.age, expected_age)

    def test_age_without_birth_date(self):
        """Test age property when no birth date is set"""
        new_user = User.objects.create_user(
            username="ageuser",
            email="age@example.com",
            password="testpass123"
        )
        profile = UserProfile.objects.create(user=new_user)
        self.assertIsNone(profile.age)

    def test_loyalty_points_and_membership_tier(self):
        """Test loyalty points and membership tier updates"""
        # Create new user for this test
        tier_user = User.objects.create_user(
            username="loyaltyuser",
            email="loyalty@example.com",
            password="testpass123"
        )
        
        # Test bronze tier
        profile = UserProfile.objects.create(user=tier_user, loyalty_points=500)
        self.assertEqual(profile.membership_tier, UserProfile.MembershipTier.BRONZE)
        
        # Test silver tier (1000+)
        profile.loyalty_points = 1200
        profile.save()
        self.assertEqual(profile.membership_tier, UserProfile.MembershipTier.SILVER)
        
        # Test gold tier (5000+)
        profile.loyalty_points = 6000
        profile.save()
        self.assertEqual(profile.membership_tier, UserProfile.MembershipTier.GOLD)
        
        # Test platinum tier (10000+)
        profile.loyalty_points = 15000
        profile.save()
        self.assertEqual(profile.membership_tier, UserProfile.MembershipTier.PLATINUM)

    def test_add_loyalty_points(self):
        """Test adding loyalty points"""
        initial_points = self.profile.loyalty_points
        initial_tier = self.profile.membership_tier
        
        self.profile.add_loyalty_points(1000)
        
        self.assertEqual(self.profile.loyalty_points, initial_points + 1000)
        # Should still be silver tier (1500 + 1000 = 2500, silver is 1000-4999)
        self.assertEqual(self.profile.membership_tier, UserProfile.MembershipTier.SILVER)

    def test_add_loyalty_points_tier_promotion(self):
        """Test loyalty points addition that triggers tier promotion"""
        # Start with a new user and profile
        new_user = User.objects.create_user(
            username="tieruser",
            email="tier@example.com",
            password="testpass123"
        )
        profile = UserProfile.objects.create(user=new_user, loyalty_points=500)
        self.assertEqual(profile.membership_tier, UserProfile.MembershipTier.BRONZE)
        
        # Add enough points to reach silver
        profile.add_loyalty_points(600)  # 500 + 600 = 1100
        self.assertEqual(profile.membership_tier, UserProfile.MembershipTier.SILVER)

    def test_deduct_loyalty_points_success(self):
        """Test successful loyalty points deduction"""
        initial_points = self.profile.loyalty_points  # 1500
        
        success = self.profile.deduct_loyalty_points(500)
        
        self.assertTrue(success)
        self.assertEqual(self.profile.loyalty_points, initial_points - 500)  # 1000

    def test_deduct_loyalty_points_insufficient(self):
        """Test loyalty points deduction with insufficient balance"""
        success = self.profile.deduct_loyalty_points(2000)  # More than 1500 available
        
        self.assertFalse(success)
        self.assertEqual(self.profile.loyalty_points, 1500)  # Should remain unchanged

    def test_loyalty_discount_percentage(self):
        """Test discount percentage based on membership tier"""
        # Create separate users for each tier test
        bronze_user = User.objects.create_user(
            username="bronzeuser",
            email="bronze@example.com",
            password="testpass123"
        )
        silver_user = User.objects.create_user(
            username="silveruser",
            email="silver@example.com",
            password="testpass123"
        )
        gold_user = User.objects.create_user(
            username="golduser",
            email="gold@example.com",
            password="testpass123"
        )
        platinum_user = User.objects.create_user(
            username="platinumuser",
            email="platinum@example.com",
            password="testpass123"
        )
        
        # Bronze - 0%
        bronze_profile = UserProfile.objects.create(user=bronze_user, loyalty_points=500)
        self.assertEqual(bronze_profile.get_loyalty_discount_percentage(), 0)
        
        # Silver - 5%
        silver_profile = UserProfile.objects.create(user=silver_user, loyalty_points=1500)
        self.assertEqual(silver_profile.get_loyalty_discount_percentage(), 5)
        
        # Gold - 10%
        gold_profile = UserProfile.objects.create(user=gold_user, loyalty_points=6000)
        self.assertEqual(gold_profile.get_loyalty_discount_percentage(), 10)
        
        # Platinum - 15%
        platinum_profile = UserProfile.objects.create(user=platinum_user, loyalty_points=12000)
        self.assertEqual(platinum_profile.get_loyalty_discount_percentage(), 15)

    def test_can_receive_marketing(self):
        """Test marketing communication eligibility"""
        # Active user with marketing enabled
        self.assertTrue(self.profile.can_receive_marketing())
        
        # Inactive user
        self.user.is_active = False
        self.user.save()
        self.assertFalse(self.profile.can_receive_marketing())
        
        # Active user with marketing disabled
        self.user.is_active = True
        self.user.save()
        self.profile.marketing_emails = False
        self.profile.save()
        self.assertFalse(self.profile.can_receive_marketing())

    def test_profile_one_to_one_relationship(self):
        """Test that each user can have only one profile"""
        # Try to create another profile for the same user
        with self.assertRaises(Exception):
            UserProfile.objects.create(user=self.user)

    def test_profile_cascade_deletion(self):
        """Test that profile is deleted when user is deleted"""
        profile_id = self.profile.id
        user_id = self.user.id
        
        # Delete user
        self.user.delete()
        
        # Profile should be deleted too
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())


@override_settings(
    REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
    },
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
)
class UserAPITestCase(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="apiuser",
            email="api@example.com",
            password="testpass123",
            first_name="API",
            last_name="User",
            phone="+212600123456"
        )
        
        # Create profile
        self.profile = UserProfile.objects.create(
            user=self.user,
            date_of_birth=date(1985, 3, 20),
            gender=UserProfile.Gender.MALE,
            bio="API test user",
            loyalty_points=2500,
            marketing_emails=True
        )
        # Update membership tier based on points
        self.profile._update_membership_tier()
        self.profile.save()
        
        # Create some addresses
        self.address1 = Address.objects.create(
            user=self.user,
            kind=Address.Kind.SHIPPING,
            full_name="API User",
            line1="123 API Street",
            city="Test City",
            country="MA",
            is_default=True,
            label="Home"
        )
        
        self.address2 = Address.objects.create(
            user=self.user,
            kind=Address.Kind.BILLING,
            full_name="API User", 
            line1="456 Work Ave",
            city="Test City",
            country="MA",
            label="Office"
        )

    def authenticate_user(self):
        """Helper to authenticate user"""
        self.client.force_authenticate(user=self.user)

    def test_get_me_authenticated(self):
        """Test GET /api/me/ with authenticated user"""
        self.authenticate_user()
        
        url = reverse('user-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        # Check user fields
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], 'apiuser')
        self.assertEqual(data['email'], 'api@example.com')
        self.assertEqual(data['first_name'], 'API')
        self.assertEqual(data['last_name'], 'User')
        self.assertEqual(data['phone'], '+212600123456')
        
        # Check profile data
        self.assertIn('profile', data)
        profile_data = data['profile']
        self.assertEqual(profile_data['loyalty_points'], 2500)
        self.assertEqual(profile_data['membership_tier'], 'silver')
        self.assertEqual(profile_data['full_name'], 'API User')
        self.assertTrue(profile_data['marketing_emails'])
        
        # Check address count
        self.assertEqual(data['addresses_count'], 2)
        self.assertEqual(data['default_address_id'], self.address1.id)

    def test_get_me_unauthenticated(self):
        """Test GET /api/me/ without authentication"""
        url = reverse('user-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_me_creates_profile_if_missing(self):
        """Test that GET /api/me/ creates profile if user doesn't have one"""
        # Create user without profile
        user_no_profile = User.objects.create_user(
            username="noprofile",
            email="noprofile@example.com", 
            password="testpass123"
        )
        
        self.client.force_authenticate(user=user_no_profile)
        
        # Ensure no profile exists
        self.assertFalse(UserProfile.objects.filter(user=user_no_profile).exists())
        
        url = reverse('user-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that profile was created
        self.assertTrue(UserProfile.objects.filter(user=user_no_profile).exists())
        
        # Check profile data in response
        self.assertIn('profile', response.data)
        profile_data = response.data['profile']
        self.assertEqual(profile_data['loyalty_points'], 0)
        self.assertEqual(profile_data['membership_tier'], 'bronze')

    def test_get_me_user_with_no_addresses(self):
        """Test GET /api/me/ for user with no addresses"""
        # Create user with profile but no addresses
        user_no_addr = User.objects.create_user(
            username="noaddr",
            email="noaddr@example.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=user_no_addr)
        
        self.client.force_authenticate(user=user_no_addr)
        
        url = reverse('user-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['addresses_count'], 0)
        self.assertIsNone(response.data['default_address_id'])

    def test_patch_me_authenticated(self):
        """Test PATCH /api/me/ with authenticated user"""
        self.authenticate_user()
        
        url = reverse('user-me')
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '+212600987654',
            'locale': 'en',
            'timezone': 'UTC'
        }
        
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the data was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.phone, '+212600987654')
        self.assertEqual(self.user.locale, 'en')
        self.assertEqual(self.user.timezone, 'UTC')
        
        # Verify response contains updated data
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        self.assertEqual(response.data['phone'], '+212600987654')

    def test_patch_me_partial_update(self):
        """Test PATCH /api/me/ with partial data"""
        self.authenticate_user()
        
        url = reverse('user-me')
        update_data = {
            'first_name': 'NewFirst'
        }
        
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only specified field was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NewFirst')
        # Other fields should remain unchanged
        self.assertEqual(self.user.last_name, 'User')  # Original value from setUp

    def test_patch_me_unauthenticated(self):
        """Test PATCH /api/me/ without authentication"""
        url = reverse('user-me')
        update_data = {
            'first_name': 'Unauthorized'
        }
        
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_me_invalid_data(self):
        """Test PATCH /api/me/ with invalid data"""
        self.authenticate_user()
        
        url = reverse('user-me')
        update_data = {
            'locale': 'invalid_locale_code_too_long'  # This exceeds the max_length=10
        }
        
        response = self.client.patch(url, update_data, format='json')
        
        # Should return 400 due to validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('locale', response.data)

    def test_get_addresses_authenticated_with_addresses(self):
        """Test GET /api/me/addresses/ with authenticated user who has addresses"""
        self.authenticate_user()
        
        url = reverse('user-addresses')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return list of 2 addresses (from setUp)
        self.assertEqual(len(response.data), 2)
        
        # Check address data structure
        address_data = response.data[0]  # First address (should be default)
        expected_fields = [
            'id', 'kind', 'full_name', 'line1', 'line2', 'city',
            'region', 'postal_code', 'country', 'phone', 'is_default',
            'label', 'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, address_data)
        
        # Verify default address comes first
        self.assertTrue(response.data[0]['is_default'])  # Default address first
        self.assertFalse(response.data[1]['is_default'])  # Non-default second

    def test_get_addresses_authenticated_no_addresses(self):
        """Test GET /api/me/addresses/ with authenticated user who has no addresses"""
        # Create user with no addresses
        user_no_addr = User.objects.create_user(
            username="noaddress",
            email="noaddress@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=user_no_addr)
        
        url = reverse('user-addresses')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Empty list
        self.assertEqual(response.data, [])

    def test_get_addresses_unauthenticated(self):
        """Test GET /api/me/addresses/ without authentication"""
        url = reverse('user-addresses')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_addresses_ordering(self):
        """Test that addresses are ordered by default first, then by creation date"""
        self.authenticate_user()
        
        # Create additional addresses with specific ordering
        older_address = Address.objects.create(
            user=self.user,
            kind=Address.Kind.OTHER,
            full_name="Old Address",
            line1="999 Old Street",
            city="Old City",
            country="MA",
            label="Old"
        )
        
        # Make the older address default (should move to front)
        older_address.is_default = True
        older_address.save()
        
        url = reverse('user-addresses')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # 2 from setUp + 1 new
        
        # First address should be the default (older_address)
        self.assertEqual(response.data[0]['id'], older_address.id)
        self.assertTrue(response.data[0]['is_default'])
        
        # Other addresses should not be default
        self.assertFalse(response.data[1]['is_default'])
        self.assertFalse(response.data[2]['is_default'])

    def test_get_addresses_user_isolation(self):
        """Test that users only see their own addresses"""
        # Create another user with addresses
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        Address.objects.create(
            user=other_user,
            kind=Address.Kind.SHIPPING,
            full_name="Other User",
            line1="Other Street",
            city="Other City",
            country="MA"
        )
        
        # Authenticate as original user
        self.authenticate_user()
        
        url = reverse('user-addresses')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only original user's addresses
        
        # Verify all addresses belong to authenticated user
        for address_data in response.data:
            # Get the actual address to verify user
            address = Address.objects.get(id=address_data['id'])
            self.assertEqual(address.user, self.user)

    def test_post_address_authenticated(self):
        """Test POST /api/me/addresses/ with authenticated user"""
        self.authenticate_user()
        
        url = reverse('user-addresses')
        address_data = {
            'kind': 'shipping',
            'full_name': 'Jane Doe',
            'line1': '789 New Street',
            'line2': 'Apt 456',
            'city': 'Marrakech',
            'region': 'Marrakech-Safi',
            'postal_code': '40000',
            'country': 'MA',
            'phone': '+212600555666',
            'is_default': False,
            'label': 'New Home'
        }
        
        response = self.client.post(url, address_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the response data
        self.assertEqual(response.data['full_name'], 'Jane Doe')
        self.assertEqual(response.data['line1'], '789 New Street')
        self.assertEqual(response.data['city'], 'Marrakech')
        self.assertEqual(response.data['kind'], 'shipping')
        self.assertFalse(response.data['is_default'])
        self.assertEqual(response.data['label'], 'New Home')
        
        # Verify the address was created in database
        self.assertEqual(Address.objects.filter(user=self.user).count(), 3)  # 2 from setUp + 1 new
        new_address = Address.objects.get(full_name='Jane Doe')
        self.assertEqual(new_address.user, self.user)
        self.assertEqual(new_address.line1, '789 New Street')

    def test_post_address_minimal_data(self):
        """Test POST /api/me/addresses/ with minimal required data"""
        self.authenticate_user()
        
        url = reverse('user-addresses')
        address_data = {
            'full_name': 'Minimal Address',
            'line1': '123 Simple St',
            'city': 'TestCity'
        }
        
        response = self.client.post(url, address_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify defaults were applied
        self.assertEqual(response.data['kind'], 'shipping')  # Default kind
        self.assertEqual(response.data['country'], 'MA')     # Default country
        self.assertFalse(response.data['is_default'])        # Default is_default
        
        # Verify it was saved
        new_address = Address.objects.get(full_name='Minimal Address')
        self.assertEqual(new_address.user, self.user)

    def test_post_address_set_as_default(self):
        """Test POST /api/me/addresses/ with is_default=True"""
        self.authenticate_user()
        
        # First verify current default
        current_default = Address.objects.get(user=self.user, is_default=True)
        
        url = reverse('user-addresses')
        address_data = {
            'full_name': 'New Default',
            'line1': '555 Default Ave',
            'city': 'DefaultCity',
            'is_default': True
        }
        
        response = self.client.post(url, address_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_default'])
        
        # Verify old default is no longer default
        current_default.refresh_from_db()
        self.assertFalse(current_default.is_default)
        
        # Verify new address is the default
        new_address = Address.objects.get(full_name='New Default')
        self.assertTrue(new_address.is_default)

    def test_post_address_missing_required_fields(self):
        """Test POST /api/me/addresses/ with missing required fields"""
        self.authenticate_user()
        
        url = reverse('user-addresses')
        incomplete_data = {
            'line1': '123 Missing Data St'
            # Missing full_name and city (required fields)
        }
        
        response = self.client.post(url, incomplete_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that validation errors are returned
        self.assertIn('full_name', response.data)
        self.assertIn('city', response.data)
        
        # Verify no address was created
        self.assertEqual(Address.objects.filter(user=self.user).count(), 2)  # Only setUp addresses

    def test_post_address_unauthenticated(self):
        """Test POST /api/me/addresses/ without authentication"""
        url = reverse('user-addresses')
        address_data = {
            'full_name': 'Unauthorized User',
            'line1': '123 Unauthorized St',
            'city': 'UnauthorizedCity'
        }
        
        response = self.client.post(url, address_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Verify no address was created
        self.assertFalse(Address.objects.filter(full_name='Unauthorized User').exists())

    def test_post_address_invalid_kind(self):
        """Test POST /api/me/addresses/ with invalid address kind"""
        self.authenticate_user()
        
        url = reverse('user-addresses')
        address_data = {
            'full_name': 'Test User',
            'line1': '123 Test St',
            'city': 'TestCity',
            'kind': 'invalid_kind'  # Not in Address.Kind.choices
        }
        
        response = self.client.post(url, address_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('kind', response.data)

    def test_post_address_user_isolation(self):
        """Test that created addresses belong to the authenticated user only"""
        # Create another user
        other_user = User.objects.create_user(
            username="otheruser2",
            email="other2@example.com",
            password="testpass123"
        )
        
        # Authenticate as original user
        self.authenticate_user()
        
        url = reverse('user-addresses')
        address_data = {
            'full_name': 'Isolated Address',
            'line1': '123 Isolated St',
            'city': 'IsolatedCity'
        }
        
        response = self.client.post(url, address_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the address belongs to authenticated user, not other user
        new_address = Address.objects.get(full_name='Isolated Address')
        self.assertEqual(new_address.user, self.user)
        self.assertNotEqual(new_address.user, other_user)
        
        # Verify other user has no addresses
        self.assertEqual(Address.objects.filter(user=other_user).count(), 0)
