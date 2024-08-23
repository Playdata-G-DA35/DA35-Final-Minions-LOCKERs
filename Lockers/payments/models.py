# payments/models.py

from django.db import models
from common.models import Reservations
from django.conf import settings

class Payments(models.Model):
    payment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservations, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    card_number = models.CharField(max_length=16, blank=True, null=True)  # 사용자 카드 번호 추가
    card_expiry = models.CharField(max_length=5, blank=True, null=True)  # 카드 만료일 추가
    card_cvc = models.CharField(max_length=4, blank=True, null=True)  # 카드 CVC 추가
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'Payments'
