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


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following',
        verbose_name='пользователь')
    following = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='подписки')

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique following',
            ),
        )

    def __str__(self) -> str:
        return f'{self.user} : {self.following}'
