import { useEffect, useState } from "react";

export const useDebounce = <T>(
  newState: T | null,
  timeMs: number,
): T | null => {
  const [state, setState] = useState<T | null>(null);

  useEffect(() => {
    const newTimer = setTimeout(() => setState(newState), timeMs);
    return () => clearTimeout(newTimer);
  }, [newState, timeMs]);

  return state;
};
