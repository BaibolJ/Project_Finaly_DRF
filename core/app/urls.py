from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .views import RegisterView, UserProfileView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'cars', CarViewSet, basename='car')

urlpatterns = [
    path('index/', CarIndexView.as_view()),
    path('cars/', CarListView.as_view(), name='car-list'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('cars/<int:pk>/', CarRetrieveUpdateDestroyView.as_view(), name='car-detail'),
    path('rentals/', CreateRentalView.as_view(), name='create-rental'),
    path('rentals/create/', RentalCreateView.as_view(), name='rental-create'),
    path('rentals/<int:pk>/update/', RentalUpdateView.as_view(), name='rental-update'),
    path('comments/', SiteCommentListCreateView.as_view(), name='comment-list-create'),
    path('', include(router.urls)),  # включение маршрутов из router
    # path('ratings/create/', RatingCreateView.as_view(), name='rating-create'),
    # path('categories/', CategoryListView.as_view(), name='category-list'),
]
