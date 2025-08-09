from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

# Swagger imports
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Transfer XML Generator API",
        default_version='v1',
        description="""
        Bank Transfer XML Generator API
        
        ## Főbb funkciók:
        - **Kedvezményezettek kezelése** (CRUD)
        - **Utalási sablonok** létrehozása és kezelése
        - **Utalások** létrehozása és XML generálás
        - **Excel import** kedvezményezettek tömeges feltöltéséhez
        - **Köteg kezelés** több utalás egyszerre
        
        ## Munkafolyamat:
        1. Kedvezményezettek feltöltése (Excel vagy kézi)
        2. Sablonok létrehozása gyakori utalási ciklusokhoz
        3. Sablon betöltése → szerkesztés → XML generálás
        """,
        terms_of_service="https://www.yourcompany.com/terms/",
        contact=openapi.Contact(email="developer@yourcompany.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('bank_transfers.api_urls')),
    
    # Swagger Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-docs'),  # Alias
    
    # Régi template URLs (opcionális)
    # path('', include('bank_transfers.urls')),
]

# Static files (development)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

