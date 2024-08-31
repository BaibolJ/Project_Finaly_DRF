from django_filters.rest_framework import DjangoFilterBackend
from .filters import CarFilter
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, permissions, status, viewsets, mixins
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg import openapi
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from .serializers import *
from .models import *
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .filters import CarFilter
from rest_framework.pagination import PageNumberPagination
from .permissions import IsAuthorOrReadOnly
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.views.decorators.csrf import csrf_exempt
import random
from django.http import HttpResponseRedirect
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, SAFE_METHODS

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD  # Убедитесь, что поле email используется для аутентификации

    def validate(self, attrs):
        # Убедитесь, что email передается вместо username
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("No active account found with the given credentials")

            if not user.check_password(password):
                raise serializers.ValidationError("No active account found with the given credentials")

            if not user.is_active:
                raise serializers.ValidationError("No active account found with the given credentials")

            attrs['email'] = email
            attrs['username'] = user.username  # Убедитесь, что в attrs передается username для токена
            return super().validate(attrs)
        else:
            raise serializers.ValidationError("Must include email and password.")


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        # Разрешить доступ только администраторам и менеджерам
        if request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', None) in ['admin', 'manager']):
            return True
        return False


class IsAdminOrManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Разрешить безопасные методы (GET, HEAD, OPTIONS) всем пользователям
        if request.method in SAFE_METHODS:
            return True
        # Разрешить только администраторам и менеджерам для других методов
        return request.user and (request.user.is_superuser or getattr(request.user, 'is_staff', False))


class IsAuthenticatedUser(BasePermission):
    def has_permission(self, request, view):
        # Проверка на аутентификацию пользователя
        return request.user.is_authenticated


class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarDetailSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    @action(detail=True, methods=['get', 'post', 'patch', 'delete'], permission_classes=[IsAuthenticatedUser])
    def details(self, request, pk=None):
        """
        GET: Get car details, comments, and ratings.
        POST: Add comment or rating.
        PATCH: Update comment or rating.
        DELETE: Delete comment or rating.
        """
        car = self.get_object()

        if request.method == 'GET':
            # Детали автомобиля
            car_serializer = CarDetailSerializer(car)

            # Комментарии к автомобилю
            comments = Comment.objects.filter(car=car)
            comment_serializer = CommentSerializer(comments, many=True)

            # Рейтинги автомобиля
            ratings = Rating.objects.filter(car=car)
            if ratings.exists():
                avg_rating = sum(r.stars for r in ratings) / ratings.count()
            else:
                avg_rating = None

            data = {
                'car': car_serializer.data,
                'comments': comment_serializer.data,
                'average_rating': avg_rating
            }

            return Response(data)

        elif request.method == 'POST':
            if 'text' in request.data:
                # Если есть текст, значит это комментарий
                serializer = CommentSerializer(data=request.data, context={'request': request})
                if serializer.is_valid():
                    serializer.save(user=request.user, car=car)
                    return Response(serializer.data, status=201)
                return Response(serializer.errors, status=400)
            elif 'stars' in request.data:
                # Если есть поле stars, значит это рейтинг
                serializer = RatingSerializer(data=request.data, context={'request': request})
                if serializer.is_valid():
                    serializer.save(user=request.user, car=car)
                    return Response(serializer.data, status=201)
                return Response(serializer.errors, status=400)

        elif request.method == 'PATCH':
            if 'comment_id' in request.data:
                # Редактирование комментария
                comment = get_object_or_404(Comment, id=request.data['comment_id'], user=request.user, car=car)
                serializer = CommentSerializer(comment, data=request.data, partial=True, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=400)
            elif 'rating_id' in request.data:
                # Редактирование рейтинга
                rating = get_object_or_404(Rating, id=request.data['rating_id'], user=request.user, car=car)
                serializer = RatingSerializer(rating, data=request.data, partial=True, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=400)

        elif request.method == 'DELETE':
            if 'comment_id' in request.data:
                # Удаление комментария
                comment = get_object_or_404(Comment, id=request.data['comment_id'], user=request.user, car=car)
                comment.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            elif 'rating_id' in request.data:
                # Удаление рейтинга
                rating = get_object_or_404(Rating, id=request.data['rating_id'], user=request.user, car=car)
                rating.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

        return Response({'error': 'Invalid request'}, status=400)


# class CommentListCreateView(generics.ListCreateAPIView):
#     serializer_class = CommentSerializer
#     # permission_classes = [permissions.IsAuthenticated]
#
#     # def perform_create(self, serializer):
#     #     car_id = self.kwargs['car_id']
#     #     serializer.save(user=self.request.user, car_id=car_id)
#     #
#     # def get_queryset(self):
#     #     car_id = self.kwargs['car_id']
#     #     return CommentToObjects.objects.filter(car_id=car_id)


# class RatingCreateView(generics.CreateAPIView):
#     queryset = Rating.objects.all()
#     serializer_class = RatingSerializer
#     permission_classes = [permissions.IsAuthenticated]

# ----------------------------------------------------


class RentalCreateView(generics.CreateAPIView):
    queryset = Rental.objects.all()
    serializer_class = RentalSerializer


class RentalUpdateView(generics.UpdateAPIView):
    queryset = Rental.objects.all()
    serializer_class = RentalSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": serializer.data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class CarPagination(PageNumberPagination):
    page_size = 12  # Количество объектов на одной странице
    page_size_query_param = 'page_size'
    max_page_size = 12  # Максимальное количество объектов на страниц


class CarListView(generics.ListCreateAPIView):
    queryset = Car.objects.all()
    serializer_class = CarIndexSerializers
    filter_backends = [DjangoFilterBackend]
    filterset_class = CarFilter
    pagination_class = CarPagination
    permission_classes = [IsAdminOrManagerOrReadOnly]  # Используем кастомное разрешение

    def perform_create(self, serializer):
        # Если вам нужно выполнить дополнительные действия при создании, делайте это здесь
        serializer.save()

    @method_decorator(cache_page(60 * 15))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CarRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Car.objects.all()
    serializer_class = CarDetailSerializer  # Используйте CarDetailSerializer, если требуется более детализированная информация
    permission_classes = [IsAdminOrManager]  # Используем кастомное разрешение

    def get_serializer_context(self):
        context = super().get_serializer_context()
        car = self.get_object()
        ratings = car.ratings.all()
        if ratings:
            avg_rating = sum(r.stars for r in ratings) / ratings.count()
        else:
            avg_rating = None
        context['avg_rating'] = avg_rating
        return context


# class CategoryListView(generics.ListAPIView):
#     queryset = Category.objects.all()
#     serializer_class = CarCategorySerializers
#
#     @method_decorator(cache_page(60 * 15))
#     def get(self, request, *args, **kwargs):
#         return super().get(request, *args, **kwargs)


class CreateRentalView(generics.CreateAPIView):
    queryset = Rental.objects.all()
    serializer_class = RentalSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rental = serializer.save()
        rental.calculate_total_cost()
        rental.car.status = 1
        rental.car.save()

        return Response({
            "message": "Автомобиль успешно забронирован.",
            "rental": serializer.data
        }, status=status.HTTP_201_CREATED)


class IsAuthorOrReadOnlyComment(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Разрешаем доступ к объекту только если пользователь является автором
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


class SiteCommentListCreateView(generics.ListCreateAPIView):
    queryset = SiteComment.objects.all().order_by('-created_at')
    serializer_class = SiteCommentSerializer
    permission_classes = [IsAuthorOrReadOnlyComment]

    def perform_create(self, serializer):
        user = self.request.user
        # Проверяем, есть ли уже комментарий от этого пользователя
        if SiteComment.objects.filter(author=user).exists():
            # Если комментарий уже существует, возвращаем ошибку
            raise serializers.ValidationError("Извините но писать отзыв можно только один раз")
        serializer.save(author=user)


class CarIndexView(APIView):

    @swagger_auto_schema(
        operation_description="Получить категории и топ 10 машин",
        responses={200: openapi.Response('OK', CarIndexSerializers(many=True))},

    )
    def get(self, request):
        # Получение всех категорий
        categories = Category.objects.all()
        # Получение топ 10 машин
        cars = Car.objects.order_by('?')[:10]
        # Получение всех комментариев
        comments = list(SiteComment.objects.all())
        random_comments = random.sample(comments, min(4, len(comments)))

        category_serializers = CarCategorySerializers(categories, many=True)
        car_serializers = CarIndexSerializers(cars, many=True)
        comment_serializers = SiteCommentSerializer(random_comments, many=True)

        data = {
            "categories": category_serializers.data,
            "cars": car_serializers.data,
            "comments": comment_serializers.data
        }

        return Response(data)



