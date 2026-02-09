/**
 * TypeScript types for HD export API
 */

export type ExportSourceType = 'styled' | 'ai_generated' | 'processed';

export interface ExportJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  currentStep: string | null;
  isPaid: boolean;
  resultUrl: string | null;
  resultWidth: number | null;
  resultHeight: number | null;
  fileSizeBytes: number | null;
  processingTimeMs: number | null;
  errorType: string | null;
  errorMessage: string | null;
}

export interface HDExportRequest {
  sourceType: ExportSourceType;
  sourceJobId: string;
}

export interface ExportJobListResponse {
  items: ExportJob[];
  total: number;
}
