import type { RecapMetricValue, RecapPeriod } from "../../lib/types";

export function metricMap(recap: RecapPeriod | null): Map<string, RecapMetricValue> {
  return new Map((recap?.metrics ?? []).map((item) => [item.metric_key, item]));
}

export function metricNumber(metrics: Map<string, RecapMetricValue>, key: string): number | null {
  const value = metrics.get(key)?.numeric_value;
  return typeof value === "number" ? value : null;
}

export function metricText(metrics: Map<string, RecapMetricValue>, key: string): string | null {
  return metrics.get(key)?.text_value ?? null;
}

export function metricJson(metrics: Map<string, RecapMetricValue>, key: string): Record<string, unknown> {
  return metrics.get(key)?.json_value ?? {};
}

export function stageChangeLabel(raw: string | null): string {
  if (!raw) {
    return "No stage movement";
  }
  const [start, end] = raw.split("->");
  if (!start || !end) {
    return raw.replace(/_/g, " ");
  }
  return `${start.replace(/_/g, " ")} to ${end.replace(/_/g, " ")}`;
}
