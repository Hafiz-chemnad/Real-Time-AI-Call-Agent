'use client';

import { useQuery } from '@tanstack/react-query';
import { useWorkspaceStore } from '@/store/workspace';

export interface WorkspaceData {
  id: string;
  name: string;
  phone_number?: string;
  plan?: 'free' | 'pro' | 'enterprise';
  prompt_instructions?: string;
  greeting?: string;
  [key: string]: any;
}

export function useCustomerData() {
  const { activeBusinessId } = useWorkspaceStore();

  const { data, isLoading, error, refetch } = useQuery<WorkspaceData>({
    queryKey: ['workspace', activeBusinessId],
    queryFn: async () => {
      if (!activeBusinessId) throw new Error('No active business ID provided');

      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/businesses/${activeBusinessId}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch business profile: ${response.statusText}`);
      }

      return response.json();
    },
    enabled: !!activeBusinessId,
  });

  return {
    workspace: data,
    isLoading,
    error,
    refetch,
  };
}