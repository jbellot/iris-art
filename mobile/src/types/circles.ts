/**
 * Types for circles and invites
 */

export interface Circle {
  id: string;
  name: string;
  role: 'owner' | 'member';
  member_count: number;
  created_at: string;
}

export interface CircleMember {
  user_id: string;
  email: string;
  role: 'owner' | 'member';
  joined_at: string;
}

export interface InviteInfo {
  circle_name: string;
  inviter_email: string;
  expires_in_days: number;
}

export interface InviteResponse {
  invite_url: string;
  token: string;
  expires_in_days: number;
}
