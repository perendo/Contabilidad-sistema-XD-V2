"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import ErrorAlert from "@/components/ErrorAlert";
import { AppHeader } from "@/components/AppHeader";
import { isAuthenticated, clearSession, api, errorMessage } from "@/lib/api";
import {
  Button,
  Container,
  Paper,
  Box,
  TextField,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  CircularProgress,
  Typography,
} from "@mui/material";

type IvaBreakdown = {
  devengado: number;
  deducible: number;
};

type IvaResult = {
  iva_devengado: number;
  iva_deducible: number;
  saldo: number;
  tipo_saldo: string;
  breakdown: Record<string, IvaBreakdown>;
};

export default function IvaPage() {
  const router = useRouter();
  const { mode, toggle } = useThemeMode();
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [result, setResult] = useState<IvaResult | null>(null);
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
      setResult(await api(`/iva-liquidation?${params.toString()}`));
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
        title="Liquidación IVA (Mod. 303)"
        mode={mode}
        toggle={toggle}
        onNavigateToPanel={() => router.push("/")}
        onLogout={logout}
      />
      <Container sx={{ mt: 4 }} maxWidth="md">
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
            <TextField label="Desde" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
            <TextField label="Hasta" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
            <Button variant="contained" onClick={load} disabled={loading}>Consultar</Button>
          </Box>
          <ErrorAlert message={error} sx={{ mt: 2 }} />
        </Paper>
        {loading ? <CircularProgress /> : result && (
          <Paper sx={{ p: 3 }}>
            <Typography><strong>IVA devengado:</strong> {result.iva_devengado.toFixed(2)}</Typography>
            <Typography><strong>IVA deducible:</strong> {result.iva_deducible.toFixed(2)}</Typography>
            <Typography><strong>Saldo:</strong> {result.saldo.toFixed(2)} ({result.tipo_saldo})</Typography>
            <Table sx={{ mt: 2 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Tipo IVA</TableCell>
                  <TableCell align="right">Devengado</TableCell>
                  <TableCell align="right">Deducible</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(result.breakdown).map(([rate, b]) => (
                  <TableRow key={rate}>
                    <TableCell>{rate}%</TableCell>
                    <TableCell align="right">{b.devengado.toFixed(2)}</TableCell>
                    <TableCell align="right">{b.deducible.toFixed(2)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        )}
      </Container>
    </>
  );
}
