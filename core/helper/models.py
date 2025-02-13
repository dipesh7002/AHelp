from django.db import models
from client.models import Subjects

class AssignmentHelper(models.Model):
    name = models.CharField(max_length=50, blank=True)
    age = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=50, blank=True)
    description = models.TextField(max_length=500, blank=True)
    phone_no = models.PositiveBigIntegerField()
    email = models.EmailField()
    education = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(blank=True)
    experience_years = models.PositiveIntegerField()
    mastery_subjects = models.ManyToManyField(Subjects)
    total_assignment_done = models.PositiveIntegerField()
    average_rating = models.PositiveIntegerField()
    
    is_active = models.BooleanField()
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True)

class HelperRating(models.Model):
    name = models.ForeignKey(AssignmentHelper, on_delete=models.RESTRICT, blank=True)
    rating = models.PositiveIntegerField()
    
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True)