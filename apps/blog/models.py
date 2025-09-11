from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()


class Category(models.Model):
    """Blog post category"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Categories"
        indexes = [models.Index(fields=['slug'])]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def articles_count(self):
        """Get count of published articles in this category"""
        return self.articles.filter(status='published').count()
    
    @property
    def total_articles_count(self):
        """Get count of all articles in this category"""
        return self.articles.count()


class SubCategory(models.Model):
    """Blog post sub-category"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Sub Categories"
        indexes = [models.Index(fields=['slug'])]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    """Blog post tags"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['slug'])]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Article(models.Model):
    """Blog article model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    content = models.TextField(help_text="Article content/text")
    excerpt = models.TextField(max_length=500, blank=True, help_text="Short description for previews")
    
    # Relationships
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    tags = models.ManyToManyField(Tag, related_name='articles', blank=True)
    
    # Image
    featured_image = models.ImageField(
        upload_to='blog/images/',
        blank=True,
        null=True,
        help_text="Featured image for the article"
    )
    image_alt_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="Alternative text for the featured image"
    )
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=255, blank=True)
    
    # Status and timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False, help_text="Featured articles for homepage")
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Reading stats
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category']),
            models.Index(fields=['author']),
            models.Index(fields=['is_featured', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def is_published(self):
        """Check if article is published"""
        return self.status == 'published' and self.published_at is not None


class Comment(models.Model):
    """Article comments"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_comments')
    content = models.TextField()
    
    # Comment moderation
    is_approved = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Parent comment for replies (nested comments)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['article', 'is_approved']),
            models.Index(fields=['author']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.article.title}"
    
    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return self.parent is not None
