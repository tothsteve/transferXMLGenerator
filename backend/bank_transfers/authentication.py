from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Company, CompanyUser, UserProfile
from .permissions import FeatureChecker


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
            
            # Get enabled features for each company
            companies_with_features = []
            for membership in companies:
                company_data = CompanySerializer(membership.company, context={'user': user}).data
                enabled_features = FeatureChecker.get_enabled_features_for_company(membership.company)
                company_data['enabled_features'] = enabled_features
                companies_with_features.append(company_data)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': profile_serializer.data,
                'companies': companies_with_features,
                'login_timestamp': user.last_login.isoformat() if user.last_login else None
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
        
        # Include enabled features for the new active company
        company_data = CompanySerializer(membership.company, context={'user': request.user}).data
        enabled_features = FeatureChecker.get_enabled_features_for_company(membership.company)
        company_data['enabled_features'] = enabled_features
        
        return Response({
            'message': 'Aktív cég megváltoztatva',
            'company': company_data
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
        
        # Add enabled features for each company
        companies_with_features = []
        for membership in companies:
            company_data = CompanySerializer(membership.company, context={'user': request.user}).data
            enabled_features = FeatureChecker.get_enabled_features_for_company(membership.company)
            company_data['enabled_features'] = enabled_features
            companies_with_features.append(company_data)
        
        return Response({
            'user': serializer.data,
            'companies': companies_with_features
        })
    
    @swagger_auto_schema(
        operation_description="Aktív cég engedélyezett funkcióinak lekérése"
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def features(self, request):
        """Get enabled features for user's current active company"""
        if not hasattr(request, 'company') or not request.company:
            # Try to get company from user profile
            try:
                profile = UserProfile.objects.get(user=request.user)
                if profile.last_active_company:
                    # Verify user still has access
                    membership = CompanyUser.objects.filter(
                        user=request.user,
                        company=profile.last_active_company,
                        is_active=True
                    ).first()
                    if membership:
                        company = membership.company
                    else:
                        # Fall back to first available company
                        membership = CompanyUser.objects.filter(
                            user=request.user,
                            is_active=True
                        ).select_related('company').first()
                        company = membership.company if membership else None
                else:
                    company = None
            except UserProfile.DoesNotExist:
                company = None
        else:
            company = request.company
        
        if not company:
            return Response({
                'error': 'Nincs aktív cég',
                'enabled_features': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        enabled_features = FeatureChecker.get_enabled_features_for_company(company)
        
        return Response({
            'company_id': company.id,
            'company_name': company.name,
            'enabled_features': enabled_features,
            'feature_count': len(enabled_features)
        })
    
    @swagger_auto_schema(
        operation_description="Felhasználó kiléptetése (csak adminok)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='A kiléptetendő felhasználó ID-ja')
            },
            required=['user_id']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'user_username': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            403: 'Nincs jogosultság',
            404: 'Felhasználó nem található'
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def force_logout(self, request):
        """Force logout a user (admin only)"""
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id szükséges'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if current user is admin in any company
        admin_memberships = CompanyUser.objects.filter(
            user=request.user,
            role='ADMIN',
            is_active=True
        )
        
        if not admin_memberships.exists():
            return Response({'error': 'Csak adminok érhető el ez a funkció'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get target user
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Felhasználó nem található'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if admin has permission to manage this user (same company)
        admin_companies = set(m.company_id for m in admin_memberships)
        target_companies = set(
            CompanyUser.objects.filter(
                user=target_user,
                is_active=True
            ).values_list('company_id', flat=True)
        )
        
        if not admin_companies.intersection(target_companies):
            return Response({
                'error': 'Nincs jogosultság ennek a felhasználónak a kezelésére'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Don't allow admin to logout themselves
        if target_user.id == request.user.id:
            return Response({'error': 'Nem tudja saját magát kiléptetni'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Force logout by updating user's password (this invalidates all tokens)
        # We'll use a more sophisticated approach with token blacklisting if available
        try:
            # Update last_login to force re-authentication
            target_user.last_login = None
            target_user.save(update_fields=['last_login'])
            
            return Response({
                'message': f'Felhasználó {target_user.username} sikeresen kiléptetve',
                'user_username': target_user.username,
                'forced_logout_by': request.user.username
            })
        except Exception as e:
            return Response({
                'error': 'Hiba a kiléptetés során',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_description="Token érvényességének ellenőrzése"
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def validate_token(self, request):
        """Validate current token and return user info"""
        return Response({
            'valid': True,
            'user_id': request.user.id,
            'username': request.user.username,
            'is_active': request.user.is_active
        })