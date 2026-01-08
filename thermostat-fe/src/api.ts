import type { Setpoint } from "./hooks/useWiserRoom";

const ENDPOINT = import.meta.env.VITE_API_ENDPOINT || "http://localhost:8080";

export interface WiserState {
  hot_water_channels: HotWaterChannel[];
  heating_channels: HeatingChannel[];
  rooms: Room[];
  room_stats: RoomStat[];
}

export interface HotWaterChannel {
  id: number;
  is_firing: boolean;
  control_source: string;
  boost_ends_at_unix: number | null;
  schedule_id: number | null;
}

export interface HeatingChannel {
  id: number;
  is_firing: boolean;
  demand_percent: number;
  room_ids: number[];
}

export interface Room {
  id: number;
  name: string;
  room_stat_id: number;
  current_temperature: number;
  setpoint_temperature: number;
  demand_percent: number;
  is_firing: boolean;
  control_source: string;
  boost_ends_at_unix: number | null;
  schedule_id: number | null;
  next_setpoint_unix: number | null;
}

export interface RoomStat {
  id: number;
  temperature: number;
  humidity: number;
}

export const getState = async (): Promise<WiserState> => {
  const res = await fetch(ENDPOINT, { credentials: "include" });
  const js = await res.json();
  return js;
};

export const refreshCache = async (): Promise<void> => {
  await fetch(`${ENDPOINT}?ignore_cache=true`, { credentials: "include" });
};

export const boostHeating = async (
  roomId: number,
  setpoint: Setpoint,
): Promise<WiserState> => {
  const nowInSeconds = Math.floor(Date.now() / 1000);
  const diffInSeconds = setpoint.untilUnix - nowInSeconds;
  const minutesAway = Math.floor(diffInSeconds / 60);
  const res = await fetch(`${ENDPOINT}/heating/${roomId}/boost`, {
    method: "PATCH",
    body: JSON.stringify({
      temperature: setpoint.temperature,
      duration_minutes: minutesAway,
    }),
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  const resp = await res.json();
  return resp;
};

export const cancelHeatingBoost = async (
  roomId: number,
): Promise<WiserState> => {
  const res = await fetch(`${ENDPOINT}/heating/${roomId}/boost/cancel`, {
    method: "PATCH",
    credentials: "include",
  });

  const resp = await res.json();
  return resp;
};

export const boostHotWater = async (chId: number, durationMinutes: number) => {
  const res = await fetch(`${ENDPOINT}/hot_water/${chId}/boost`, {
    method: "PATCH",
    body: JSON.stringify({
      duration_minutes: durationMinutes,
    }),
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  const resp = await res.json();
  return resp;
};

export const cancelHotWaterBoost = async (chId: number) => {
  const res = await fetch(`${ENDPOINT}/hot_water/${chId}/boost/cancel`, {
    method: "PATCH",
    credentials: "include",
  });

  const resp = await res.json();
  return resp;
};
