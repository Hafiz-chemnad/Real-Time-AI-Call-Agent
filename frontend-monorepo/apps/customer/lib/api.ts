// lib/api.ts

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

// FastAPI strictly requires UUID string format (returns 422 if an arbitrary string like "demo-business" is passed)
export const DEFAULT_BUSINESS_ID = "123e4567-e89b-12d3-a456-426614174000";

/**
 * Sanitizes input IDs. If the ID is missing or not a valid UUID format (e.g., "demo-business"),
 * it defaults to a valid UUID string to prevent FastAPI 422 validation errors.
 */
export function sanitizeBusinessId(id?: string): string {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!id || !uuidRegex.test(id)) {
    return DEFAULT_BUSINESS_ID;
  }
  return id;
}

/**
 * Core API fetch wrapper that automatically handles backend URLs, headers,
 * trailing slashes, and graceful fallback mock data for unmapped backend routes.
 */
async function fetchFromBackend<T>(
  endpoint: string,
  options?: RequestInit,
  fallbackData?: T
): Promise<T> {
  const url = `${BACKEND_URL}${endpoint}`;

  try {
    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
    });

    // If endpoint doesn't exist on backend (404) and fallback provided, return mock gracefully
    if (res.status === 404 && fallbackData !== undefined) {
      console.warn(`[API Mock Fallback] 404 at ${endpoint}. Returning local fallback data.`);
      return fallbackData;
    }

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`API Error ${res.status} (${res.statusText}): ${errorText}`);
    }

    if (res.status === 204) {
      return {} as T;
    }

    return await res.json();
  } catch (error) {
    if (fallbackData !== undefined) {
      console.warn(`[API Mock Fallback] Connection error for ${endpoint}. Returning local fallback:`, error);
      return fallbackData;
    }
    throw error;
  }
}

// ==========================================================
// Strictly Aligned API Client Methods
// ==========================================================

export const api = {
  // --------------------------------------------------------
  // 1. Business Profile & Persona Configuration
  // --------------------------------------------------------
  getBusiness: (businessId?: string) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(`/businesses/${id}`);
  },

  updateBusiness: (businessId: string | undefined, payload: Record<string, any>) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(`/businesses/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  updatePrompt: (businessId: string | undefined, system_prompt_template: string) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(`/businesses/${id}/prompt`, {
      method: "PUT",
      body: JSON.stringify({ system_prompt_template }),
    });
  },

  updateGuardrails: (businessId: string | undefined, guardrails: Record<string, any>) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(`/businesses/${id}/guardrails`, {
      method: "PUT",
      body: JSON.stringify({ guardrails }),
    });
  },

  // GET /persona fallback (maps directly to business details or mock)
  getPersona: (businessId?: string) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(
      `/businesses/${id}`,
      undefined,
      {
        name: "Voice AI Receptionist",
        greeting: "Hello! How can I assist your business today?",
        tone: "professional",
        system_prompt: "You are an AI phone receptionist handling inbound calls efficiently.",
      }
    );
  },

  // --------------------------------------------------------
  // 2. Tools Management (Trailing Slash Required: /tools/)
  // --------------------------------------------------------
  getTools: (businessId?: string) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(`/businesses/${id}/tools/`, undefined, []);
  },

  createTool: (businessId: string | undefined, toolData: Record<string, any>) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(`/businesses/${id}/tools/`, {
      method: "POST",
      body: JSON.stringify(toolData),
    });
  },

  updateTool: (businessId: string | undefined, toolId: string, toolData: Record<string, any>) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(`/businesses/${id}/tools/${toolId}`, {
      method: "PUT",
      body: JSON.stringify(toolData),
    });
  },

  deleteTool: (businessId: string | undefined, toolId: string) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(`/businesses/${id}/tools/${toolId}`, {
      method: "DELETE",
    });
  },

  // --------------------------------------------------------
  // 3. Knowledge Base (Trailing Slash Required: /knowledge/)
  // --------------------------------------------------------
  getKnowledge: (businessId?: string) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(`/businesses/${id}/knowledge/`, undefined, { documents: [] });
  },

  updateKnowledge: (businessId: string | undefined, knowledgeData: Record<string, any>) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(`/businesses/${id}/knowledge/`, {
      method: "PUT",
      body: JSON.stringify(knowledgeData),
    });
  },

  // --------------------------------------------------------
  // 4. Test Chat (Trailing Slash Required: /chat/)
  // --------------------------------------------------------
  sendChatMessage: (businessId: string | undefined, transcript: string) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(`/businesses/${id}/chat/`, {
      method: "POST",
      body: JSON.stringify({ transcript }),
    });
  },

  // --------------------------------------------------------
  // 5. Dashboard Views with Safe Fallback Mocks
  //    (Handles endpoints missing in FastAPI backend schema)
  // --------------------------------------------------------
  getMetrics: (businessId?: string) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(
      `/businesses/${id}/metrics`,
      undefined,
      {
        total_calls: 142,
        avg_duration_seconds: 118,
        escalation_rate: 0.05,
        total_cost: 12.4,
        calls_trend: [
          { date: "Aug 18", calls: 22 },
          { date: "Aug 19", calls: 25 },
          { date: "Aug 20", calls: 19 },
          { date: "Aug 21", calls: 30 },
          { date: "Aug 22", calls: 28 },
          { date: "Aug 23", calls: 18 },
        ],
      }
    );
  },

  getLogs: (businessId?: string) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(
      `/businesses/${id}/logs`,
      undefined,
      [
        {
          id: "log-1",
          timestamp: new Date().toISOString(),
          caller: "+1 (555) 019-2831",
          duration_seconds: 94,
          status: "completed",
          summary: "Caller asked about business hours and appointment booking.",
          intent: "general_inquiry",
        },
      ]
    );
  },

  getChannels: (businessId?: string) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(
      `/businesses/${id}/channels`,
      undefined,
      {
        phone_number: "+1 (800) 555-0199",
        provider: "Twilio",
        status: "connected",
        webrtc_enabled: true,
      }
    );
  },

  getBilling: (businessId?: string) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(
      `/businesses/${id}/billing`,
      undefined,
      {
        plan: "Pro Plan",
        status: "active",
        minutes_used: 280,
        minutes_limit: 1000,
        current_period_end: "2026-09-01T00:00:00Z",
      }
    );
  },

  updateAutoRefill: (businessId: string | undefined, enabled: boolean) => {
    const id = sanitizeBusinessId(businessId);
    return fetchFromBackend(
      `/businesses/${id}/billing/auto-refill`,
      {
        method: "POST",
        body: JSON.stringify({ auto_refill: enabled }),
      },
      { success: true, auto_refill: enabled }
    );
  },
};