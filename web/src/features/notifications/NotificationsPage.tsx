import { Link } from "react-router-dom";

import { isApiError } from "../../api/errors";
import { RatingBadge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { EmptyState, ErrorPanel, Spinner } from "../../components/ui/StatePanel";
import { useNotifications, useRunNotifications } from "../../hooks/useNotifications";
import { formatDate } from "../../lib/format";

export function NotificationsPage() {
  const feed = useNotifications();
  const run = useRunNotifications();

  return (
    <div className="space-y-5">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Notifications</h1>
          <p className="text-sm text-muted">High-priority recommendation changes</p>
        </div>
        <Button variant="secondary" loading={run.isPending} onClick={() => run.mutate()}>
          Run now
        </Button>
      </header>

      {run.isSuccess && (
        <p className="text-sm text-muted">
          Evaluated {run.data.evaluated} · sent {run.data.sent}
          {run.data.skipped_quiet_hours ? " · skipped (quiet hours)" : ""}
        </p>
      )}

      {feed.isLoading && <Spinner />}
      {feed.isError && (
        <ErrorPanel
          message={isApiError(feed.error) ? feed.error.message : "Could not load notifications."}
        />
      )}
      {feed.data && feed.data.items.length === 0 && (
        <EmptyState
          title="No notifications yet"
          hint="Add symbols to your watchlist or portfolio; the hourly refresh notifies you of meaningful rating changes. Or hit “Run now”."
        />
      )}

      <ul className="space-y-2">
        {feed.data?.items.map((item, i) => (
          <li
            key={`${item.symbol}-${item.sent_at}-${i}`}
            className="flex items-center justify-between rounded-lg border border-border bg-surface px-4 py-3"
          >
            <div className="flex items-center gap-3">
              {item.rating && <RatingBadge rating={item.rating} />}
              {item.symbol ? (
                <Link to={`/recommendations/${item.symbol}`} className="font-semibold hover:text-primary">
                  {item.symbol}
                </Link>
              ) : (
                <span className="text-muted">—</span>
              )}
            </div>
            <div className="text-right text-sm text-muted">
              <div>{formatDate(item.sent_at)}</div>
              <div className={item.status === "sent" ? "text-bull" : "text-bear"}>{item.status}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
