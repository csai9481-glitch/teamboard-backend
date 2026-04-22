from django.urls import path
from .views import RegisterView, LoginView
from .views import QueryKBView
from .views import UsageSummaryView

urlpatterns = [
    path('auth/register/', RegisterView.as_view()),
    path('auth/login/', LoginView.as_view()),
    path('kb/query/', QueryKBView.as_view()),
    path('admin/usage-summary/', UsageSummaryView.as_view()),
]