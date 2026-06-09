/**
 * API Client for EyeQ Backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UploadResponse {
  success: boolean;
  filename: string;
  path: string;
  size: number;
}

export interface InspectionRequest {
  component_type: string;
  cad_file_path: string;
}

export interface InspectionStatus {
  status: string;
  step?: string;
  message: string;
  data?: any;
  results?: any;
  cad_dimensions?: Record<string, number>;
  live_measurement?: string;
}

export interface CADDimensions {
  dimensions: Record<string, number>;
}

export interface ComparisonReport {
  report: Record<string, any>;
}

export interface DashboardStats {
  total_inspections: number;
  defective_count: number;
  pass_rate: number;
  avg_deviation: number;
}

export interface RecentInspection {
  timestamp: number;
  status: string;
  measurements: Record<string, number>;
  errors: Record<string, number>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: "Unknown error" }));
      throw new Error(error.detail || error.message || "Request failed");
    }

    return response.json();
  }

  async uploadCADFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${this.baseUrl}/api/upload-cad`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: "Upload failed" }));
      throw new Error(error.detail || error.message || "Upload failed");
    }

    return response.json();
  }

  async startInspection(request: InspectionRequest): Promise<{ success: boolean; inspection_id: string; message: string }> {
    return this.request("/api/start-inspection", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getInspectionStatus(inspectionId: string): Promise<InspectionStatus> {
    return this.request(`/api/inspection-status/${inspectionId}`);
  }

  async getLiveMeasurement(): Promise<{ measurement: string | null }> {
    return this.request("/api/live-measurement");
  }

  async getCADDimensions(): Promise<CADDimensions> {
    return this.request("/api/cad-dimensions");
  }

  async getComparisonReport(): Promise<ComparisonReport> {
    return this.request("/api/comparison-report");
  }

  async getDashboardStats(): Promise<DashboardStats> {
    return this.request("/api/dashboard-stats");
  }

  async getRecentInspections(limit: number = 10): Promise<{ inspections: RecentInspection[] }> {
    return this.request(`/api/recent-inspections?limit=${limit}`);
  }

  async stopInspection(inspectionId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/stop-inspection/${inspectionId}`, {
      method: "POST",
    });
  }
}

export const apiClient = new ApiClient();

