import { useQueryClient } from "@tanstack/react-query";
import { boostHotWater, cancelHotWaterBoost } from "../api";
import { useWiserState } from "./useWiserState";

export const useWiserHotWater = (chId: number) => {
  const { data } = useWiserState();
  const queryClient = useQueryClient();

  if (!data) {
    return null;
  }

  const hwState = data?.hot_water_channels.find(
    (channel) => channel.id === chId,
  );
  if (!hwState) {
    throw new Error(`HW channel ${chId} not found`);
  }

  const cancelBoost = async () => {
    const resp = await cancelHotWaterBoost(chId);
    queryClient.setQueryData(["wiserState"], resp);
  };

  const boost = async (durationMinutes: number) => {
    const resp = await boostHotWater(chId, durationMinutes);
    queryClient.setQueryData(["wiserState"], resp);
  };

  return {
    isFiring: hwState.is_firing,
    boostEndsAtUnix: hwState.boost_ends_at_unix,
    controlSource: hwState.control_source,
    boost,
    cancelBoost,
  };
};
