import axios from 'axios';

const apiClient = axios.create({
  withCredentials: true,
  // Disable Expect header to prevent 417 errors
  headers: {
    'Expect': ''
  }
});

apiClient.interceptors.request.use((config) => {
  const csrfToken =
    (typeof window !== 'undefined' && (window.csrf_token || window?.frappe?.csrf_token)) || undefined;

  if (csrfToken) {
    config.headers = config.headers ?? {};
    config.headers['X-Frappe-CSRF-Token'] = csrfToken;
  }

  // Remove Expect header if it exists (some servers don't support it)
  if (config.headers) {
    delete config.headers['Expect'];
  }

  // Log request for debugging
  console.log('API Request:', {
    method: config.method?.toUpperCase(),
    url: config.url,
    headers: config.headers,
    data: config.data
  });

  return config;
});

// Add response interceptor for error logging
apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response Success:', {
      url: response.config.url,
      status: response.status,
      data: response.data
    });
    return response;
  },
  (error) => {
    console.error('API Response Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message,
      headers: error.response?.headers
    });
    return Promise.reject(error);
  }
);

export default apiClient;

