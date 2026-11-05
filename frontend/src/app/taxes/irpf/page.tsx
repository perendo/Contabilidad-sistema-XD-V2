"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import { isAuthenticated, clearSession, api, errorMessage } from "@/lib/api";
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";

type IrpfSummary = {
  year: number;
  quarter: number;
  modelo_111: { base: number; retenciones_a_ingresar: number };
  pagos_a_cuenta_130: { base: number; retenciones_soportadas: number };
  facturas_emitidas_count: number;
  facturas_recibidas_count: number;
};

export default function IrpfPage() {
  const router = useRouter();
  const { mode, toggle } = useThemeMode();
  const [year, setYear] = useState("");
  const [quarter, setQuarter] = useState("1");
  const [result, setResult] = useState<IrpfSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // El año actual se calcula tras el montaje: `new Date()` no es estable
    // durante el prerender de Next.js.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setYear(String(new Date().getFullYear()));
    if (!isAuthenticated()) router.push("/login");
  }, [router]);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ year, quarter });
      setResult(await api(`/irpf-summary?${params.toString()}`));
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
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>Retenciones IRPF (Mod. 111)</Typography>
          <Button color="inherit" onClick={toggle}>{mode === "dark" ? "Claro" : "Oscuro"}</Button>
          <Button color="inherit" href="/">Panel</Button>
          <Button color="inherit" onClick={logout}>Salir</Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }} maxWidth="md">
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
            <TextField
              label="Ejercicio"
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              slotProps={{ inputLabel: { shrink: true }, htmlInput: { min: 2000, max: 2100 } }}
              sx={{ width: 130 }}
            />
            <FormControl sx={{ minWidth: 110 }}>
              <InputLabel id="quarter-label">Trimestre</InputLabel>
              <Select
                labelId="quarter-label"
                label="Trimestre"
                value={quarter}
                onChange={(e) => setQuarter(e.target.value)}
              >
                <MenuItem value="1">1T</MenuItem>
                <MenuItem value="2">2T</MenuItem>
                <MenuItem value="3">3T</MenuItem>
                <MenuItem value="4">4T</MenuItem>
              </Select>
            </FormControl>
            <Button variant="contained" onClick={load} disabled={loading}>Consultar</Button>
          </Box>
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        </Paper>
        {loading ? <CircularProgress /> : result && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Resumen {result.quarter}T {result.year}
            </Typography>
            <Table sx={{ mt: 1 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Modelo</TableCell>
                  <TableCell align="right">Base</TableCell>
                  <TableCell align="right">Retenciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Modelo 111 (retenciones practicadas)</TableCell>
                  <TableCell align="right">{result.modelo_111.base.toFixed(2)}</TableCell>
                  <TableCell align="right">{result.modelo_111.retenciones_a_ingresar.toFixed(2)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Pagos a cuenta 130 (retenciones soportadas)</TableCell>
                  <TableCell align="right">{result.pagos_a_cuenta_130.base.toFixed(2)}</TableCell>
                  <TableCell align="right">{result.pagos_a_cuenta_130.retenciones_soportadas.toFixed(2)}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
            <Box sx={{ mt: 2, display: "flex", flexDirection: "column", gap: 0.5 }}>
              <Typography variant="body2" color="text.secondary">
                Facturas recibidas con retención: {result.facturas_recibidas_count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Facturas emitidas con retención: {result.facturas_emitidas_count}
              </Typography>
            </Box>
          </Paper>
        )}
      </Container>
    </>
  );
}
