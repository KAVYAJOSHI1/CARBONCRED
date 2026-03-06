from django.db import models

class CarbonCreditData(models.Model):
    farmer_name = models.CharField(max_length=100)
    farmer_wallet = models.CharField(max_length=42)
    amount_minted = models.FloatField()
    tx_hash = models.CharField(max_length=66, unique=True)
    status = models.CharField(max_length=20, default="Success")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.farmer_name} - {self.amount_minted} RCC"

class Upload(models.Model):
    image = models.ImageField(upload_to='uploads/')
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    image_hash = models.CharField(max_length=64, blank=True, null=True)
    
    # New Field for Delta Logic
    biomass_credits = models.FloatField(default=0.0)

    status = models.CharField(
        max_length=20,
        default='PENDING'
    )