import {
  ActionIcon,
  Button,
  Group,
  Modal,
  SimpleGrid,
  Stack,
  Text,
} from "@mantine/core";
import {
  IconCalendar,
  IconMinus,
  IconPlus,
  IconRocket,
  IconX,
} from "@tabler/icons-react";
import { useState } from "react";
import { useMediaQuery } from "@mantine/hooks";

export interface Setpoint {
  temperature: number;
  untilUnix: number;
}

export interface TemperatureControlProps {
  setpointDegrees: number;
  onChange: (setpoint: Setpoint) => void;
  nextSetpointUnix: number | null;
  setpointPending: boolean;
  source: string;
  onCancelBoost?: () => void;
  minTemp?: number;
  maxTemp?: number;
  step?: number;
}

export function TemperatureControl({
  setpointDegrees,
  onChange,
  nextSetpointUnix,
  setpointPending,
  source,
  onCancelBoost,
  minTemp = 10,
  maxTemp = 23,
  step = 0.5,
}: TemperatureControlProps) {
  const roundUpToNearest5Minutes = (unixTimestamp: number) => {
    const date = new Date(unixTimestamp * 1000);
    const minutes = date.getMinutes();
    const roundedMinutes = Math.ceil(minutes / 5) * 5;
    date.setMinutes(roundedMinutes, 0, 0);
    return Math.floor(date.getTime() / 1000);
  };

  const getMidnightTonight = () => {
    const midnight = new Date();
    midnight.setHours(24, 0, 0, 0);
    return Math.floor(midnight.getTime() / 1000);
  };

  const getDefaultDuration = () => {
    return nextSetpointUnix || getMidnightTonight();
  };

  const handleIncrement = () => {
    const newTemp = Math.min(setpointDegrees + step, maxTemp);
    if (newTemp !== setpointDegrees) {
      onChange({
        temperature: newTemp,
        untilUnix: getDefaultDuration(),
      });
    }
  };

  const handleDecrement = () => {
    const newTemp = Math.max(setpointDegrees - step, minTemp);
    if (newTemp !== setpointDegrees) {
      onChange({
        temperature: newTemp,
        untilUnix: getDefaultDuration(),
      });
    }
  };

  const handlePresetTemp = (temp: number) => {
    if (temp !== setpointDegrees) {
      onChange({
        temperature: temp,
        untilUnix: getDefaultDuration(),
      });
    }
  };

  const [durationModalOpen, setDurationModalOpen] = useState(false);
  const isMobile = useMediaQuery("(max-width: 768px)");

  const presetTemps = [15, 19, 20];

  const formatNextSetpointTime = () => {
    if (nextSetpointUnix === null) return null;

    const date = new Date(nextSetpointUnix * 1000);
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    const prefix = source === "Boost" ? "Boost until" : "Until";
    return `${prefix} ${hours}:${minutes}`;
  };

  const formatTime = (unixTimestamp: number) => {
    const date = new Date(unixTimestamp * 1000);
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    return `${hours}:${minutes}`;
  };

  const getTimeFromNowPlusHours = (hours: number) => {
    const futureTime = new Date();
    futureTime.setHours(futureTime.getHours() + hours);
    const unixTime = Math.floor(futureTime.getTime() / 1000);
    return roundUpToNearest5Minutes(unixTime);
  };

  const handleDurationSelect = (
    type: number | "midnight" | "next-schedule",
  ) => {
    let untilUnix: number;

    if (type === "midnight") {
      untilUnix = getMidnightTonight();
    } else if (type === "next-schedule") {
      untilUnix = nextSetpointUnix || getMidnightTonight();
    } else {
      // For hour-based durations, the rounding is already done in getTimeFromNowPlusHours
      untilUnix = getTimeFromNowPlusHours(type);
    }

    onChange({
      temperature: setpointDegrees,
      untilUnix,
    });

    setDurationModalOpen(false);
  };

  return (
    <Stack
      gap="md"
      align="stretch"
      style={{
        width: "100%",
        maxWidth: isMobile ? "100%" : "600px",
        margin: "0 auto",
      }}
    >
      <Stack gap="xs" align="center">
        <Group gap="xl" align="center" justify="center">
          <ActionIcon
            size="xl"
            variant="filled"
            onClick={handleDecrement}
            disabled={setpointDegrees <= minTemp}
            aria-label="Decrease temperature"
          >
            <IconMinus size={24} />
          </ActionIcon>

          <Text
            size="4rem"
            fw={700}
            c={setpointPending ? "gray.5" : undefined}
            style={{
              userSelect: "none",
              minWidth: "120px",
              textAlign: "center",
            }}
          >
            {setpointDegrees.toFixed(1)}
          </Text>

          <ActionIcon
            size="xl"
            variant="filled"
            onClick={handleIncrement}
            disabled={setpointDegrees >= maxTemp}
            aria-label="Increase temperature"
          >
            <IconPlus size={24} />
          </ActionIcon>
        </Group>

        {formatNextSetpointTime() && (
          <>
            {source === "Boost" ? (
              <Group gap="xs" style={{ width: "100%" }}>
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => setDurationModalOpen(true)}
                  style={{ flex: 1 }}
                  leftSection={<IconRocket size={14} />}
                >
                  {formatNextSetpointTime()}
                </Button>
                <Button
                  variant="light"
                  color="red"
                  size="sm"
                  onClick={onCancelBoost}
                  disabled={setpointPending}
                  leftSection={<IconX size={14} />}
                >
                  Cancel
                </Button>
              </Group>
            ) : (
              <Group gap="xs" justify="center">
                {source === "Schedule" && (
                  <IconCalendar size={16} color="var(--mantine-color-gray-7)" />
                )}
                <Text size="sm" c="gray.7">
                  {formatNextSetpointTime()}
                </Text>
              </Group>
            )}
          </>
        )}
      </Stack>

      <Group gap="sm" justify="space-between" style={{ width: "100%" }}>
        {presetTemps.map((temp) => (
          <Button
            key={temp}
            variant="light"
            size="sm"
            onClick={() => handlePresetTemp(temp)}
            style={{ flex: 1 }}
          >
            {temp}°
          </Button>
        ))}
      </Group>

      <Modal
        opened={durationModalOpen}
        onClose={() => setDurationModalOpen(false)}
        title="Set Duration"
        centered={false}
        styles={{
          content: {
            marginTop: "20vh",
          },
        }}
      >
        <SimpleGrid cols={2} spacing="md">
          <Button
            variant="light"
            onClick={() => handleDurationSelect(1)}
            h="auto"
            py="md"
          >
            <Stack gap="xs" align="center">
              <div>1 Hour</div>
              <Text size="xs" c="dimmed">
                {formatTime(getTimeFromNowPlusHours(1))}
              </Text>
            </Stack>
          </Button>
          <Button
            variant="light"
            onClick={() => handleDurationSelect(2)}
            h="auto"
            py="md"
          >
            <Stack gap="xs" align="center">
              <div>2 Hours</div>
              <Text size="xs" c="dimmed">
                {formatTime(getTimeFromNowPlusHours(2))}
              </Text>
            </Stack>
          </Button>
          <Button
            variant="light"
            onClick={() => handleDurationSelect(4)}
            h="auto"
            py="md"
          >
            <Stack gap="xs" align="center">
              <div>4 Hours</div>
              <Text size="xs" c="dimmed">
                {formatTime(getTimeFromNowPlusHours(4))}
              </Text>
            </Stack>
          </Button>
          <Button
            variant="light"
            onClick={() => handleDurationSelect(6)}
            h="auto"
            py="md"
          >
            <Stack gap="xs" align="center">
              <div>6 Hours</div>
              <Text size="xs" c="dimmed">
                {formatTime(getTimeFromNowPlusHours(6))}
              </Text>
            </Stack>
          </Button>
          {nextSetpointUnix && (
            <Button
              variant="light"
              onClick={() => handleDurationSelect("next-schedule")}
              h="auto"
              py="md"
            >
              <Stack gap="xs" align="center">
                <div>Next Schedule</div>
                <Text size="xs" c="dimmed">
                  {formatTime(nextSetpointUnix)}
                </Text>
              </Stack>
            </Button>
          )}
          <Button
            variant="light"
            onClick={() => handleDurationSelect("midnight")}
            h="auto"
            py="md"
          >
            <Stack gap="xs" align="center">
              <div>Midnight</div>
              <Text size="xs" c="dimmed">
                {formatTime(getMidnightTonight())}
              </Text>
            </Stack>
          </Button>
        </SimpleGrid>
      </Modal>
    </Stack>
  );
}
