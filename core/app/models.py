from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from .signals import update_car_status
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


# class Rating(models.Model):
#     car = models.ForeignKey('Car', on_delete=models.CASCADE, related_name='ratings')
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     stars = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
#
#     class Meta:
#         unique_together = ('car', 'user')
#
#     def __str__(self):
#         return f'{self.car.title} - {self.stars} Stars'


class Comment(models.Model):
    car = models.ForeignKey('app.Car', related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey('app.CustomUser', related_name='comments', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Rating(models.Model):
    car = models.ForeignKey('app.Car', related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey('app.CustomUser', related_name='ratings', on_delete=models.CASCADE)
    stars = models.PositiveIntegerField(default=1)  # Минимум 1, максимум 5
    created_at = models.DateTimeField(auto_now_add=True)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, blank=False, null=False)  # Уникальное поле email
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_admin = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return self.username


class BrandCars(models.Model):
    title = models.CharField(max_length=123)

    def __str__(self):
        return self.title


class Category(models.Model):
    title = models.CharField(max_length=123)

    def __str__(self):
        return self.title


# class ChoicesField(models.CharField):
#     def __init__(self, *args, **kwargs):
#         self.choices = kwargs.pop('choices', [])
#         kwargs['max_length'] = max(len(choice[0]) for choice in self.choices)
#         super().__init__(*args, **kwargs)
#
#     def get_prep_value(self, value):
#         if value not in dict(self.choices):
#             raise ValueError(f'Invalid value for ChoicesField: {value}')
#         return super().get_prep_value(value)


class CarBodyType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class FuelType(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Gearbox(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Status(models.Model):
    status = models.CharField(max_length=100)

    def __str__(self):
        return self.status


# Машины:
class Car(models.Model):
    created_at = models.DateTimeField(default=timezone.now, help_text="Дата добавления автомобиля")
    title = models.CharField(max_length=500)
    price_day = models.PositiveIntegerField(help_text="Цена аренды за день в рублях")
    img_front = models.ImageField(upload_to='media/front', blank=False, null=False, default='media/defult_img')
    img_back = models.ImageField(upload_to='media/back', blank=False, null=False, default='media/defult_img')
    salon = models.ImageField(upload_to='media/salon', blank=False, null=False, default='media/defult_img')
    volume = models.DecimalField(max_digits=8, decimal_places=1, help_text="Объем двигателя в литрах")
    power = models.IntegerField(help_text="Мощность двигателя в лошадиных силах")
    fuel_type = models.ForeignKey(
        FuelType, on_delete=models.CASCADE
    )
    gearbox = models.ForeignKey(
        Gearbox, on_delete=models.CASCADE
    )
    type_car_body = models.ForeignKey(
        CarBodyType,
        on_delete=models.CASCADE,
        related_name='cars',
        help_text="Тип кузова"
    )
    brand = models.ForeignKey(BrandCars, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    status = models.ForeignKey(
        Status,
        on_delete=models.CASCADE,
    )

    year = models.PositiveIntegerField(help_text="Год выпуска автомобиля")

    def __str__(self):
        return self.title

    def is_available(self):
        return self.status == 2  # Возвращает True, если автомобиль свободен

    # def get_type_car_body_display(self):
    #     return f'{self.type_car_body}'


# Отзывы на сайт:
class SiteComment(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Comment by {self.author} on {self.created_at}'


# Аренды:
class Rental(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='rentals', help_text="Пользователь, который арендовал автомобиль")
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='rentals')
    start_date = models.DateField(help_text="Дата начала аренды")
    end_date = models.DateField(help_text="Дата окончания аренды")
    number = PhoneNumberField(unique=True, blank=False, null=True, default='')
    total_cost = models.PositiveIntegerField(help_text="Общая стоимость аренды")
    status = models.PositiveSmallIntegerField(
        choices=[
            (1, 'Активно'),
            (2, 'Завершено'),
            (3, 'Отменено')
        ],
        default=1,
        help_text="Статус аренды"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rental of {self.car.title} by {self.user.username} from {self.start_date} to {self.end_date}"

    def calculate_total_cost(self):
        total_days = (self.end_date - self.start_date).days
        self.total_cost = total_days * self.car.price_day
        self.save()
        return self.total_cost

    def is_active(self):
        return self.status == 1

    def cancel(self):
        self.status = 3
        self.car.status = 2  # Освобождаем автомобиль
        self.car.save()
        self.save()

    def complete(self):
        self.status = 2
        self.car.status = 2  # Освобождаем автомобиль
        self.car.save()
        self.save()