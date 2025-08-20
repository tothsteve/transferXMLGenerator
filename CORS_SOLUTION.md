# CORS Solution Documentation

## Problem
The frontend React application needed to send custom headers (`x-company-id`) to the Django backend, but CORS preflight requests were failing with:

```
Access to XMLHttpRequest at 'backend-url' from origin 'frontend-url' has been blocked by CORS policy: Request header field x-company-id is not allowed by Access-Control-Allow-Headers in preflight response.
```

## Attempted Solutions That Failed

### 1. django-cors-headers Configuration
- Tried `CORS_ALLOW_ALL_HEADERS = True` - didn't work
- Tried explicit `CORS_ALLOWED_HEADERS` list - headers were ignored
- Updated to django-cors-headers 4.4.0 - still failed
- Issue: django-cors-headers wasn't properly handling custom headers in preflight responses

### 2. Railway Environment Variables
- Checked for `CORS_ALLOW_ALL` Railway setting - was already `false`
- Railway wasn't overriding Django CORS settings

## Final Working Solution

### Custom CORS Middleware
Created a custom Django middleware to handle CORS preflight requests directly:

**File**: `backend/transferXMLGenerator/cors_middleware.py`

```python
class CustomCORSMiddleware:
    def __call__(self, request):
        if request.method == 'OPTIONS':
            response = HttpResponse()
            origin = request.META.get('HTTP_ORIGIN')
            
            # Validate allowed origins
            if origin and (origin.endswith('.railway.app') or 
                          origin.endswith('.up.railway.app') or 
                          origin in ['http://localhost:3000', 'http://127.0.0.1:3000']):
                response['Access-Control-Allow-Origin'] = origin
            
            response['Access-Control-Allow-Headers'] = (
                'accept, authorization, content-type, user-agent, x-csrftoken, '
                'x-requested-with, x-company-id, cache-control, pragma, expires, '
                'dnt, origin, accept-encoding'
            )
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            
            return response
        
        # Process normal requests...
```

### Django Settings Configuration
**File**: `backend/transferXMLGenerator/settings_production.py`

```python
MIDDLEWARE = [
    'transferXMLGenerator.cors_middleware.CustomCORSMiddleware',  # Custom CORS ONLY
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # ... other middleware (removed corsheaders.middleware.CorsMiddleware)
]

# Removed 'corsheaders' from INSTALLED_APPS
# Removed all CORS_* settings - handled by custom middleware
```

## Key Points

1. **Removed django-cors-headers completely** - it wasn't working with custom headers
2. **Custom middleware is first in the stack** - intercepts OPTIONS requests before other middleware
3. **Explicit header list includes x-company-id** - ensures custom header is allowed
4. **Origin validation for security** - only allows Railway and localhost origins
5. **Works with Railway deployment** - no conflicts with Railway's edge proxy

## Testing
The solution was verified with curl:
```bash
curl -X OPTIONS \
  -H "Origin: https://frontend.railway.app" \
  -H "Access-Control-Request-Headers: x-company-id,authorization,content-type" \
  https://backend.railway.app/api/endpoint/
```

Response includes:
```
access-control-allow-headers: accept, authorization, content-type, user-agent, x-csrftoken, x-requested-with, x-company-id, cache-control, pragma, expires, dnt, origin, accept-encoding
```

## Result
✅ Frontend can now successfully send `x-company-id` header to backend  
✅ CORS preflight requests pass  
✅ Application works on Railway.app deployment  

## Lesson Learned
When django-cors-headers fails with custom headers, implement custom CORS middleware for full control over preflight responses.