from django.db.models import Count
from .permissions import IsAdminUser
from django.db.models import Q
from django.db import transaction
from .models import KBEntry, QueryLog
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Company


# 🔐 Helper function to generate JWT
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
    }


# ✅ REGISTER API
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        company_name = request.data.get('company_name')

        # Check if user exists
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )

        # Get company (created via signal)
        company = user.company
        company.company_name = company_name
        company.save()

        # Generate token
        tokens = get_tokens_for_user(user)

        return Response({
            "username": user.username,
            "company_name": company.company_name,
            "api_key": company.api_key,
            "access": tokens['access']
        }, status=status.HTTP_201_CREATED)


# ✅ LOGIN API
class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        tokens = get_tokens_for_user(user)
        company = user.company

        return Response({
            "access": tokens['access'],
            "company_name": company.company_name,
            "api_key": company.api_key
        }, status=status.HTTP_200_OK)

class QueryKBView(APIView):

    def post(self, request):
        search_term = request.data.get('search')

        # ❌ If search missing
        if not search_term:
            return Response(
                {"error": "Search field is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        company = request.user.company

        # ✅ Atomic transaction
        with transaction.atomic():

            # 🔍 Search query
            results = KBEntry.objects.filter(
                Q(question__icontains=search_term) |
                Q(answer__icontains=search_term)
            )

            count = results.count()

            # 📝 Log query
            QueryLog.objects.create(
                company=company,
                search_term=search_term,
                results_count=count
            )

        # ✅ Prepare response
        data = []
        for item in results:
            data.append({
                "id": item.id,
                "question": item.question,
                "answer": item.answer,
                "category": item.category
            })

        return Response({
            "search": search_term,
            "count": count,
            "results": data
        }, status=status.HTTP_200_OK)

class UsageSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):

        # 🔢 Total queries
        total_queries = QueryLog.objects.aggregate(
            total=Count('id')
        )['total']

        # 🏢 Active companies
        active_companies = QueryLog.objects.values('company').distinct().count()

        # 🔝 Top search terms
        top_search_terms = QueryLog.objects.values('search_term') \
            .annotate(count=Count('id')) \
            .order_by('-count')[:5]

        return Response({
            "total_queries": total_queries,
            "active_companies": active_companies,
            "top_search_terms": top_search_terms
        })