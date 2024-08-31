from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='app.Rental')
def update_car_status(sender, instance, created, **kwargs):
    from .models import Rental, Car
    from django.utils import timezone

    if created:
        return

    current_date = timezone.now().date()

    if instance.end_date < current_date:
        if instance.status != 2:
            instance.status = 2
            instance.car.status = 2
            instance.car.save(update_fields=['status'])
            instance.save(update_fields=['status'])
    elif instance.start_date <= current_date <= instance.end_date:
        if instance.status != 1:
            instance.status = 1
            instance.car.status = 1
            instance.car.save(update_fields=['status'])
            instance.save(update_fields=['status'])