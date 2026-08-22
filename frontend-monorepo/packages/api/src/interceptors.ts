import { apiClient } from './client';

// Person 2: Inject the real Supabase JWT session token here later
apiClient.interceptors.request.use((config) => {
  const token = ''; // TODO: Fetch from Supabase auth session
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});