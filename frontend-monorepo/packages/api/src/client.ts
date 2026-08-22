import axios from 'axios';

// This points to your Python FastAPI server (which usually runs on 8000)
export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});