from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    email = models.EmailField("email_address", unique=True, max_length=254)
    first_name = models.CharField("first_name", max_length=254)
    last_name = models.CharField("last_name", max_length=254)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name','username']

    class Meta(AbstractUser.Meta):
        ordering = ['id']
    
    def __str__(self):
        """Строковое представление модели"""

        return self.username


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    author = models.ForeignKey(User, verbose_name="author", on_delete=models.CASCADE, related_name='followers')
    created = models.DateTimeField("time created",auto_now_add=True)