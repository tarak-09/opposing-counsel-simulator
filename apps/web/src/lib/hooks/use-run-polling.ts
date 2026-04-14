"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchRunStatus } from "@/lib/api";

export function useRunPolling(runId: string | null) {
  return useQuery({
    queryKey: ["run-status", runId],
    queryFn: () => fetchRunStatus(runId as string),
    enabled: Boolean(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.run.status;
      return status === "completed" || status === "failed" ? false : 2000;
    },
  });
}
