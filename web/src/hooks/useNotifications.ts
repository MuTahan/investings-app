import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { notificationRepository } from "../repositories/notificationRepository";

const KEY = ["notifications"];

export function useNotifications() {
  return useQuery({ queryKey: KEY, queryFn: () => notificationRepository.list() });
}

export function useRunNotifications() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => notificationRepository.run(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: KEY }),
  });
}
