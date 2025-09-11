from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Category, SubCategory, Tag, Article, Comment


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    articles_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'is_active', 'created_at', 'articles_count')
        read_only_fields = ('id', 'slug', 'created_at')


class SubCategorySerializer(serializers.ModelSerializer):
    """Serializer for SubCategory model"""
    
    class Meta:
        model = SubCategory
        fields = ('id', 'name', 'slug', 'description', 'is_active', 'created_at')
        read_only_fields = ('id', 'slug', 'created_at')


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'is_active', 'created_at')
        read_only_fields = ('id', 'slug', 'created_at')


class ArticleListSerializer(serializers.ModelSerializer):
    """Serializer for Article list view"""
    author_name = serializers.CharField(source='author.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = (
            'id', 'title', 'slug', 'excerpt', 'author_name', 'category_name', 
            'subcategory_name', 'tags', 'featured_image', 'status', 'is_featured',
            'published_at', 'created_at', 'view_count', 'comments_count'
        )
        read_only_fields = ('id', 'slug', 'created_at')
    
    @extend_schema_field(serializers.IntegerField)
    def get_comments_count(self, obj):
        """Get count of approved comments for this article"""
        return obj.comments.filter(is_approved=True).count()


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Serializer for Article detail view"""
    author_name = serializers.CharField(source='author.username', read_only=True)
    category = CategorySerializer(read_only=True)
    subcategory = SubCategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = (
            'id', 'title', 'slug', 'content', 'excerpt', 'author', 'author_name',
            'category', 'subcategory', 'tags', 'featured_image', 'image_alt_text',
            'meta_title', 'meta_description', 'status', 'is_featured',
            'published_at', 'created_at', 'updated_at', 'view_count', 'comments_count'
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at', 'view_count')
    
    @extend_schema_field(serializers.IntegerField)
    def get_comments_count(self, obj):
        """Get count of approved comments for this article"""
        return obj.comments.filter(is_approved=True).count()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model"""
    author_name = serializers.CharField(source='author.username', read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = (
            'id', 'content', 'author', 'author_name', 'is_approved', 
            'created_at', 'updated_at', 'parent', 'replies_count'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    @extend_schema_field(serializers.IntegerField)
    def get_replies_count(self, obj):
        """Get count of approved replies to this comment"""
        return obj.replies.filter(is_approved=True).count()