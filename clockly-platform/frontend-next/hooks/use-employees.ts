"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { employeesService } from "@/services/employees.service";
import type { EmployeeCreateRequest, EmployeeUpdateRequest } from "@/types/employee";

export const employeeKeys = {
  all: ["employees"] as const,
  detail: (id: string) => ["employees", id] as const,
};

export function useEmployees() {
  return useQuery({
    queryKey: employeeKeys.all,
    queryFn: employeesService.list,
  });
}

export function useEmployee(id: string) {
  return useQuery({
    queryKey: employeeKeys.detail(id),
    queryFn: () => employeesService.get(id),
    enabled: Boolean(id),
  });
}

export function useCreateEmployee() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: EmployeeCreateRequest) =>
      employeesService.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: employeeKeys.all }),
  });
}

export function useUpdateEmployee(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: EmployeeUpdateRequest) =>
      employeesService.update(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: employeeKeys.all });
      qc.invalidateQueries({ queryKey: employeeKeys.detail(id) });
    },
  });
}

export function useSetEmployeeActive() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      employeesService.setActive(id, isActive),
    onSuccess: () => qc.invalidateQueries({ queryKey: employeeKeys.all }),
  });
}
