import axios, { AxiosResponse, InternalAxiosRequestConfig } from 'axios';

interface TokenRefreshResponse {
  access: string;
  refresh?: string;
}

class TokenManager {
  private static instance: TokenManager;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (error?: any) => void;
  }> = [];

  public static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager();
    }
    return TokenManager.instance;
  }

  private processQueue(error: any, token: string | null = null) {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error);
      } else {
        resolve(token);
      }
    });

    this.failedQueue = [];
  }

  public setupInterceptors(
    onTokenRefresh: (accessToken: string, refreshToken?: string) => void,
    onLogout: () => void,
    axiosInstance: any = axios
  ) {
    console.log('🔧 Setting up interceptors on axios instance');
    
    // Request interceptor to add auth header
    axiosInstance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('accessToken');
        console.log('🔑 TokenManager interceptor - token exists:', !!token);
        console.log('🔑 Request URL:', config.url);
        
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
          console.log('✅ Added Authorization header');
          
          // Add company header if available
          const currentCompany = localStorage.getItem('currentCompany');
          if (currentCompany) {
            try {
              const company = JSON.parse(currentCompany);
              config.headers['X-Company-ID'] = company.id.toString();
              console.log('✅ Added X-Company-ID header:', company.id);
            } catch (error) {
              console.error('Error parsing current company:', error);
            }
          } else {
            console.log('⚠️ No currentCompany in localStorage');
          }
        } else {
          console.log('❌ No token or headers available');
        }
        return config;
      },
      (error: any) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle token refresh
    axiosInstance.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      async (error: any) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // If we're already refreshing, queue this request
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            }).then((token) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`;
              }
              return axiosInstance(originalRequest);
            }).catch((err) => {
              return Promise.reject(err);
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          const refreshToken = localStorage.getItem('refreshToken');

          if (!refreshToken) {
            this.processQueue(error, null);
            onLogout();
            return Promise.reject(error);
          }

          try {
            const response = await axios.post<TokenRefreshResponse>(
              '/api/auth/token/refresh/',
              { refresh: refreshToken }
            );

            const { access, refresh } = response.data;
            
            // Update tokens
            localStorage.setItem('accessToken', access);
            if (refresh) {
              localStorage.setItem('refreshToken', refresh);
            }

            // Notify auth context
            onTokenRefresh(access, refresh);

            // Update original request header
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access}`;
            }

            // Process queued requests
            this.processQueue(null, access);

            return axiosInstance(originalRequest);
          } catch (refreshError) {
            this.processQueue(refreshError, null);
            onLogout();
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  public clearTokens() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userData');
    localStorage.removeItem('companiesData');
    localStorage.removeItem('currentCompany');
  }

  public getAccessToken(): string | null {
    return localStorage.getItem('accessToken');
  }

  public getRefreshToken(): string | null {
    return localStorage.getItem('refreshToken');
  }

  public setTokens(accessToken: string, refreshToken: string) {
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
  }
}

export default TokenManager;