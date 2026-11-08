"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import { ListState } from "@/components/ListState";
import { AppHeader } from "@/components/AppHeader";
import { isAuthenticated, clearSession, api, errorMessage } from "@/lib/api";
import {
  Button,
  Container,
  Paper,
  Box,
  TextField,
  Typography,
} from "@mui/material";

type PygResult = {
  total_ingresos: number;
  total_gastos: number;
  resultado: number;
  tipo_resultado: string;
};

export default function PygPage() {
  const router = useRouter();
  const { mode, toggle } = useThemeMode();
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [result, setResult] = useState<PygResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) router.push("/login");
  }, [router]);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      setResult(await api(`/cuenta-perdidas-ganancias?${params.toString()}`));
    } catch (e) {
      setError(errorMessage(e));
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
        title="Cuenta de pérdidas y ganancias"
        mode={mode}
        toggle={toggle}
        onNavigateToPanel={() => router.push("/")}
        onLogout={logout}
      />
      <Container sx={{ mt: 4 }} maxWidth="sm">
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
            <TextField label="Desde" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
            <TextField label="Hasta" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
            <Button variant="contained" onClick={load} disabled={loading}>Consultar</Button>
          </Box>
          <ListState loading={loading} items={result ? [result] : []} error={error} onRetry={load} />
        </Paper>
        {!loading && result && (
          <Paper sx={{ p: 3 }}>
            <Typography><strong>Total ingresos:</strong> {result.total_ingresos.toFixed(2)}</Typography>
            <Typography><strong>Total gastos:</strong> {result.total_gastos.toFixed(2)}</Typography>
            <Typography><strong>Resultado:</strong> {result.resultado.toFixed(2)}</Typography>
            <Typography><strong>Tipo:</strong> {result.tipo_resultado}</Typography>
          </Paper>
        )}
      </Container>
    </>
  );
}
