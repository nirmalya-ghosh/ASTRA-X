/**
 * AstraX AI — API Client
 * Centralized API communication with the FastAPI backend.
 */

export function getApiUrl(): string {
  let url = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  // Gracefully handle if the user forgot to append /api/v1 in their Vercel settings
  if (!url.includes("/api/v1")) {
    url = url.replace(/\/+$/, '') + "/api/v1";
  }
  return url.replace(/\/+$/, '');
}

const API_BASE = getApiUrl();

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options;

  let url = `${API_BASE}${endpoint}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.set(key, String(value));
      }
    });
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers: {
      "Content-Type": "application/json",
      ...fetchOptions.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, error.detail || "Unknown error");
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

// ── Dataset API ──────────────────────────────────────────────

export interface Dataset {
  id: number;
  name: string;
  description: string | null;
  source_path: string;
  status: string;
  file_count: number;
  total_size_bytes: number;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Frame {
  id: number;
  dataset_id: number;
  filename: string;
  frame_index: number;
  width: number | null;
  height: number | null;
  bitpix: number | null;
  exposure_time: number | null;
  filter_name: string | null;
  date_obs: string | null;
  ra: number | null;
  dec: number | null;
  instrument: string | null;
  status: string;
  preview_path: string | null;
  created_at: string;
}

export interface Candidate {
  id: number;
  frame_id: number;
  dataset_id: number;
  x_centroid: number;
  y_centroid: number;
  ra: number | null;
  dec: number | null;
  flux: number | null;
  magnitude: number | null;
  snr: number | null;
  fwhm: number | null;
  sharpness: number | null;
  roundness: number | null;
  motion_dx: number | null;
  motion_dy: number | null;
  motion_speed: number | null;
  motion_angle: number | null;
  confidence_score: number;
  risk_score: number;
  persistence_score: number;
  detection_count: number;
  classification: string;
  object_type: string | null;
  notes?: string;
  detection_method: string | null;
  created_at: string;
  reviewed_at: string | null;
}

export interface TaskStatus {
  id: number;
  task_type: string;
  status: string;
  progress: number;
  message: string | null;
  result_json: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export const api = {
  // Health
  health: () => apiFetch<{ status: string; version: string; gpu_available: boolean }>("/health"),

  // Datasets
  datasets: {
    list: (params?: { skip?: number; limit?: number; status?: string }) =>
      apiFetch<{ datasets: Dataset[]; total: number }>("/datasets", { params }),

    get: (id: number) => apiFetch<Dataset>(`/datasets/${id}`),

    importFolder: (data: { path: string; name?: string; description?: string }) =>
      apiFetch<Dataset>("/datasets/import-folder", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    frames: (datasetId: number) =>
      apiFetch<Frame[]>(`/datasets/${datasetId}/frames`),

    frameHeader: (datasetId: number, frameIndex: number) =>
      apiFetch<{ frame_id: number; filename: string; headers: Record<string, unknown> }>(
        `/datasets/${datasetId}/frames/${frameIndex}/header`
      ),

    framePreviewUrl: (datasetId: number, frameIndex: number, stretch = "zscale", colormap = "gray") =>
      `${API_BASE}/datasets/${datasetId}/frames/${frameIndex}/preview?stretch=${stretch}&colormap=${colormap}`,

    delete: (id: number) =>
      apiFetch<void>(`/datasets/${id}`, { method: "DELETE" }),

    upload: async (file: File, name?: string) => {
      const formData = new FormData();
      formData.append("file", file);
      if (name) formData.append("name", name);

      const response = await fetch(`${API_BASE}/datasets`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new ApiError(response.status, error.detail);
      }

      return response.json() as Promise<Dataset>;
    },
  },

  // Detection
  detection: {
    run: (data: {
      dataset_id: number;
      fwhm?: number;
      threshold_sigma?: number;
      motion_threshold?: number;
    }) =>
      apiFetch<TaskStatus>("/detection/run", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  // Processing
  processing: {
    run: (data: { dataset_id: number; steps?: Array<{ name: string; enabled: boolean; params?: Record<string, unknown> }> }) =>
      apiFetch<TaskStatus>("/processing/run", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  // Candidates
  candidates: {
    list: (params?: {
      dataset_id?: number;
      classification?: string;
      min_confidence?: number;
      sort_by?: string;
      sort_order?: string;
      page?: number;
      page_size?: number;
    }) =>
      apiFetch<{ candidates: Candidate[]; total: number; page: number; page_size: number }>(
        "/candidates",
        { params }
      ),

    get: (id: number) => apiFetch<Candidate>(`/candidates/${id}`),

    review: (id: number, data: { classification: string; object_type?: string; notes?: string }) =>
      apiFetch<Candidate>(`/candidates/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),

    bulkReview: (candidateIds: number[], classification: string) =>
      apiFetch<{ updated: number }>("/candidates/bulk-review", {
        method: "POST",
        body: JSON.stringify({ candidate_ids: candidateIds, classification }),
      }),
  },

  // Tasks
  tasks: {
    list: (params?: { task_type?: string; status?: string; limit?: number }) =>
      apiFetch<TaskStatus[]>("/tasks", { params }),

    get: (id: number) => apiFetch<TaskStatus>(`/tasks/${id}`),
  },

  // AI Assistant
  assistant: {
    chat: (data: { message: string; session_id?: string; context?: Record<string, unknown> }) =>
      apiFetch<{ session_id: string; role: string; content: string; created_at: string }>(
        "/assistant/chat",
        { method: "POST", body: JSON.stringify(data) }
      ),

    explain: (candidateId: number) =>
      apiFetch<{ candidate_id: number; explanation: string }>(
        `/assistant/explain?candidate_id=${candidateId}`,
        { method: "POST" }
      ),

    history: (sessionId: string) =>
      apiFetch<Array<{ session_id: string; role: string; content: string; created_at: string }>>(
        `/assistant/history?session_id=${sessionId}`
      ),
  },

  // Export
  export: {
    create: (data: { dataset_id: number; format: string; candidate_ids?: number[] }) =>
      apiFetch<{ task_id: number; format: string; status: string }>(
        "/export",
        { method: "POST", body: JSON.stringify(data) }
      ),
  },

  // Settings
  settings: {
    get: () => apiFetch<Record<string, unknown>>("/settings"),

    update: (data: Record<string, unknown>) =>
      apiFetch<Record<string, unknown>>("/settings", {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
  },
};
