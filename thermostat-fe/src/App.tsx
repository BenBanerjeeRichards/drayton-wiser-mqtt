import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import "./App.css";
import { RoomPage } from "./pages/RoomPage";
import { RoomList } from "./pages/RoomList";
import { HotWaterPage } from "./pages/HotWaterPage";
import { createTheme, MantineProvider } from "@mantine/core";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import { refreshCache } from "./api";

const queryClient = new QueryClient();
const theme = createTheme({});

function App() {
  useEffect(() => {
    // Refresh cache on initial load
    refreshCache().catch(() => {
      // Silently ignore errors
    });
  }, []);

  return (
    <MantineProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter basename="/thermostat">
          <Routes>
            <Route path="/" element={<RoomList />} />
            <Route path="/room/:roomId" element={<RoomPage />} />
            <Route path="/hot-water/:channelId" element={<HotWaterPage />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </MantineProvider>
  );
}

export default App;
