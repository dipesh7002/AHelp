from django.db import models

class Subjects(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField()
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class PostAssignment(models.Model):
    title = models.CharField(max_length=50, null=True, blank=True)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(max_length=200)
    upload_file = models.FileField(upload_to='uploads')
    deadline = models.DateField()
    is_active = models.BooleanField(blank=True, default=True)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



