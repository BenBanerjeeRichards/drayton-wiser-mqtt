import { useQuery } from "@tanstack/react-query";
import { getState } from "../api";

export const useWiserState = () => {
  return useQuery({
    queryKey: ["wiserState"],
    queryFn: getState,
    refetchInterval: 1000, // we cache server side so frequent poll means we propagate changes quickly
    refetchIntervalInBackground: false,
  });
};
