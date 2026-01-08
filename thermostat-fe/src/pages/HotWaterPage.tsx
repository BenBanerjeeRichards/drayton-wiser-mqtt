import { useParams, useNavigate } from "react-router-dom";
import {
  ActionIcon,
  Button,
  Group,
  Modal,
  SimpleGrid,
  Stack,
  Text,
} from "@mantine/core";
import { IconArrowLeft, IconFlame } from "@tabler/icons-react";
import { useMediaQuery } from "@mantine/hooks";
import { useWiserHotWater } from "../hooks/useWiserHotWater";
import { useState } from "react";

export function HotWaterPage() {
  const { channelId } = useParams<{ channelId: string }>();
  const navigate = useNavigate();
  const isMobile = useMediaQuery("(max-width: 768px)");
  const [boostModalOpen, setBoostModalOpen] = useState(false);

  const hwState = useWiserHotWater(Number(channelId));

  if (!hwState) {
    return <>Loading...</>;
  }

  const formatTime = (unixTimestamp: number | null) => {
    if (!unixTimestamp) return null;
    const date = new Date(unixTimestamp * 1000);
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    return `${hours}:${minutes}`;
  };

  const handleBoostSelect = (hours: number) => {
    hwState.boost(hours * 60);
    setBoostModalOpen(false);
  };

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
            aria-label="Back to home"
          >
            <IconArrowLeft size={20} />
          </ActionIcon>
          <Group align="center" gap="xs">
            <Text size="xl" fw={700}>
              Hot Water
            </Text>
            {hwState.isFiring && <IconFlame size={20} color="orange" />}
          </Group>
        </Group>
      </Group>

      <Stack
        gap="md"
        style={{
          width: "100%",
          maxWidth: isMobile ? "100%" : "600px",
          margin: "2rem auto 0",
        }}
      >
        <Group justify="center" py="xl">
          <Text size="2rem" fw={600} c={hwState.isFiring ? "orange" : "gray.6"}>
            {hwState.isFiring ? "Heating" : "Off"}
          </Text>
        </Group>

        {hwState.controlSource === "Boost" && hwState.boostEndsAtUnix && (
          <Stack gap="md">
            <Text size="lg" ta="center">
              Boost until {formatTime(hwState.boostEndsAtUnix)}
            </Text>
            <Button
              variant="light"
              color="red"
              size="md"
              onClick={hwState.cancelBoost}
              fullWidth
            >
              Cancel Boost
            </Button>
          </Stack>
        )}

        {hwState.controlSource === "Schedule" && (
          <Button
            variant="filled"
            size="lg"
            onClick={() => setBoostModalOpen(true)}
            fullWidth
          >
            Boost Hot Water
          </Button>
        )}
      </Stack>

      <Modal
        opened={boostModalOpen}
        onClose={() => setBoostModalOpen(false)}
        title="Boost Duration"
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
            onClick={() => handleBoostSelect(1)}
            h="auto"
            py="md"
          >
            <div>1 Hour</div>
          </Button>
          <Button
            variant="light"
            onClick={() => handleBoostSelect(2)}
            h="auto"
            py="md"
          >
            <div>2 Hours</div>
          </Button>
        </SimpleGrid>
      </Modal>
    </div>
  );
}
