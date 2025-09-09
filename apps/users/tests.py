from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Address, UserAddress

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
        
        # Create addresses
        self.home_address = Address.objects.create(
            kind=Address.Kind.SHIPPING,
            full_name="John Doe",
            line1="123 Main St",
            city="Casablanca",
            country="MA",
            phone="+212600123456"
        )
        
        self.work_address = Address.objects.create(
            kind=Address.Kind.BILLING,
            full_name="John Doe",
            line1="456 Office Blvd",
            line2="Suite 789",
            city="Rabat",
            region="Rabat-Salé-Kénitra",
            postal_code="10000",
            country="MA"
        )
        
        self.other_address = Address.objects.create(
            kind=Address.Kind.OTHER,
            full_name="Jane Smith",
            line1="789 Friend Ave",
            city="Marrakech",
            country="MA"
        )

    def test_user_can_have_multiple_addresses(self):
        """Test that a user can have multiple addresses"""
        # Add addresses to user1
        UserAddress.objects.create(
            user=self.user1,
            address=self.home_address,
            is_default=True,
            label="Home"
        )
        
        UserAddress.objects.create(
            user=self.user1,
            address=self.work_address,
            label="Work"
        )
        
        self.assertEqual(self.user1.addresses.count(), 2)
        self.assertTrue(self.user1.addresses.filter(kind=Address.Kind.SHIPPING).exists())
        self.assertTrue(self.user1.addresses.filter(kind=Address.Kind.BILLING).exists())

    def test_default_address_functionality(self):
        """Test default address behavior"""
        # Add home address as default
        UserAddress.objects.create(
            user=self.user1,
            address=self.home_address,
            is_default=True,
            label="Home"
        )
        
        # Add work address as default (should override previous default)
        UserAddress.objects.create(
            user=self.user1,
            address=self.work_address,
            is_default=True,
            label="Work"
        )
        
        # Check that work address is now the default
        default_address = self.user1.default_address
        self.assertEqual(default_address, self.work_address)
        
        # Check that home address is no longer default
        home_user_address = UserAddress.objects.get(user=self.user1, address=self.home_address)
        self.assertFalse(home_user_address.is_default)

    def test_address_filtering_by_kind(self):
        """Test filtering addresses by kind"""
        # Add different types of addresses
        UserAddress.objects.create(user=self.user1, address=self.home_address)
        UserAddress.objects.create(user=self.user1, address=self.work_address)
        UserAddress.objects.create(user=self.user1, address=self.other_address)
        
        # Test filtering
        shipping_addresses = self.user1.get_addresses_by_kind(Address.Kind.SHIPPING)
        billing_addresses = self.user1.get_addresses_by_kind(Address.Kind.BILLING)
        other_addresses = self.user1.get_addresses_by_kind(Address.Kind.OTHER)
        
        self.assertEqual(shipping_addresses.count(), 1)
        self.assertEqual(billing_addresses.count(), 1) 
        self.assertEqual(other_addresses.count(), 1)
        
        self.assertEqual(shipping_addresses.first(), self.home_address)
        self.assertEqual(billing_addresses.first(), self.work_address)

    def test_multiple_users_can_share_address(self):
        """Test that multiple users can use the same address"""
        # Both users add the same address
        UserAddress.objects.create(user=self.user1, address=self.home_address, label="Home")
        UserAddress.objects.create(user=self.user2, address=self.home_address, label="Friend's Place")
        
        # Check that address is linked to both users
        self.assertTrue(self.user1.addresses.filter(id=self.home_address.id).exists())
        self.assertTrue(self.user2.addresses.filter(id=self.home_address.id).exists())
        
        # Check reverse relationship
        self.assertEqual(self.home_address.address_users.count(), 2)

    def test_user_address_unique_constraint(self):
        """Test that user-address combination is unique"""
        UserAddress.objects.create(user=self.user1, address=self.home_address)
        
        # Try to create duplicate - should raise error
        with self.assertRaises(Exception):
            UserAddress.objects.create(user=self.user1, address=self.home_address)

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
        """Test that deleting an address removes UserAddress relationships"""
        UserAddress.objects.create(user=self.user1, address=self.home_address)
        
        # Delete the address
        address_id = self.home_address.id
        self.home_address.delete()
        
        # Check that UserAddress relationship is also deleted
        self.assertFalse(UserAddress.objects.filter(address_id=address_id).exists())
        self.assertEqual(self.user1.addresses.count(), 0)
