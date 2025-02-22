from django.db import models
from django.conf import settings
import os

# Create your models here.

class Document(models.Model):
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    created_at = models.DateTimeField(auto_now_add=True)
    size = models.BigIntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.filename

    def save(self, *args, **kwargs):
        if not self.size and self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    @property
    def url(self):
        return self.file.url if self.file else None
