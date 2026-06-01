import { apiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type { NotificationFeedResponse, RunResult } from "../models/notification";

export const notificationRepository = {
  list: (limit = 50) => apiClient.get<NotificationFeedResponse>(endpoints.notifications.list(limit)),
  run: () => apiClient.post<RunResult>(endpoints.notifications.run),
};
