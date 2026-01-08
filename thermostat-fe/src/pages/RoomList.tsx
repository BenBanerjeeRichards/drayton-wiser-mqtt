import { Button, Group, Stack, Text } from "@mantine/core";
import { useWiserState } from "../hooks/useWiserState";
import { useNavigate } from "react-router-dom";
import { useMediaQuery } from "@mantine/hooks";
import { IconFlame } from "@tabler/icons-react";

export function RoomList() {
  const { data, isLoading, error } = useWiserState();
  const navigate = useNavigate();
  const isMobile = useMediaQuery("(max-width: 768px)");

  if (isLoading) {
    return <div style={{ padding: "1rem" }}>Loading...</div>;
  }

  if (error) {
    return <div style={{ padding: "1rem" }}>Error loading rooms</div>;
  }

  if (!data) {
    return null;
  }

  return (
    <Stack
      gap="md"
      style={{
        width: "100%",
        maxWidth: isMobile ? "100%" : "600px",
        margin: "0 auto",
        padding: "1rem",
      }}
    >
      <Text size="xl" fw={700} mb="md">
        Rooms
      </Text>
      <Stack gap="sm">
        {data.rooms.map((room) => (
          <Button
            key={room.id}
            variant="light"
            size="lg"
            onClick={() => navigate(`/room/${room.id}`)}
            h="auto"
            py="md"
          >
            <Group justify="space-between" style={{ width: "100%" }}>
              <Group gap="xs" align="center">
                <Text fw={500}>{room.name}</Text>
                {room.is_firing && <IconFlame size={18} color="orange" />}
              </Group>
              <Text fw={600}>{room.setpoint_temperature.toFixed(1)}°</Text>
            </Group>
          </Button>
        ))}

        {data.hot_water_channels.length > 0 && (
          <Button
            variant="light"
            size="lg"
            onClick={() =>
              navigate(`/hot-water/${data.hot_water_channels[0].id}`)
            }
            h="auto"
            py="md"
          >
            <Group justify="space-between" style={{ width: "100%" }}>
              <Group gap="xs" align="center">
                <Text fw={500}>Hot Water</Text>
                {data.hot_water_channels[0].is_firing && (
                  <IconFlame size={18} color="orange" />
                )}
              </Group>
            </Group>
          </Button>
        )}
      </Stack>
    </Stack>
  );
}
