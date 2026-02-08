from django.db import models
from django.contrib.auth import get_user_model


class Tweet(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='tweets'
    )
    content = models.CharField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    # class Meta:
    #     db_table = "tweet"
    #     ordering = ['-created_at']
    #     indexes = [models.Index(fields=['created_at'])]

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}"