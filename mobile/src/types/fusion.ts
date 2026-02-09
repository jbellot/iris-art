export type BlendMode = 'poisson' | 'alpha';
export type LayoutType = 'horizontal' | 'vertical' | 'grid_2x2';
export type FusionType = 'fusion' | 'composition';

export interface FusionArtwork {
  id: string;
  creator_id: string;
  fusion_type: FusionType;
  blend_mode?: BlendMode;
  layout?: LayoutType;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result_url?: string;
  thumbnail_url?: string;
  source_artwork_ids: string[];
  created_at: string;
  completed_at?: string;
  error?: string;
}

export interface ConsentStatus {
  artwork_id: string;
  owner_id: string;
  owner_name: string;
  status: 'pending' | 'granted' | 'denied';
}

export interface FusionSubmitResponse {
  fusion_id?: string;
  status: 'submitted' | 'consent_required';
  websocket_url?: string;
  pending?: ConsentStatus[];
}

export interface FusionProgress {
  fusion_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  current_step: string;
  result_url?: string;
  thumbnail_url?: string;
  error?: string;
}
