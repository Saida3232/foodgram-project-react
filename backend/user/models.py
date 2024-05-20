from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    email = models.EmailField("email", unique=True, max_length=150)
    first_name = models.CharField("first_name", max_length=150)
    last_name = models.CharField("last_name", max_length=150)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta(AbstractUser.Meta):
        ordering = ['id']

    def __str__(self):
        return self.username
