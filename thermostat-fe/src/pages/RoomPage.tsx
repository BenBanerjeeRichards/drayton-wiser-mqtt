import { TemperatureControl } from "../components/temperature-control/TemperatureControl";
import { useWiserRoom } from "../hooks/useWiserRoom";
import { useParams, useNavigate } from "react-router-dom";
import { ActionIcon, Group, Text } from "@mantine/core";
import { IconArrowLeft, IconFlame } from "@tabler/icons-react";
import { useMediaQuery } from "@mantine/hooks";

export function RoomPage() {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();
  const isMobile = useMediaQuery("(max-width: 768px)");
  const roomState = useWiserRoom(Number(roomId));

  if (!roomState) {
    return <>Loading...</>;
  }

  const {
    desiredSetpoint,
    setDesiredSetpoint,
    setpointTemperature,
    currentTemperature,
    roomName,
    nextSetpointUnix,
    controlSource,
    isFiring,
    cancelBoost,
  } = roomState;

  return (
    <div style={{ width: "100%", padding: "0 1rem" }}>
      <Group
        align="center"
        justify="space-between"
        style={{
          width: "100%",
          maxWidth: isMobile ? "100%" : "600px",
          margin: "0 auto",
          paddingTop: "1.5rem",
          paddingBottom: "1rem",
        }}
      >
        <Group align="center" gap="md">
          <ActionIcon
            size="lg"
            variant="subtle"
            onClick={() => navigate("/")}
            aria-label="Back to rooms"
          >
            <IconArrowLeft size={20} />
          </ActionIcon>
          <Group align="center" gap="xs">
            <Text size="xl" fw={700}>
              {roomName}
            </Text>
            {isFiring && <IconFlame size={20} color="orange" />}
          </Group>
        </Group>

        <Text size="lg" fw={500} c="gray.7">
          {currentTemperature.toFixed(1)}°
        </Text>
      </Group>

      <div style={{ marginTop: "2rem" }}>
        <TemperatureControl
          setpointPending={desiredSetpoint?.temperature !== undefined}
          setpointDegrees={desiredSetpoint?.temperature || setpointTemperature}
          source={controlSource}
          onChange={(setpoint) => {
            setDesiredSetpoint(setpoint);
          }}
          nextSetpointUnix={nextSetpointUnix}
          onCancelBoost={cancelBoost}
        />
      </div>
    </div>
  );
}
