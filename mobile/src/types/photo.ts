/**
 * Photo-related types
 */

export interface Photo {
  id: string;
  user_id: string;
  s3_key: string;
  thumbnail_url?: string;
  original_url: string;
  width?: number;
  height?: number;
  file_size?: number;
  upload_status: 'pending' | 'uploaded' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface PhotoListResponse {
  items: Photo[];
  total: number;
  page: number;
  page_size: number;
}

export interface PresignedUploadResponse {
  upload_url: string;
  photo_id: string;
  s3_key: string;
}

export interface PhotoUploadComplete {
  photo_id: string;
  file_size: number;
  width: number;
  height: number;
}
