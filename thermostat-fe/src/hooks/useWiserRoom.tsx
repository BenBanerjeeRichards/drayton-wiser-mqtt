import { useEffect, useState } from "react";
import { useWiserState } from "./useWiserState";
import { boostHeating, cancelHeatingBoost } from "../api";
import { useQueryClient } from "@tanstack/react-query";
import { useDebounce } from "./useDebouce";

export interface Setpoint {
  temperature: number;
  untilUnix: number;
}

export const useWiserRoom = (roomId: number) => {
  // When the user presses a button, it takes a while until we are able to sync this with
  // the actual thermostat. Until then, it is 'desired'
  const [desiredSetpoint, setDesiredSetpoint] = useState<Setpoint | null>(null);
  const debouncedSetpoint = useDebounce(desiredSetpoint, 200);
  const { data } = useWiserState();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!debouncedSetpoint) {
      return;
    }
    const sync = async () => {
      // Sync with thermostat
      const resp = await boostHeating(roomId, debouncedSetpoint);
      queryClient.setQueryData(["wiserState"], resp);
      setDesiredSetpoint(null);
    };
    sync();
  }, [roomId, debouncedSetpoint, queryClient]);

  if (!data) {
    return null;
  }

  const roomState = data.rooms.find((room) => room.id === roomId);
  if (!roomState) {
    throw new Error(`Room ${roomId} not found`);
  }

  const cancelBoost = async () => {
    const resp = await cancelHeatingBoost(roomId);
    queryClient.setQueryData(["wiserState"], resp);
  };

  return {
    desiredSetpoint,
    setDesiredSetpoint,
    setpointTemperature: roomState.setpoint_temperature,
    currentTemperature: roomState.current_temperature,
    roomName: roomState.name,
    nextSetpointUnix: roomState.next_setpoint_unix,
    controlSource: roomState.control_source,
    isFiring: roomState.is_firing,
    cancelBoost,
  };
};
