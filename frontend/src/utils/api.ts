const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface RequestOptions extends RequestInit {
  token?: string;
  skipAuth?: boolean;
}

const getStoredToken = (key: string): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(key);
  }
  return null;
};

const setStoredToken = (key: string, value: string | null) => {
  if (typeof window !== 'undefined') {
    if (value) {
      localStorage.setItem(key, value);
    } else {
      localStorage.removeItem(key);
    }
  }
};

export const getAccessToken = () => getStoredToken('access_token');
export const setAccessToken = (token: string | null) => setStoredToken('access_token', token);
export const getRefreshToken = () => getStoredToken('refresh_token');
export const setRefreshToken = (token: string | null) => setStoredToken('refresh_token', token);

export const clearTokens = () => {
  setAccessToken(null);
  setRefreshToken(null);
};

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

const onRefreshed = (token: string) => {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
};

const addRefreshSubscriber = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb);
};

async function handleTokenRefresh(): Promise<string> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    clearTokens();
    throw new Error('Session expired, please login again.');
  }

  const data = await res.json();
  setAccessToken(data.access_token);
  setRefreshToken(data.refresh_token);
  return data.access_token;
}

export async function apiRequest(path: string, options: RequestOptions = {}): Promise<any> {
  const url = `${API_URL}${path}`;
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (!options.skipAuth) {
    const token = getAccessToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }

  const fetchOptions = {
    ...options,
    headers,
  };

  const response = await fetch(url, fetchOptions);

  if (response.status === 401 && !options.skipAuth) {
    // If we're already refreshing, queue this request
    if (isRefreshing) {
      return new Promise((resolve) => {
        addRefreshSubscriber((newToken) => {
          headers.set('Authorization', `Bearer ${newToken}`);
          resolve(fetch(url, { ...options, headers }).then((res) => res.json()));
        });
      });
    }

    isRefreshing = true;

    try {
      const newAccessToken = await handleTokenRefresh();
      isRefreshing = false;
      onRefreshed(newAccessToken);

      // Retry the original request
      headers.set('Authorization', `Bearer ${newAccessToken}`);
      const retryResponse = await fetch(url, { ...options, headers });
      if (!retryResponse.ok) {
        throw new Error(`Retry request failed with status: ${retryResponse.status}`);
      }
      return await retryResponse.json();
    } catch (refreshErr) {
      isRefreshing = false;
      clearTokens();
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('auth_session_expired'));
      }
      throw refreshErr;
    }
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    let errorMessage = `Request failed with status ${response.status}`;
    
    if (errorBody && errorBody.detail) {
      if (Array.isArray(errorBody.detail)) {
        errorMessage = errorBody.detail
          .map((err: any) => {
            if (typeof err === 'object' && err !== null) {
              const field = err.loc ? err.loc.filter((l: any) => l !== 'body').join('.') : '';
              return field ? `${field}: ${err.msg}` : err.msg || JSON.stringify(err);
            }
            return String(err);
          })
          .join(', ');
      } else if (typeof errorBody.detail === 'object' && errorBody.detail !== null) {
        errorMessage = errorBody.detail.message || errorBody.detail.detail || JSON.stringify(errorBody.detail);
      } else {
        errorMessage = String(errorBody.detail);
      }
    }
    
    throw new Error(errorMessage);
  }

  // Handle empty response bodies (like 204 No Content)
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  get: (path: string, options?: RequestOptions) => apiRequest(path, { ...options, method: 'GET' }),
  post: (path: string, body: any, options?: RequestOptions) =>
    apiRequest(path, {
      ...options,
      method: 'POST',
      body: body instanceof FormData || body instanceof URLSearchParams ? body : JSON.stringify(body),
    }),
  put: (path: string, body: any, options?: RequestOptions) =>
    apiRequest(path, {
      ...options,
      method: 'PUT',
      body: body instanceof FormData || body instanceof URLSearchParams ? body : JSON.stringify(body),
    }),
  delete: (path: string, options?: RequestOptions) => apiRequest(path, { ...options, method: 'DELETE' }),
};
