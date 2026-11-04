"use client"

import useSWR from "swr"
import api from "@/lib/api"

/**
 * A/B testing client.
 *
 * `GET /experiments/:key` both evaluates the user's variant and records their
 * first exposure. That side effect is intentional: the evaluation call is the
 * moment the experiment surface is shown. The endpoint is idempotent, so
 * re-renders and reloads cannot inflate the denominator.
 *
 * The hook fails open. If the experiment service is unavailable, `variant`
 * stays null and the caller renders the control experience.
 */

export type ExperimentAssignment = {
  key: string
  name: string
  status: string
  active: boolean
  variant: string | null
  primary_metric: string
}

export const BRIEFING_QUICK_COMPLETE = "briefing_quick_complete"
export const QUICK_ACTION_COMPLETED = "quick_action_completed"

export function useExperiment(key: string) {
  const { data, error, isLoading } = useSWR<ExperimentAssignment>(
    `/experiments/${key}`,
    (url: string) => api.get(url).then(r => r.data),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      dedupingInterval: 3600000,
    }
  )

  return {
    experiment: data,
    variant: data?.variant ?? null,
    active: data?.active ?? false,
    isLoading,
    error,
  }
}

/**
 * Record a conversion event. The server resolves the variant from the user's
 * exposure, so the client cannot claim to be in a different arm.
 */
export async function trackExperimentEvent(
  key: string,
  eventName: string,
  metadata?: Record<string, unknown>
) {
  return api.post(`/experiments/${key}/events`, {
    event_name: eventName,
    metadata,
  })
}
