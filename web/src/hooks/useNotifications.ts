import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { NotificationPreference } from "../models/notification";
import { notificationRepository } from "../repositories/notificationRepository";

const KEY = ["notifications"];
const PREFS_KEY = ["notification-preferences"];

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

export function useNotificationPreferences() {
  return useQuery({ queryKey: PREFS_KEY, queryFn: () => notificationRepository.getPreferences() });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (prefs: NotificationPreference) => notificationRepository.updatePreferences(prefs),
    onSuccess: (data) => queryClient.setQueryData(PREFS_KEY, data),
  });
}
