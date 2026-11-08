"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import ErrorAlert from "@/components/ErrorAlert";
import { AppHeader } from "@/components/AppHeader";
import { isAuthenticated, clearSession, errorMessage, fetchApi } from "@/lib/api";
import {
  Button,
  Container,
  Paper,
  Box,
  TextField,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
} from "@mui/material";

const FORMATS = [
  { value: "csv", label: "CSV" },
  { value: "pdf", label: "PDF" },
  { value: "xlsx", label: "Excel (XLSX)" },
];

export default function ExportPage() {
  const router = useRouter();
  const { mode, toggle } = useThemeMode();
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [format, setFormat] = useState("csv");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) router.push("/login");
  }, [router]);

  async function download() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ format });
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      const res = await fetchApi(`/exportar-balance?${params.toString()}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `balance.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(errorMessage(e, "Error al exportar"));
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    await clearSession();
    router.push("/login");
  }

  if (!isAuthenticated()) return null;

  return (
    <>
      <AppHeader
        title="Exportación Oficial"
        mode={mode}
        toggle={toggle}
        onNavigateToPanel={() => router.push("/")}
        onLogout={logout}
      />
      <Container sx={{ mt: 4 }} maxWidth="sm">
        <Paper sx={{ p: 3 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Exporta el balance de sumas y saldos del periodo seleccionado en el formato oficial.
          </Typography>
          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
            <TextField
              label="Desde"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
            <TextField
              label="Hasta"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel id="format-label">Formato</InputLabel>
              <Select
                labelId="format-label"
                label="Formato"
                value={format}
                onChange={(e) => setFormat(e.target.value)}
              >
                {FORMATS.map((f) => (
                  <MenuItem key={f.value} value={f.value}>{f.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button variant="contained" onClick={download} disabled={loading} sx={{ height: 56 }}>
              Descargar
            </Button>
          </Box>
          {loading && <CircularProgress sx={{ mt: 3 }} />}
          <ErrorAlert message={error} sx={{ mt: 3 }} />
        </Paper>
      </Container>
    </>
  );
}
