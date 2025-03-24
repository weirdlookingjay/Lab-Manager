import Cookies from 'js-cookie';

const API_BASE_URL = 'http://localhost:8000';

interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

export async function fetchWithAuth(url: string, options: FetchOptions = {}) {
  const { skipAuth = false, ...fetchOptions } = options;
  
  // Get the token from cookies
  const token = Cookies.get('token');
  
  // Prepare headers
  const headers = new Headers(fetchOptions.headers || {});
  
  // Add auth header if token exists and auth is not skipped
  if (token && !skipAuth) {
    headers.set('Authorization', `Token ${token}`); 
  }
  
  // Add default headers
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  // Ensure URL has trailing slash for Django
  const fullUrl = `${API_BASE_URL}${url}${url.endsWith('/') ? '' : '/'}`;
  
  // Make the request
  const response = await fetch(fullUrl, {
    ...fetchOptions,
    headers,
    credentials: 'include', // Include cookies
  });
  
  // Handle 401 Unauthorized by redirecting to login
  if (response.status === 401) {
    // Clear auth state
    Cookies.remove('token');
    Cookies.remove('user');
    
    // Redirect to login
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  
  return response;
}

export default fetchWithAuth;
