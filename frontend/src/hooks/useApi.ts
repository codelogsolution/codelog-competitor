
import { useCallback, useEffect, useState } from "react";

export function useApi<T>(loader: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setRefreshing(true);
    setError("");

    try {
      const result = await loader();
      setData(result);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load data"
      );
    } finally {
      setRefreshing(false);
    }
  }, [loader]);

  useEffect(() => {
    let active = true;

    loader()
      .then((result) => {
        if (active) {
          setData(result);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(
            err instanceof Error ? err.message : "Unable to load data"
          );
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [loader]);

  return { data, loading, refreshing, error, refresh };
}
