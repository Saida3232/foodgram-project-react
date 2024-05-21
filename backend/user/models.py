from django.contrib.auth.models import AbstractUser
from django.db import models

from foodgram.constants import USERNAME_MAX_LENGTH


class User(AbstractUser):
    email = models.EmailField("email", unique=True,
                              max_length=USERNAME_MAX_LENGTH)
    first_name = models.CharField("first_name", max_length=USERNAME_MAX_LENGTH)
    last_name = models.CharField("last_name", max_length=USERNAME_MAX_LENGTH)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta(AbstractUser.Meta):
        ordering = ['id']

    def __str__(self):
        return self.username
