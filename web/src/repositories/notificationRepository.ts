import { apiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type {
  NotificationFeedResponse,
  NotificationPreference,
  RunResult,
} from "../models/notification";

export const notificationRepository = {
  list: (limit = 50) => apiClient.get<NotificationFeedResponse>(endpoints.notifications.list(limit)),
  run: () => apiClient.post<RunResult>(endpoints.notifications.run),
  getPreferences: () =>
    apiClient.get<NotificationPreference>(endpoints.notifications.preferences),
  updatePreferences: (prefs: NotificationPreference) =>
    apiClient.put<NotificationPreference>(endpoints.notifications.preferences, prefs),
};
