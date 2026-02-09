/**
 * Processing-related types
 */

export interface ProcessingJob {
  job_id: string;
  photo_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  current_step: string | null;
  progress: number;
  error_type: 'quality_issue' | 'transient_error' | 'server_error' | null;
  error_message: string | null;
  suggestion: string | null;
  result_url: string | null;
  original_url: string | null;
  processing_time_ms: number | null;
  result_width: number | null;
  result_height: number | null;
  websocket_url: string;
  created_at: string;
}

export interface ProcessingProgress {
  job_id: string;
  status: string;
  progress: number;
  step: string; // User-facing magical name
  timestamp: string;
  // Completion fields (only present when completed)
  result_url?: string;
  processing_time_ms?: number;
  result_width?: number;
  result_height?: number;
  // Error fields (only present when failed)
  error_type?: string;
  message?: string;
  suggestion?: string;
}
