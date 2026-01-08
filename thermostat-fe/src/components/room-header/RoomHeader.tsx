import { Group, Text } from "@mantine/core";
import { useMediaQuery } from "@mantine/hooks";

export interface RoomHeaderProps {
  roomName: string;
  currentTemperature: number;
}

export function RoomHeader({ roomName, currentTemperature }: RoomHeaderProps) {
  const isMobile = useMediaQuery("(max-width: 768px)");

  return (
    <Group
      justify="space-between"
      align="center"
      style={{
        width: "100%",
        maxWidth: isMobile ? "100%" : "600px",
        margin: "0 auto",
        paddingTop: "1.5rem",
        paddingBottom: "1rem",
        borderBottom: "1px solid var(--mantine-color-gray-3)",
      }}
    >
      <Text size="xl" fw={700}>
        {roomName}
      </Text>
      <Text size="lg" fw={500} c="gray.7">
        {currentTemperature.toFixed(1)}°
      </Text>
    </Group>
  );
}
