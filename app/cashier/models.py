from django.db import models
from django.contrib.auth.models import User

class Gun(models.Model):
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    stock = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(null=True, blank=True, upload_to='images/')

    def reduce_stock(self, quantity):
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        else:
            return False

from django.db import models
from django.contrib.auth.models import User

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gun = models.ForeignKey(Gun, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)


    @property
    def total_price(self):
        return self.gun.price * self.quantity

    def calculate_discount(self):
        if self.quantity > 25:
            return 0.10  # 10% discount for more than 25 items
        elif self.quantity > 10:
            return 0.05  # 5% discount for more than 10 items
        else:
            return 0.0   # No discount for 10 items or less

    @property
    def discounted_total_price(self):
        discount_factor = 1 - self.calculate_discount()
        return int(self.total_price * discount_factor)

    @discounted_total_price.setter
    def discounted_total_price(self, value):
        # This is a dummy setter, as the discounted_total_price is calculated based on other properties
        pass

    def is_payment_less(self):
        try:
            latest_payment = Payment.objects.filter(order=self).latest('date')
            if latest_payment.amount < self.total_price:
                return True
            else:
                return False
        except Payment.DoesNotExist:
            return False

    def process_purchase(self):
        try:
            gun = self.gun
            if gun.reduce_stock(self.quantity):
                return True
            else:
                return False  # Insufficient stock
        except Gun.DoesNotExist:
            return False


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
