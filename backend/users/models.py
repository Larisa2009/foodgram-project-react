from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class FoodgramUser(AbstractUser):
    username = models.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        unique=True,
    )
    first_name = models.CharField(
        max_length=settings.FIRST_NAME_MAX_LENGTH,
        blank=False,
    )
    last_name = models.CharField(
        max_length=settings.LAST_NAME_MAX_LENGTH,
        blank=False,
    )
    email = models.EmailField(
        max_length=settings.EMAIL_MAX_LENGTH,
        unique=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_name_author'),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='check_author'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.author}'
