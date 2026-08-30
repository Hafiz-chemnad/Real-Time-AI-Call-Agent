'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface WorkspaceState {
  activeBusinessId: string;
  setActiveBusinessId: (id: string, queryClient?: any) => void;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      activeBusinessId: 'demo-business',
      setActiveBusinessId: (id, queryClient) => {
        set({ activeBusinessId: id });
        if (queryClient) {
          queryClient.invalidateQueries();
        }
      },
    }),
    {
      name: 'active-workspace-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);