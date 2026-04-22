"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { attendanceService } from "@/services/attendance.service";
import type { AttendanceHistoryFilters, ClockRequest } from "@/types/attendance";

export const attendanceKeys = {
  current: ["attendance", "current"] as const,
  history: (filters: AttendanceHistoryFilters) =>
    ["attendance", "history", filters] as const,
};

export function useCurrentAttendance() {
  return useQuery({
    queryKey: attendanceKeys.current,
    queryFn: attendanceService.current,
    refetchInterval: 30_000,
  });
}

export function useAttendanceHistory(filters: AttendanceHistoryFilters = {}) {
  return useQuery({
    queryKey: attendanceKeys.history(filters),
    queryFn: () => attendanceService.history(filters),
  });
}

export function useClockIn() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload?: ClockRequest) => attendanceService.clockIn(payload),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: attendanceKeys.current }),
  });
}

export function useClockOut() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload?: ClockRequest) => attendanceService.clockOut(payload),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: attendanceKeys.current }),
  });
}
