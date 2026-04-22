"use client";

import { create } from "zustand";
import type { AttendanceStatus } from "@/types/attendance";

interface KioskState {
  selectedEmployee: AttendanceStatus | null;
  pin: string;
  step: "grid" | "pin" | "success";
  successType: "in" | "out" | null;
  selectEmployee: (status: AttendanceStatus) => void;
  appendPin: (digit: string) => void;
  clearPin: () => void;
  reset: () => void;
  setSuccess: (type: "in" | "out") => void;
}

export const useKioskStore = create<KioskState>((set) => ({
  selectedEmployee: null,
  pin: "",
  step: "grid",
  successType: null,

  selectEmployee: (status) =>
    set({ selectedEmployee: status, step: "pin", pin: "" }),

  appendPin: (digit) =>
    set((s) => ({ pin: s.pin.length < 4 ? s.pin + digit : s.pin })),

  clearPin: () => set({ pin: "" }),

  setSuccess: (type) => set({ step: "success", successType: type }),

  reset: () =>
    set({ selectedEmployee: null, pin: "", step: "grid", successType: null }),
}));
