import axios from 'axios';

// Create an axios instance with default configuration
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1', // Adjust based on your API gateway setup
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors like 401 (unauthorized) or 403 (forbidden)
    if (error.response) {
      if (event.response.status === 401) {
        // Redirect to login or refresh token
        // For now, we'll just log it
        console.warn('Unauthorized access');
      }
    }
    return Promise.reject(error);
  }
);

// Export specific service functions
export const forecastAPI = {
  getForecasts: (params?: any) => apiClient.get('/forecasts', { params }),
  getForecast: (id: string) => apiClient.get(`/forecasts/${id}`),
  generateForecast: (data: any) => apiClient.post('/forecasts/generate', data),
  getForecastAccuracy: (productId: string, params?: any) =>
    apiClient.get(`/forecasts/${productId}/accuracy`, { params }),
  trainModel: (data: any) => apiClient.post('/models/train', data),
};

export const inventoryAPI = {
  getInventoryLevels: (params?: any) =>
    apiClient.get('/inventory-levels', { params }),
  createInventoryLevel: (data: any) =>
    apiClient.post('/inventory-levels', data),
  getInventoryLevel: (id: string) => apiClient.get(`/inventory-levels/${id}`),
  updateInventoryLevel: (id: string, data: any) =>
    apiClient.put(`/inventory-levels/${id}`, data),
  optimizeInventory: (data: any) => apiClient.post('/optimize', data),
  getOptimizations: (params?: any) =>
    apiClient.get('/optimizations', { params }),
  getInventoryAlerts: (params?: any) =>
    apiClient.get('/inventory-alerts', { params }),
};

export const promotionAPI = {
  getPromotions: (params?: any) => apiClient.get('/promotions', { params }),
  createPromotion: (data: any) => apiClient.post('/promotions', data),
  getPromotion: (id: string) => apiClient.get(`/promotions/${id}`),
  updatePromotion: (id: string, data: any) =>
    apiClient.put(`/promotions/${id}`, data),
  deletePromotion: (id: string) => apiClient.delete(`/promotions/${id}`),
  usePromotion: (id: string) => apiClient.post(`/promotions/${id}/use`),
  getPromotionEffectiveness: (data: any) =>
    apiClient.post('/promotions/effectiveness', data),
  getPriceHistory: (params?: any) => apiClient.get('/price-history', { params }),
  createPriceHistory: (data: any) =>
    apiClient.post('/price-history', data),
  optimizePrices: (data: any) => apiClient.post('/price/optimize', data),
};

export const userAPI = {
  login: (data: any) => apiClient.post('/auth/login', data),
  register: (data: any) => apiClient.post('/auth/register', data),
  getProfile: () => apiClient.get('/users/me'),
  updateProfile: (data: any) => apiClient.put('/users/me', data),
  changePassword: (data: any) =>
    apiClient.post('/users/me/change-password', data),
  getUsers: (params?: any) => apiClient.get('/users', { params }),
  createUser: (data: any) => apiClient.post('/users', data),
  getUser: (id: string) => apiClient.get(`/users/${id}`),
  updateUser: (id: string, data: any) =>
    apiClient.put(`/users/${id}`, data),
  deleteUser: (id: string) => apiClient.delete(`/users/${id}`),
  getRoles: () => apiClient.get('/roles'),
  createRole: (data: any) => apiClient.post('/roles', data),
};

export default apiClient;