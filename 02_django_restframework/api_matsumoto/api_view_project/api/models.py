from django.db import models
from django.conf import settings


class Item(models.Model):
    name = models.CharField(max_length=20)
    price = models.IntegerField()
    discount = models.IntegerField()

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=50)
    price = models.IntegerField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products'
    )



