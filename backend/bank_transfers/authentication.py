from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Company, CompanyUser, UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Felhasználó regisztráció serializer"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    company_name = serializers.CharField(max_length=200)
    company_tax_id = serializers.CharField(max_length=20)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 
                 'password', 'password_confirm', 'company_name', 'company_tax_id']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("A jelszavak nem egyeznek.")
        
        # Check if company with this tax_id already exists
        if Company.objects.filter(tax_id=attrs['company_tax_id']).exists():
            raise serializers.ValidationError("Ezzel az adószámmal már létezik cég.")
        
        return attrs
    
    def create(self, validated_data):
        # Remove password_confirm and company data
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        company_name = validated_data.pop('company_name')
        company_tax_id = validated_data.pop('company_tax_id')
        
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                password=password,
                **validated_data
            )
            
            # Create company
            company = Company.objects.create(
                name=company_name,
                tax_id=company_tax_id
            )
            
            # Create company user relationship with admin role
            CompanyUser.objects.create(
                user=user,
                company=company,
                role='ADMIN'
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                last_active_company=company
            )
            
            return user


class CustomTokenObtainPairSerializer(serializers.Serializer):
    """Egyedi token szerző serializer céges adatokkal"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('A felhasználói fiók inaktív.')
                
                # Get user's companies
                company_memberships = CompanyUser.objects.filter(
                    user=user, is_active=True
                ).select_related('company')
                
                if not company_memberships.exists():
                    raise serializers.ValidationError('A felhasználónak nincs aktív céges tagsága.')
                
                attrs['user'] = user
                attrs['companies'] = company_memberships
                return attrs
            else:
                raise serializers.ValidationError('Hibás felhasználónév vagy jelszó.')
        else:
            raise serializers.ValidationError('Meg kell adni a felhasználónevet és jelszót.')


class CompanySerializer(serializers.ModelSerializer):
    """Cég serializer"""
    user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'tax_id', 'address', 'phone', 'email', 'user_role']
    
    def get_user_role(self, obj):
        user = self.context.get('user')
        if user:
            membership = CompanyUser.objects.filter(user=user, company=obj).first()
            return membership.role if membership else None
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Felhasználói profil serializer"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'first_name', 'last_name', 
                 'phone', 'preferred_language', 'timezone', 'last_active_company']


class AuthenticationViewSet(GenericViewSet):
    """Autentikációs végpontok"""
    
    @swagger_auto_schema(
        operation_description="Felhasználó regisztráció",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Új felhasználó és cég regisztrációja"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Sikeres regisztráció',
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Bejelentkezés",
        request_body=CustomTokenObtainPairSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'companies': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                }
            )
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Bejelentkezés és token generálás"""
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            companies = serializer.validated_data['companies']
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Serialize companies
            company_serializer = CompanySerializer(
                [membership.company for membership in companies], 
                many=True, 
                context={'user': user}
            )
            
            # Get user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile_serializer = UserProfileSerializer(profile)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': profile_serializer.data,
                'companies': company_serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Aktív cég váltása",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'company_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        )
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def switch_company(self, request):
        """Aktív cég váltása"""
        company_id = request.data.get('company_id')
        
        if not company_id:
            return Response({'error': 'company_id szükséges'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user has access to this company
        try:
            membership = CompanyUser.objects.get(
                user=request.user,
                company_id=company_id,
                is_active=True
            )
        except CompanyUser.DoesNotExist:
            return Response({'error': 'Nincs jogosultság ehhez a céghez'}, status=status.HTTP_403_FORBIDDEN)
        
        # Update user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.last_active_company = membership.company
        profile.save()
        
        return Response({
            'message': 'Aktív cég megváltoztatva',
            'company': CompanySerializer(membership.company, context={'user': request.user}).data
        })
    
    @swagger_auto_schema(
        operation_description="Felhasználói profil lekérése"
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Felhasználói profil lekérése"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        
        # Get user's companies
        companies = CompanyUser.objects.filter(
            user=request.user, is_active=True
        ).select_related('company')
        company_serializer = CompanySerializer(
            [membership.company for membership in companies], 
            many=True, 
            context={'user': request.user}
        )
        
        return Response({
            'user': serializer.data,
            'companies': company_serializer.data
        })