from django.db import models
from django.contrib.auth.models import AbstractUser



class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
    )


    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )


    def __str__(self):
        return f'{self.user.username} - {self.author.username}'