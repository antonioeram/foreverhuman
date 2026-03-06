/**
 * API client — axios cu JWT interceptor + refresh token rotation
 */
import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import * as SecureStore from 'expo-secure-store';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'https://clinic.foreverhuman.health/api/v1';

const TOKEN_KEY = 'fh_access_token';
const REFRESH_KEY = 'fh_refresh_token';

// ---------------------------------------------------------------------------
// Token storage (SecureStore — iOS Keychain / Android Keystore)
// ---------------------------------------------------------------------------
export const tokenStorage = {
  getAccess:     () => SecureStore.getItemAsync(TOKEN_KEY),
  getRefresh:    () => SecureStore.getItemAsync(REFRESH_KEY),
  setAccess:     (t: string) => SecureStore.setItemAsync(TOKEN_KEY, t),
  setRefresh:    (t: string) => SecureStore.setItemAsync(REFRESH_KEY, t),
  clearAll:      () => Promise.all([
    SecureStore.deleteItemAsync(TOKEN_KEY),
    SecureStore.deleteItemAsync(REFRESH_KEY),
  ]),
};

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — adaugă access token
api.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const token = await tokenStorage.getAccess();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — refresh automat la 401
let isRefreshing = false;
let failedQueue: Array<{ resolve: Function; reject: Function }> = [];

const processQueue = (error: Error | null, token: string | null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(token);
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          original.headers.Authorization = `Bearer ${token}`;
          return api(original);
        });
      }

      original._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = await tokenStorage.getRefresh();
        const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        await tokenStorage.setAccess(data.access_token);
        await tokenStorage.setRefresh(data.refresh_token);

        processQueue(null, data.access_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch (refreshError) {
        processQueue(refreshError as Error, null);
        await tokenStorage.clearAll();
        // TODO: redirect la login screen (via navigation)
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// ---------------------------------------------------------------------------
// API methods
// ---------------------------------------------------------------------------
export const authAPI = {
  login:   (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  logout:  () => api.post('/auth/logout'),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
};

export const chatAPI = {
  sendMessage: (patientId: string, message: string, sessionId?: string) =>
    api.post(`/chat/${patientId}/message`, { message, session_id: sessionId }),
  getHistory: (patientId: string, limit = 50) =>
    api.get(`/chat/${patientId}/history`, { params: { limit } }),
};

export const analysesAPI = {
  uploadPDF:    (patientId: string, file: FormData) =>
    api.post(`/analyses/${patientId}/upload`, file, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getBiomarkers: (patientId: string, name?: string) =>
    api.get(`/analyses/${patientId}/biomarkers`, { params: { name } }),
  getTrend:     (patientId: string, biomarkerName: string) =>
    api.get(`/analyses/${patientId}/biomarkers/${biomarkerName}/trend`),
};

export const sensorsAPI = {
  getLatest: (patientId: string, metrics?: string[]) =>
    api.get(`/sensors/${patientId}/latest`, { params: { metrics: metrics?.join(',') } }),
  getTrend:  (patientId: string, metric: string, fromDate?: string, toDate?: string) =>
    api.get(`/sensors/${patientId}/trend`, { params: { metric, from_date: fromDate, to_date: toDate } }),
};
