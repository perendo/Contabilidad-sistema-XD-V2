"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import { isAuthenticated, clearSession, api } from "@/lib/api";
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

type ThirdParty = {
  third_party_id: number;
  tax_id: string;
  name: string;
  total_annual: number;
};

type Modelo347 = {
  year: number;
  threshold: number;
  third_parties: ThirdParty[];
};

export default function Modelo347Page() {
  const router = useRouter();
  const { mode, toggle } = useThemeMode();
  const [year, setYear] = useState("");
  const [threshold, setThreshold] = useState("3005.06");
  const [result, setResult] = useState<Modelo347 | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setYear(String(new Date().getFullYear()));
    if (!isAuthenticated()) router.push("/login");
  }, [router]);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ year, threshold });
      setResult(await api(`/modelo-347?${params.toString()}`));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    await clearSession();
    router.push("/login");
  }

  if (!isAuthenticated()) return null;

  const total = result
    ? result.third_parties.reduce((acc, tp) => acc + tp.total_annual, 0)
    : 0;

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>Modelo 347 Anual</Typography>
          <Button color="inherit" onClick={toggle}>{mode === "dark" ? "Claro" : "Oscuro"}</Button>
          <Button color="inherit" href="/">Panel</Button>
          <Button color="inherit" onClick={logout}>Salir</Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }} maxWidth="lg">
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
            <TextField
              label="Umbral (€)"
              type="number"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              slotProps={{ inputLabel: { shrink: true }, htmlInput: { min: 0, step: "0.01" } }}
              sx={{ width: 170 }}
            />
            <Button variant="contained" onClick={load} disabled={loading}>Consultar</Button>
          </Box>
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        </Paper>
        {loading ? <CircularProgress /> : result && (
          <Paper>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>NIF/CIF</TableCell>
                  <TableCell>Nombre</TableCell>
                  <TableCell align="right">Total anual</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {result.third_parties.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={3}>
                      <Typography color="text.secondary">
                        Ningún tercero supera el umbral de {result.threshold.toFixed(2)} €.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
                {result.third_parties.map((tp) => (
                  <TableRow key={tp.third_party_id}>
                    <TableCell sx={{ fontFamily: "monospace" }}>{tp.tax_id}</TableCell>
                    <TableCell>{tp.name}</TableCell>
                    <TableCell align="right">{tp.total_annual.toFixed(2)}</TableCell>
                  </TableRow>
                ))}
                {result.third_parties.length > 0 && (
                  <TableRow>
                    <TableCell colSpan={2}><strong>TOTAL</strong></TableCell>
                    <TableCell align="right"><strong>{total.toFixed(2)}</strong></TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Paper>
        )}
      </Container>
    </>
  );
}
