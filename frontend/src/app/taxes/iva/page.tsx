"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import { getToken, clearToken, api } from "@/lib/api";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Paper,
  Box,
  TextField,
  Alert,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  CircularProgress,
} from "@mui/material";

export default function IvaPage() {
  const router = useRouter();
  const { mode, toggle } = useThemeMode();
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) router.push("/login");
  }, [router]);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      setResult(await api(`/iva-liquidation?${params.toString()}`));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    clearToken();
    router.push("/login");
  }

  if (!getToken()) return null;

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>Liquidación IVA (Mod. 303)</Typography>
          <Button color="inherit" onClick={toggle}>{mode === "dark" ? "Claro" : "Oscuro"}</Button>
          <Button color="inherit" href="/">Panel</Button>
          <Button color="inherit" onClick={logout}>Salir</Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }} maxWidth="md">
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
            <TextField label="Desde" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
            <TextField label="Hasta" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
            <Button variant="contained" onClick={load} disabled={loading}>Consultar</Button>
          </Box>
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
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
                {Object.entries(result.breakdown).map(([rate, b]: any) => (
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
