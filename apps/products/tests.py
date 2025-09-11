from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from .models import Category, Product, Color, Size, Tag


class CategoryListAPITestCase(APITestCase):
    """Test cases for Category List API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create active categories
        self.electronics = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic devices and gadgets",
            is_active=True
        )
        
        self.accessories = Category.objects.create(
            name="Accessories", 
            slug="accessories",
            description="Phone and computer accessories",
            is_active=True
        )
        
        # Create inactive category (should not appear in API)
        self.inactive_category = Category.objects.create(
            name="Discontinued",
            slug="discontinued", 
            description="Old products",
            is_active=False
        )
        
        # Create products for testing product count
        self.product1 = Product.objects.create(
            name="Power Bank",
            slug="power-bank",
            sku="PWB-001",
            price=Decimal("29.99"),
            stock_quantity=10,
            is_active=True
        )
        self.product1.categories.add(self.electronics)
        
        self.product2 = Product.objects.create(
            name="Phone Case",
            slug="phone-case", 
            sku="PC-001",
            price=Decimal("15.99"),
            stock_quantity=25,
            is_active=True
        )
        self.product2.categories.add(self.accessories)
        
        # Inactive product (should not count)
        self.inactive_product = Product.objects.create(
            name="Old Product",
            slug="old-product",
            sku="OLD-001", 
            price=Decimal("9.99"),
            stock_quantity=0,
            is_active=False
        )
        self.inactive_product.categories.add(self.electronics)
        
        self.url = reverse('category-list')
    
    def test_get_categories_success(self):
        """Test GET /api/v1/products/categories/ returns categories successfully"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only active categories
        
        # Check categories are ordered by name
        category_names = [cat['name'] for cat in response.data]
        self.assertEqual(category_names, ['Accessories', 'Electronics'])
    
    def test_get_categories_response_structure(self):
        """Test the response contains all required fields"""
        response = self.client.get(self.url)
        
        category = response.data[0]  # First category (Accessories)
        expected_fields = ['id', 'name', 'slug', 'description', 'is_active', 'products_count']
        
        for field in expected_fields:
            self.assertIn(field, category)
        
        # Check specific values
        self.assertEqual(category['name'], 'Accessories')
        self.assertEqual(category['slug'], 'accessories')
        self.assertEqual(category['description'], 'Phone and computer accessories')
        self.assertTrue(category['is_active'])
        self.assertEqual(category['products_count'], 1)  # One active product
    
    def test_categories_exclude_inactive(self):
        """Test that inactive categories are not returned"""
        response = self.client.get(self.url)
        
        category_names = [cat['name'] for cat in response.data]
        self.assertNotIn('Discontinued', category_names)
        self.assertEqual(len(response.data), 2)
    
    def test_products_count_only_active_products(self):
        """Test that products_count only includes active products"""
        response = self.client.get(self.url)
        
        # Find Electronics category
        electronics_data = next(cat for cat in response.data if cat['name'] == 'Electronics')
        
        # Should only count the active product, not the inactive one
        self.assertEqual(electronics_data['products_count'], 1)
    
    def test_categories_ordered_by_name(self):
        """Test that categories are returned in alphabetical order"""
        # Create another category to test ordering
        Category.objects.create(
            name="Cables",
            slug="cables",
            description="Various cables", 
            is_active=True
        )
        
        response = self.client.get(self.url)
        category_names = [cat['name'] for cat in response.data]
        
        # Should be alphabetically ordered
        self.assertEqual(category_names, ['Accessories', 'Cables', 'Electronics'])
    
    def test_no_authentication_required(self):
        """Test that the endpoint doesn't require authentication"""
        # This should work without any authentication headers
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_empty_categories_list(self):
        """Test response when no active categories exist"""
        # Deactivate all categories
        Category.objects.filter(is_active=True).update(is_active=False)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
    
    def test_category_with_zero_products(self):
        """Test category that has no products shows count of 0"""
        empty_category = Category.objects.create(
            name="Empty Category",
            slug="empty-category",
            description="No products here",
            is_active=True
        )
        
        response = self.client.get(self.url)
        
        empty_cat_data = next(cat for cat in response.data if cat['name'] == 'Empty Category')
        self.assertEqual(empty_cat_data['products_count'], 0)
    
    def test_category_with_multiple_products(self):
        """Test category with multiple products shows correct count"""
        # Add another product to electronics
        product3 = Product.objects.create(
            name="USB Cable",
            slug="usb-cable",
            sku="USB-001",
            price=Decimal("12.99"),
            stock_quantity=50,
            is_active=True
        )
        product3.categories.add(self.electronics)
        
        response = self.client.get(self.url)
        
        electronics_data = next(cat for cat in response.data if cat['name'] == 'Electronics')
        self.assertEqual(electronics_data['products_count'], 2)  # Now has 2 active products


class CategoryModelTestCase(TestCase):
    """Test cases for Category model"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name="Test Category",
            description="Test description"
        )
    
    def test_category_creation(self):
        """Test category is created successfully"""
        self.assertEqual(self.category.name, "Test Category")
        self.assertEqual(self.category.description, "Test description")
        self.assertTrue(self.category.is_active)  # Default value
    
    def test_category_slug_auto_generation(self):
        """Test that slug is auto-generated from name"""
        category = Category.objects.create(
            name="Auto Slug Test Category"
        )
        self.assertEqual(category.slug, "auto-slug-test-category")
    
    def test_category_slug_manual_override(self):
        """Test that manually set slug is preserved"""
        category = Category.objects.create(
            name="Manual Slug Test",
            slug="custom-slug"
        )
        self.assertEqual(category.slug, "custom-slug")
    
    def test_category_string_representation(self):
        """Test category string representation"""
        self.assertEqual(str(self.category), "Test Category")
    
    def test_category_ordering(self):
        """Test categories are ordered by name"""
        category_z = Category.objects.create(name="Z Category")
        category_a = Category.objects.create(name="A Category")
        category_m = Category.objects.create(name="M Category")
        
        categories = list(Category.objects.all())
        category_names = [cat.name for cat in categories]
        
        # Should be ordered alphabetically
        expected_order = ["A Category", "M Category", "Test Category", "Z Category"]
        self.assertEqual(category_names, expected_order)


class ColorListAPITestCase(APITestCase):
    """Test cases for Color List API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create active colors
        self.red = Color.objects.create(
            name="Red",
            hex_code="#FF0000",
            is_active=True
        )
        
        self.blue = Color.objects.create(
            name="Blue",
            hex_code="#0000FF",
            is_active=True
        )
        
        # Create inactive color (should not appear in API)
        self.inactive_color = Color.objects.create(
            name="Discontinued Green",
            hex_code="#00FF00",
            is_active=False
        )
        
        # Create products for testing product count
        self.product1 = Product.objects.create(
            name="Red Power Bank",
            slug="red-power-bank",
            sku="RPB-001",
            price=Decimal("29.99"),
            stock_quantity=10,
            is_active=True
        )
        self.product1.colors.add(self.red)
        
        self.product2 = Product.objects.create(
            name="Blue Phone Case",
            slug="blue-phone-case",
            sku="BPC-001",
            price=Decimal("15.99"),
            stock_quantity=25,
            is_active=True
        )
        self.product2.colors.add(self.blue)
        
        # Inactive product (should not count)
        self.inactive_product = Product.objects.create(
            name="Old Red Product",
            slug="old-red-product",
            sku="ORP-001",
            price=Decimal("9.99"),
            stock_quantity=0,
            is_active=False
        )
        self.inactive_product.colors.add(self.red)
        
        self.url = reverse('color-list')
    
    def test_get_colors_success(self):
        """Test GET /api/v1/products/colors/ returns colors successfully"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only active colors
        
        # Check colors are ordered by name
        color_names = [color['name'] for color in response.data]
        self.assertEqual(color_names, ['Blue', 'Red'])
    
    def test_get_colors_response_structure(self):
        """Test the response contains all required fields"""
        response = self.client.get(self.url)
        
        color = response.data[0]  # First color (Blue)
        expected_fields = ['id', 'name', 'hex_code', 'is_active', 'products_count']
        
        for field in expected_fields:
            self.assertIn(field, color)
        
        # Check specific values
        self.assertEqual(color['name'], 'Blue')
        self.assertEqual(color['hex_code'], '#0000FF')
        self.assertTrue(color['is_active'])
        self.assertEqual(color['products_count'], 1)  # One active product
    
    def test_colors_exclude_inactive(self):
        """Test that inactive colors are not returned"""
        response = self.client.get(self.url)
        
        color_names = [color['name'] for color in response.data]
        self.assertNotIn('Discontinued Green', color_names)
        self.assertEqual(len(response.data), 2)
    
    def test_products_count_only_active_products(self):
        """Test that products_count only includes active products"""
        response = self.client.get(self.url)
        
        # Find Red color
        red_data = next(color for color in response.data if color['name'] == 'Red')
        
        # Should only count the active product, not the inactive one
        self.assertEqual(red_data['products_count'], 1)
    
    def test_colors_ordered_by_name(self):
        """Test that colors are returned in alphabetical order"""
        # Create another color to test ordering
        Color.objects.create(
            name="Green",
            hex_code="#008000",
            is_active=True
        )
        
        response = self.client.get(self.url)
        color_names = [color['name'] for color in response.data]
        
        # Should be alphabetically ordered
        self.assertEqual(color_names, ['Blue', 'Green', 'Red'])
    
    def test_no_authentication_required(self):
        """Test that the endpoint doesn't require authentication"""
        # This should work without any authentication headers
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_empty_colors_list(self):
        """Test response when no active colors exist"""
        # Deactivate all colors
        Color.objects.filter(is_active=True).update(is_active=False)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
    
    def test_color_with_zero_products(self):
        """Test color that has no products shows count of 0"""
        empty_color = Color.objects.create(
            name="Empty Color",
            hex_code="#CCCCCC",
            is_active=True
        )
        
        response = self.client.get(self.url)
        
        empty_color_data = next(color for color in response.data if color['name'] == 'Empty Color')
        self.assertEqual(empty_color_data['products_count'], 0)
    
    def test_color_with_multiple_products(self):
        """Test color with multiple products shows correct count"""
        # Add another product to red
        product3 = Product.objects.create(
            name="Red Cable",
            slug="red-cable",
            sku="RC-001",
            price=Decimal("12.99"),
            stock_quantity=50,
            is_active=True
        )
        product3.colors.add(self.red)
        
        response = self.client.get(self.url)
        
        red_data = next(color for color in response.data if color['name'] == 'Red')
        self.assertEqual(red_data['products_count'], 2)  # Now has 2 active products


class ColorModelTestCase(TestCase):
    """Test cases for Color model"""
    
    def setUp(self):
        """Set up test data"""
        self.color = Color.objects.create(
            name="Test Color",
            hex_code="#123456"
        )
    
    def test_color_creation(self):
        """Test color is created successfully"""
        self.assertEqual(self.color.name, "Test Color")
        self.assertEqual(self.color.hex_code, "#123456")
        self.assertTrue(self.color.is_active)  # Default value
    
    def test_color_string_representation(self):
        """Test color string representation"""
        self.assertEqual(str(self.color), "Test Color")
    
    def test_color_ordering(self):
        """Test colors are ordered by name"""
        color_z = Color.objects.create(name="Z Color", hex_code="#FFFFFF")
        color_a = Color.objects.create(name="A Color", hex_code="#000000")
        color_m = Color.objects.create(name="M Color", hex_code="#888888")
        
        colors = list(Color.objects.all())
        color_names = [color.name for color in colors]
        
        # Should be ordered alphabetically
        expected_order = ["A Color", "M Color", "Test Color", "Z Color"]
        self.assertEqual(color_names, expected_order)
    
    def test_color_unique_constraints(self):
        """Test that color names and hex codes must be unique"""
        # Test unique name constraint
        with self.assertRaises(Exception):
            Color.objects.create(name="Test Color", hex_code="#DIFFERENT")
        
        # Test unique hex_code constraint
        with self.assertRaises(Exception):
            Color.objects.create(name="Different Name", hex_code="#123456")


class SizeListAPITestCase(APITestCase):
    """Test cases for Size List API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create active sizes with sort order
        self.small = Size.objects.create(
            name="Small",
            abbreviation="S",
            sort_order=1,
            is_active=True
        )
        
        self.large = Size.objects.create(
            name="Large", 
            abbreviation="L",
            sort_order=3,
            is_active=True
        )
        
        self.medium = Size.objects.create(
            name="Medium",
            abbreviation="M", 
            sort_order=2,
            is_active=True
        )
        
        # Create inactive size (should not appear in API)
        self.inactive_size = Size.objects.create(
            name="Discontinued XL",
            abbreviation="XL",
            sort_order=4,
            is_active=False
        )
        
        # Create products for testing product count
        self.product1 = Product.objects.create(
            name="Small T-Shirt",
            slug="small-tshirt",
            sku="ST-S-001",
            price=Decimal("19.99"),
            stock_quantity=10,
            is_active=True
        )
        self.product1.sizes.add(self.small)
        
        self.product2 = Product.objects.create(
            name="Large Jacket",
            slug="large-jacket",
            sku="LJ-L-001", 
            price=Decimal("49.99"),
            stock_quantity=5,
            is_active=True
        )
        self.product2.sizes.add(self.large)
        
        # Inactive product (should not count)
        self.inactive_product = Product.objects.create(
            name="Old Small Product",
            slug="old-small-product",
            sku="OSP-001",
            price=Decimal("9.99"),
            stock_quantity=0,
            is_active=False
        )
        self.inactive_product.sizes.add(self.small)
        
        self.url = reverse('size-list')
    
    def test_get_sizes_success(self):
        """Test GET /api/v1/products/sizes/ returns sizes successfully"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Only active sizes
        
        # Check sizes are ordered by sort_order
        size_names = [size['name'] for size in response.data]
        self.assertEqual(size_names, ['Small', 'Medium', 'Large'])
    
    def test_get_sizes_response_structure(self):
        """Test the response contains all required fields"""
        response = self.client.get(self.url)
        
        size = response.data[0]  # First size (Small)
        expected_fields = ['id', 'name', 'abbreviation', 'sort_order', 'is_active', 'products_count']
        
        for field in expected_fields:
            self.assertIn(field, size)
        
        # Check specific values
        self.assertEqual(size['name'], 'Small')
        self.assertEqual(size['abbreviation'], 'S')
        self.assertEqual(size['sort_order'], 1)
        self.assertTrue(size['is_active'])
        self.assertEqual(size['products_count'], 1)  # One active product
    
    def test_sizes_exclude_inactive(self):
        """Test that inactive sizes are not returned"""
        response = self.client.get(self.url)
        
        size_names = [size['name'] for size in response.data]
        self.assertNotIn('Discontinued XL', size_names)
        self.assertEqual(len(response.data), 3)
    
    def test_products_count_only_active_products(self):
        """Test that products_count only includes active products"""
        response = self.client.get(self.url)
        
        # Find Small size
        small_data = next(size for size in response.data if size['name'] == 'Small')
        
        # Should only count the active product, not the inactive one
        self.assertEqual(small_data['products_count'], 1)
    
    def test_sizes_ordered_by_sort_order(self):
        """Test that sizes are returned in sort_order"""
        response = self.client.get(self.url)
        
        sort_orders = [size['sort_order'] for size in response.data]
        self.assertEqual(sort_orders, [1, 2, 3])
        
        size_names = [size['name'] for size in response.data]
        self.assertEqual(size_names, ['Small', 'Medium', 'Large'])
    
    def test_sizes_secondary_ordering_by_name(self):
        """Test that sizes with same sort_order are ordered by name"""
        # Create two sizes with same sort_order
        Size.objects.create(
            name="Extra Large",
            abbreviation="XL",
            sort_order=5,
            is_active=True
        )
        Size.objects.create(
            name="Double XL", 
            abbreviation="XXL",
            sort_order=5,
            is_active=True
        )
        
        response = self.client.get(self.url)
        
        # Find the sizes with sort_order 5
        sort_5_sizes = [size for size in response.data if size['sort_order'] == 5]
        sort_5_names = [size['name'] for size in sort_5_sizes]
        
        # Should be alphabetically ordered
        self.assertEqual(sort_5_names, ['Double XL', 'Extra Large'])
    
    def test_no_authentication_required(self):
        """Test that the endpoint doesn't require authentication"""
        # This should work without any authentication headers
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_empty_sizes_list(self):
        """Test response when no active sizes exist"""
        # Deactivate all sizes
        Size.objects.filter(is_active=True).update(is_active=False)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
    
    def test_size_with_zero_products(self):
        """Test size that has no products shows count of 0"""
        empty_size = Size.objects.create(
            name="Empty Size",
            abbreviation="ES",
            sort_order=10,
            is_active=True
        )
        
        response = self.client.get(self.url)
        
        empty_size_data = next(size for size in response.data if size['name'] == 'Empty Size')
        self.assertEqual(empty_size_data['products_count'], 0)
    
    def test_size_with_multiple_products(self):
        """Test size with multiple products shows correct count"""
        # Add another product to small size
        product3 = Product.objects.create(
            name="Small Hat",
            slug="small-hat",
            sku="SH-001",
            price=Decimal("12.99"),
            stock_quantity=20,
            is_active=True
        )
        product3.sizes.add(self.small)
        
        response = self.client.get(self.url)
        
        small_data = next(size for size in response.data if size['name'] == 'Small')
        self.assertEqual(small_data['products_count'], 2)  # Now has 2 active products


class SizeModelTestCase(TestCase):
    """Test cases for Size model"""
    
    def setUp(self):
        """Set up test data"""
        self.size = Size.objects.create(
            name="Test Size",
            abbreviation="TS",
            sort_order=1
        )
    
    def test_size_creation(self):
        """Test size is created successfully"""
        self.assertEqual(self.size.name, "Test Size")
        self.assertEqual(self.size.abbreviation, "TS")
        self.assertEqual(self.size.sort_order, 1)
        self.assertTrue(self.size.is_active)  # Default value
    
    def test_size_string_representation(self):
        """Test size string representation"""
        self.assertEqual(str(self.size), "Test Size")
    
    def test_size_ordering(self):
        """Test sizes are ordered by sort_order, then name"""
        size_z = Size.objects.create(name="Z Size", sort_order=2)
        size_a = Size.objects.create(name="A Size", sort_order=1) 
        size_m = Size.objects.create(name="M Size", sort_order=1)  # Same sort_order as size_a
        
        sizes = list(Size.objects.all())
        size_names = [size.name for size in sizes]
        
        # Should be ordered by sort_order first, then alphabetically by name
        expected_order = ["A Size", "M Size", "Test Size", "Z Size"]
        self.assertEqual(size_names, expected_order)
    
    def test_size_unique_constraint(self):
        """Test that size names must be unique"""
        with self.assertRaises(Exception):
            Size.objects.create(name="Test Size", abbreviation="TS2", sort_order=2)


class TagListAPITestCase(APITestCase):
    """Test cases for Tag List API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create active tags
        self.wireless = Tag.objects.create(
            name="Wireless",
            slug="wireless",
            is_active=True
        )
        
        self.waterproof = Tag.objects.create(
            name="Waterproof",
            slug="waterproof", 
            is_active=True
        )
        
        self.fast_charging = Tag.objects.create(
            name="Fast Charging",
            slug="fast-charging",
            is_active=True
        )
        
        # Create inactive tag (should not appear in API)
        self.inactive_tag = Tag.objects.create(
            name="Discontinued Feature",
            slug="discontinued-feature",
            is_active=False
        )
        
        # Create products for testing product count
        self.product1 = Product.objects.create(
            name="Wireless Power Bank",
            slug="wireless-power-bank",
            sku="WPB-001",
            price=Decimal("39.99"),
            stock_quantity=15,
            is_active=True
        )
        self.product1.tags.add(self.wireless, self.fast_charging)
        
        self.product2 = Product.objects.create(
            name="Waterproof Phone Case",
            slug="waterproof-phone-case",
            sku="WPC-001",
            price=Decimal("24.99"),
            stock_quantity=30,
            is_active=True
        )
        self.product2.tags.add(self.waterproof)
        
        # Inactive product (should not count)
        self.inactive_product = Product.objects.create(
            name="Old Wireless Product",
            slug="old-wireless-product", 
            sku="OWP-001",
            price=Decimal("19.99"),
            stock_quantity=0,
            is_active=False
        )
        self.inactive_product.tags.add(self.wireless)
        
        self.url = reverse('tag-list')
    
    def test_get_tags_success(self):
        """Test GET /api/v1/products/tags/ returns tags successfully"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Only active tags
        
        # Check tags are ordered by name
        tag_names = [tag['name'] for tag in response.data]
        self.assertEqual(tag_names, ['Fast Charging', 'Waterproof', 'Wireless'])
    
    def test_get_tags_response_structure(self):
        """Test the response contains all required fields"""
        response = self.client.get(self.url)
        
        tag = response.data[0]  # First tag (Fast Charging)
        expected_fields = ['id', 'name', 'slug', 'is_active', 'products_count']
        
        for field in expected_fields:
            self.assertIn(field, tag)
        
        # Check specific values
        self.assertEqual(tag['name'], 'Fast Charging')
        self.assertEqual(tag['slug'], 'fast-charging')
        self.assertTrue(tag['is_active'])
        self.assertEqual(tag['products_count'], 1)  # One active product
    
    def test_tags_exclude_inactive(self):
        """Test that inactive tags are not returned"""
        response = self.client.get(self.url)
        
        tag_names = [tag['name'] for tag in response.data]
        self.assertNotIn('Discontinued Feature', tag_names)
        self.assertEqual(len(response.data), 3)
    
    def test_products_count_only_active_products(self):
        """Test that products_count only includes active products"""
        response = self.client.get(self.url)
        
        # Find Wireless tag
        wireless_data = next(tag for tag in response.data if tag['name'] == 'Wireless')
        
        # Should only count the active product, not the inactive one
        self.assertEqual(wireless_data['products_count'], 1)
    
    def test_tags_ordered_by_name(self):
        """Test that tags are returned in alphabetical order"""
        # Create another tag to test ordering
        Tag.objects.create(
            name="Bluetooth",
            slug="bluetooth",
            is_active=True
        )
        
        response = self.client.get(self.url)
        tag_names = [tag['name'] for tag in response.data]
        
        # Should be alphabetically ordered
        self.assertEqual(tag_names, ['Bluetooth', 'Fast Charging', 'Waterproof', 'Wireless'])
    
    def test_no_authentication_required(self):
        """Test that the endpoint doesn't require authentication"""
        # This should work without any authentication headers
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_empty_tags_list(self):
        """Test response when no active tags exist"""
        # Deactivate all tags
        Tag.objects.filter(is_active=True).update(is_active=False)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
    
    def test_tag_with_zero_products(self):
        """Test tag that has no products shows count of 0"""
        empty_tag = Tag.objects.create(
            name="Empty Tag",
            slug="empty-tag",
            is_active=True
        )
        
        response = self.client.get(self.url)
        
        empty_tag_data = next(tag for tag in response.data if tag['name'] == 'Empty Tag')
        self.assertEqual(empty_tag_data['products_count'], 0)
    
    def test_tag_with_multiple_products(self):
        """Test tag with multiple products shows correct count"""
        # Add another product to wireless tag
        product3 = Product.objects.create(
            name="Wireless Headphones",
            slug="wireless-headphones",
            sku="WH-001",
            price=Decimal("79.99"),
            stock_quantity=8,
            is_active=True
        )
        product3.tags.add(self.wireless)
        
        response = self.client.get(self.url)
        
        wireless_data = next(tag for tag in response.data if tag['name'] == 'Wireless')
        self.assertEqual(wireless_data['products_count'], 2)  # Now has 2 active products
    
    def test_tag_used_by_same_product_multiple_times(self):
        """Test that same product doesn't inflate tag count"""
        # The wireless power bank already has both wireless and fast_charging tags
        response = self.client.get(self.url)
        
        fast_charging_data = next(tag for tag in response.data if tag['name'] == 'Fast Charging')
        self.assertEqual(fast_charging_data['products_count'], 1)  # One product, not duplicated


class TagModelTestCase(TestCase):
    """Test cases for Tag model"""
    
    def setUp(self):
        """Set up test data"""
        self.tag = Tag.objects.create(
            name="Test Tag"
        )
    
    def test_tag_creation(self):
        """Test tag is created successfully"""
        self.assertEqual(self.tag.name, "Test Tag")
        self.assertTrue(self.tag.is_active)  # Default value
    
    def test_tag_slug_auto_generation(self):
        """Test that slug is auto-generated from name"""
        tag = Tag.objects.create(
            name="Auto Slug Test Tag"
        )
        self.assertEqual(tag.slug, "auto-slug-test-tag")
    
    def test_tag_slug_manual_override(self):
        """Test that manually set slug is preserved"""
        tag = Tag.objects.create(
            name="Manual Slug Test",
            slug="custom-tag-slug"
        )
        self.assertEqual(tag.slug, "custom-tag-slug")
    
    def test_tag_string_representation(self):
        """Test tag string representation"""
        self.assertEqual(str(self.tag), "Test Tag")
    
    def test_tag_ordering(self):
        """Test tags are ordered by name"""
        tag_z = Tag.objects.create(name="Z Tag")
        tag_a = Tag.objects.create(name="A Tag")
        tag_m = Tag.objects.create(name="M Tag")
        
        tags = list(Tag.objects.all())
        tag_names = [tag.name for tag in tags]
        
        # Should be ordered alphabetically
        expected_order = ["A Tag", "M Tag", "Test Tag", "Z Tag"]
        self.assertEqual(tag_names, expected_order)
    
    def test_tag_unique_constraints(self):
        """Test that tag names and slugs must be unique"""
        # Test unique name constraint
        with self.assertRaises(Exception):
            Tag.objects.create(name="Test Tag")
        
        # Test unique slug constraint (even when names are different)
        with self.assertRaises(Exception):
            Tag.objects.create(name="Different Name", slug="test-tag")