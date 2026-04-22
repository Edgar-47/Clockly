"use client";

import { useQuery } from "@tanstack/react-query";
import { dashboardService } from "@/services/dashboard.service";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: dashboardService.summary,
    staleTime: 20_000,
    refetchInterval: 60_000,
  });
}
