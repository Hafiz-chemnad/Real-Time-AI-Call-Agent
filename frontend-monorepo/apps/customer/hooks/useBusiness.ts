// hooks/useBusiness.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, DEFAULT_BUSINESS_ID } from "@/lib/api";

export function useBusiness(businessId: string = DEFAULT_BUSINESS_ID) {
  const queryClient = useQueryClient();

  const businessQuery = useQuery({
    queryKey: ["business", businessId],
    queryFn: () => api.getBusiness(businessId),
  });

  const toolsQuery = useQuery({
    queryKey: ["tools", businessId],
    queryFn: () => api.getTools(businessId),
  });

  const updatePromptMutation = useMutation({
    mutationFn: (systemPrompt: string) => api.updatePrompt(businessId, systemPrompt),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["business", businessId] });
    },
  });

  const createToolMutation = useMutation({
    mutationFn: (toolData: Record<string, any>) => api.createTool(businessId, toolData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tools", businessId] });
    },
  });

  return {
    business: businessQuery.data,
    isLoadingBusiness: businessQuery.isLoading,
    tools: toolsQuery.data,
    isLoadingTools: toolsQuery.isLoading,
    updatePrompt: updatePromptMutation.mutateAsync,
    createTool: createToolMutation.mutateAsync,
  };
}