from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import *
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


# Изменение

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'car', 'user', 'text', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'car', 'user', 'stars', 'created_at']
        read_only_fields = ['user', 'created_at']

    def validate_stars(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Рейтинг должен быть от 1 до 5 звезд.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class CarCategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'title')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create(
            username=validated_data['username'],
            phone_number=validated_data['phone_number']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class CarIndexSerializers(serializers.ModelSerializer):
    fuel_type = serializers.SlugRelatedField(
        queryset=FuelType.objects.all(),
        slug_field='title'
    )
    gearbox = serializers.SlugRelatedField(
        queryset=Gearbox.objects.all(),
        slug_field='title'
    )
    type_car_body = serializers.SlugRelatedField(
        queryset=CarBodyType.objects.all(),
        slug_field='name'
    )
    status = serializers.SlugRelatedField(
        queryset=Status.objects.all(),
        slug_field='status'
    )
    brand = serializers.SlugRelatedField(
        queryset=BrandCars.objects.all(),
        slug_field='title'  # Предполагается, что у модели BrandCars есть поле name
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='title'  # Предполагается, что у модели Category есть поле name
    )

    class Meta:
        model = Car
        fields = (
            'id', 'title', 'price_day', 'img_front', 'volume', 'power',
            'fuel_type', 'gearbox', 'type_car_body', 'brand', 'category',
            'status', 'year'
        )


class CarDetailSerializer(serializers.ModelSerializer):
    fuel_type = serializers.SlugRelatedField(
        queryset=FuelType.objects.all(),
        slug_field='title'
    )
    gearbox = serializers.SlugRelatedField(
        queryset=Gearbox.objects.all(),
        slug_field='title'
    )
    type_car_body = serializers.SlugRelatedField(
        queryset=CarBodyType.objects.all(),
        slug_field='name'
    )
    status = serializers.SlugRelatedField(
        queryset=Status.objects.all(),
        slug_field='status'
    )
    brand = serializers.SlugRelatedField(
        queryset=BrandCars.objects.all(),
        slug_field='title'  # Предполагается, что у модели BrandCars есть поле name
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='title'  # Предполагается, что у модели Category есть поле name
    )

    class Meta:
        model = Car
        fields = (
            'id', 'title', 'price_day', 'img_front', 'img_back', 'salon', 'volume', 'power',
            'fuel_type', 'gearbox', 'type_car_body', 'brand', 'category',
            'status', 'year'
        )

    def create(self, validated_data):
        return Car.objects.create(**validated_data)


class RentalSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    car = serializers.PrimaryKeyRelatedField(queryset=Car.objects.all())

    class Meta:
        model = Rental
        fields = ('user', 'car', 'start_date', 'number', 'end_date', 'total_cost', 'status')
        read_only_fields = ('total_cost', 'status')

    def validate(self, attrs):
        if 'car' in self.initial_data:
            car_id = self.initial_data['car']
            car = Car.objects.get(id=car_id)
            if car.status == 1:
                raise serializers.ValidationError("Этот автомобиль уже забронирован.")
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        car = validated_data.get('car')
        start_date = validated_data.get('start_date')
        end_date = validated_data.get('end_date')

        if car.status == 1:
            raise serializers.ValidationError("Этот автомобиль уже забронирован.")

        total_days = (end_date - start_date).days

        discount_rate = 0
        if total_days >= 20:
            discount_rate = 0.20
        elif total_days >= 10:
            discount_rate = 0.10
        elif total_days >= 5:
            discount_rate = 0.05

        base_cost = total_days * car.price_day
        discount_amount = base_cost * discount_rate
        total_cost = base_cost - discount_amount

        rental = Rental.objects.create(
            user=user,
            car=car,
            start_date=start_date,
            end_date=end_date,
            total_cost=total_cost
        )

        car.status = 1
        car.save(update_fields=['status'])
        rental.status = 1
        rental.save(update_fields=['status'])

        return rental


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class SiteCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = SiteComment
        fields = ['id', 'author', 'text', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get("email")  # Используем email для логина
        password = attrs.get("password")

        user = User.objects.filter(email=username).first()
        if user and user.check_password(password):
            return super().validate(attrs)
        else:
            raise serializers.ValidationError("No active account found with the given credentials")

