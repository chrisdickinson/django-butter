from django.db import models
from django.contrib.auth.models import User

class Note(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

class Tag(models.Model):
    note = models.ForeignKey(Note, related_name='tags')
    tag_name = models.CharField(max_length=255)
    visible_to_everyone = models.BooleanField(default=False)
    visible_to_members = models.ManyToManyField(User, related_name='visible_tags')


