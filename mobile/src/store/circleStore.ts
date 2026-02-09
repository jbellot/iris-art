/**
 * Zustand store for circles
 */
import { create } from 'zustand';
import { Circle } from '../types/circles';
import { getCircles } from '../services/circles';

interface CircleStore {
  circles: Circle[];
  loading: boolean;
  error: string | null;
  fetchCircles: () => Promise<void>;
  addCircle: (circle: Circle) => void;
  removeCircle: (circleId: string) => void;
}

export const useCircleStore = create<CircleStore>((set) => ({
  circles: [],
  loading: false,
  error: null,

  fetchCircles: async () => {
    set({ loading: true, error: null });
    try {
      const circles = await getCircles();
      set({ circles, loading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch circles',
        loading: false,
      });
    }
  },

  addCircle: (circle: Circle) => {
    set((state) => ({
      circles: [circle, ...state.circles],
    }));
  },

  removeCircle: (circleId: string) => {
    set((state) => ({
      circles: state.circles.filter((c) => c.id !== circleId),
    }));
  },
}));
