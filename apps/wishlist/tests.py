from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from apps.products.models import Product, Category
from .models import Wishlist, WishlistItem

User = get_user_model()


class WishlistAPITestCase(APITestCase):
    """Test case for Wishlist API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com', 
            password='testpass123'
        )

        # Create test category and products
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product1 = Product.objects.create(
            name='Test Product 1',
            slug='test-product-1',
            sku='TEST-PROD-001',
            price=29.99,
            is_active=True
        )
        self.product1.categories.add(self.category)
        
        self.product2 = Product.objects.create(
            name='Test Product 2', 
            slug='test-product-2',
            sku='TEST-PROD-002',
            price=39.99,
            is_active=True
        )
        self.product2.categories.add(self.category)
        
        self.inactive_product = Product.objects.create(
            name='Inactive Product',
            slug='inactive-product',
            sku='TEST-PROD-003',
            price=19.99,
            is_active=False
        )
        self.inactive_product.categories.add(self.category)

        # API endpoints
        self.get_wishlist_url = reverse('get_wishlist')
        self.add_to_wishlist_url = reverse('add_to_wishlist')
        self.clear_wishlist_url = reverse('clear_wishlist')

    def get_remove_url(self, product_id):
        """Get remove from wishlist URL with product ID."""
        return reverse('remove_from_wishlist', kwargs={'product_id': product_id})

    def authenticate_user(self, user):
        """Authenticate user using force_authenticate."""
        self.client.force_authenticate(user=user)

    def test_get_empty_wishlist_creates_new(self):
        """Test getting wishlist creates empty wishlist if none exists."""
        self.authenticate_user(self.user1)
        
        response = self.client.get(self.get_wishlist_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items_count'], 0)
        self.assertEqual(len(response.data['items']), 0)
        self.assertEqual(response.data['user'], self.user1.id)
        
        # Verify wishlist was created in database
        self.assertTrue(Wishlist.objects.filter(user=self.user1).exists())

    def test_get_wishlist_unauthenticated(self):
        """Test getting wishlist without authentication fails."""
        response = self.client.get(self.get_wishlist_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_wishlist_with_items(self):
        """Test getting wishlist with existing items."""
        self.authenticate_user(self.user1)
        
        # Create wishlist with items
        wishlist = Wishlist.objects.create(user=self.user1)
        WishlistItem.objects.create(wishlist=wishlist, product=self.product1)
        WishlistItem.objects.create(wishlist=wishlist, product=self.product2)
        
        response = self.client.get(self.get_wishlist_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items_count'], 2)
        self.assertEqual(len(response.data['items']), 2)
        
        # Check items contain product IDs
        product_ids = [item['product'] for item in response.data['items']]
        self.assertIn(self.product1.id, product_ids)
        self.assertIn(self.product2.id, product_ids)

    def test_add_to_wishlist_success(self):
        """Test successfully adding product to wishlist."""
        self.authenticate_user(self.user1)
        
        data = {'product': self.product1.id}
        response = self.client.post(self.add_to_wishlist_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['items_count'], 1)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['product'], self.product1.id)
        
        # Verify in database
        self.assertTrue(
            WishlistItem.objects.filter(
                wishlist__user=self.user1, 
                product=self.product1
            ).exists()
        )

    def test_add_to_wishlist_unauthenticated(self):
        """Test adding to wishlist without authentication fails."""
        data = {'product': self.product1.id}
        response = self.client.post(self.add_to_wishlist_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_to_wishlist_invalid_product(self):
        """Test adding non-existent product to wishlist fails."""
        self.authenticate_user(self.user1)
        
        data = {'product': 99999}  # Non-existent product ID
        response = self.client.post(self.add_to_wishlist_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Product not found', str(response.data))

    def test_add_to_wishlist_inactive_product(self):
        """Test adding inactive product to wishlist fails."""
        self.authenticate_user(self.user1)
        
        data = {'product': self.inactive_product.id}
        response = self.client.post(self.add_to_wishlist_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Product is not available', str(response.data))

    def test_add_duplicate_product_to_wishlist(self):
        """Test adding same product twice to wishlist fails."""
        self.authenticate_user(self.user1)
        
        # Add product first time
        data = {'product': self.product1.id}
        response = self.client.post(self.add_to_wishlist_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to add same product again
        response = self.client.post(self.add_to_wishlist_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Product is already in your wishlist', str(response.data))

    def test_add_to_wishlist_missing_product_field(self):
        """Test adding to wishlist without product field fails."""
        self.authenticate_user(self.user1)
        
        data = {}  # Missing product field
        response = self.client.post(self.add_to_wishlist_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product', response.data)

    def test_remove_from_wishlist_success(self):
        """Test successfully removing product from wishlist."""
        self.authenticate_user(self.user1)
        
        # Create wishlist with item
        wishlist = Wishlist.objects.create(user=self.user1)
        WishlistItem.objects.create(wishlist=wishlist, product=self.product1)
        WishlistItem.objects.create(wishlist=wishlist, product=self.product2)
        
        response = self.client.delete(self.get_remove_url(self.product1.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items_count'], 1)
        
        # Verify product1 was removed but product2 remains
        self.assertFalse(
            WishlistItem.objects.filter(
                wishlist__user=self.user1,
                product=self.product1
            ).exists()
        )
        self.assertTrue(
            WishlistItem.objects.filter(
                wishlist__user=self.user1,
                product=self.product2
            ).exists()
        )

    def test_remove_from_wishlist_unauthenticated(self):
        """Test removing from wishlist without authentication fails."""
        response = self.client.delete(self.get_remove_url(self.product1.id))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_remove_from_wishlist_no_wishlist(self):
        """Test removing from non-existent wishlist fails."""
        self.authenticate_user(self.user1)
        
        response = self.client.delete(self.get_remove_url(self.product1.id))
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Wishlist does not exist', str(response.data))

    def test_remove_product_not_in_wishlist(self):
        """Test removing product that's not in wishlist fails."""
        self.authenticate_user(self.user1)
        
        # Create empty wishlist
        Wishlist.objects.create(user=self.user1)
        
        response = self.client.delete(self.get_remove_url(self.product1.id))
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Product not found in your wishlist', str(response.data))

    def test_clear_wishlist_success(self):
        """Test successfully clearing wishlist."""
        self.authenticate_user(self.user1)
        
        # Create wishlist with items
        wishlist = Wishlist.objects.create(user=self.user1)
        WishlistItem.objects.create(wishlist=wishlist, product=self.product1)
        WishlistItem.objects.create(wishlist=wishlist, product=self.product2)
        
        response = self.client.delete(self.clear_wishlist_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items_count'], 0)
        self.assertEqual(len(response.data['items']), 0)
        
        # Verify all items were deleted
        self.assertEqual(WishlistItem.objects.filter(wishlist=wishlist).count(), 0)

    def test_clear_wishlist_unauthenticated(self):
        """Test clearing wishlist without authentication fails."""
        response = self.client.delete(self.clear_wishlist_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_clear_wishlist_no_wishlist(self):
        """Test clearing non-existent wishlist fails."""
        self.authenticate_user(self.user1)
        
        response = self.client.delete(self.clear_wishlist_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Wishlist does not exist', str(response.data))

    def test_user_isolation(self):
        """Test that users can only access their own wishlists."""
        # Create wishlists for both users
        wishlist1 = Wishlist.objects.create(user=self.user1)
        wishlist2 = Wishlist.objects.create(user=self.user2)
        
        WishlistItem.objects.create(wishlist=wishlist1, product=self.product1)
        WishlistItem.objects.create(wishlist=wishlist2, product=self.product2)
        
        # User1 should only see their own wishlist
        self.authenticate_user(self.user1)
        response = self.client.get(self.get_wishlist_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items_count'], 1)
        self.assertEqual(response.data['items'][0]['product'], self.product1.id)
        
        # User2 should only see their own wishlist
        self.authenticate_user(self.user2)
        response = self.client.get(self.get_wishlist_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items_count'], 1)
        self.assertEqual(response.data['items'][0]['product'], self.product2.id)


class WishlistModelTestCase(TestCase):
    """Test case for Wishlist models."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            sku='TEST-MODEL-001',
            price=29.99,
            is_active=True
        )
        self.product.categories.add(self.category)

    def test_wishlist_creation(self):
        """Test wishlist model creation."""
        wishlist = Wishlist.objects.create(user=self.user)
        
        self.assertEqual(wishlist.user, self.user)
        self.assertEqual(wishlist.items_count, 0)
        self.assertIsNotNone(wishlist.created_at)
        self.assertIsNotNone(wishlist.updated_at)

    def test_wishlist_str_method(self):
        """Test wishlist string representation."""
        wishlist = Wishlist.objects.create(user=self.user)
        
        expected_str = f"Wishlist for {self.user.email}"
        self.assertEqual(str(wishlist), expected_str)

    def test_wishlist_item_creation(self):
        """Test wishlist item model creation."""
        wishlist = Wishlist.objects.create(user=self.user)
        wishlist_item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product
        )
        
        self.assertEqual(wishlist_item.wishlist, wishlist)
        self.assertEqual(wishlist_item.product, self.product)
        self.assertIsNotNone(wishlist_item.added_at)

    def test_wishlist_item_str_method(self):
        """Test wishlist item string representation."""
        wishlist = Wishlist.objects.create(user=self.user)
        wishlist_item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product
        )
        
        self.assertEqual(str(wishlist_item), self.product.name)

    def test_wishlist_items_count_property(self):
        """Test wishlist items_count property."""
        wishlist = Wishlist.objects.create(user=self.user)
        
        # Initially empty
        self.assertEqual(wishlist.items_count, 0)
        
        # Add items
        WishlistItem.objects.create(wishlist=wishlist, product=self.product)
        
        # Refresh from database
        wishlist.refresh_from_db()
        self.assertEqual(wishlist.items_count, 1)

    def test_unique_constraint(self):
        """Test that the same product cannot be added twice to same wishlist."""
        wishlist = Wishlist.objects.create(user=self.user)
        
        # First item should be created successfully
        WishlistItem.objects.create(wishlist=wishlist, product=self.product)
        
        # Second item with same product should raise IntegrityError
        with self.assertRaises(Exception):  # IntegrityError
            WishlistItem.objects.create(wishlist=wishlist, product=self.product)
