"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import ErrorAlert from "@/components/ErrorAlert";
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
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  CircularProgress,
} from "@mui/material";

type Row = { code: string; name: string; debe: number; haber: number; saldo: number };

export default function BalancePage() {
  const router = useRouter();
  const { mode, toggle } = useThemeMode();
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [totalDebe, setTotalDebe] = useState(0);
  const [totalHaber, setTotalHaber] = useState(0);
  const [cuadrado, setCuadrado] = useState<boolean | null>(null);
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
      const data = await api(`/balance-sumas-saldos?${params.toString()}`);
      setRows(data.accounts);
      setTotalDebe(data.total_debe);
      setTotalHaber(data.total_haber);
      setCuadrado(data.cuadrado);
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
          <Typography variant="h6" sx={{ flexGrow: 1 }}>Balance de sumas y saldos</Typography>
          <Button color="inherit" onClick={toggle}>{mode === "dark" ? "Claro" : "Oscuro"}</Button>
          <Button color="inherit" href="/">Panel</Button>
          <Button color="inherit" onClick={logout}>Salir</Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }} maxWidth="lg">
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
            <TextField label="Desde" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
            <TextField label="Hasta" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
            <Button variant="contained" onClick={load} disabled={loading}>Consultar</Button>
          </Box>
          <ErrorAlert message={error} sx={{ mt: 2 }} />
        </Paper>
        {loading ? <CircularProgress /> : (
          <Paper>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Código</TableCell>
                  <TableCell>Nombre</TableCell>
                  <TableCell align="right">Debe</TableCell>
                  <TableCell align="right">Haber</TableCell>
                  <TableCell align="right">Saldo</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((r) => (
                  <TableRow key={r.code}>
                    <TableCell sx={{ fontFamily: "monospace" }}>{r.code}</TableCell>
                    <TableCell>{r.name}</TableCell>
                    <TableCell align="right">{r.debe.toFixed(2)}</TableCell>
                    <TableCell align="right">{r.haber.toFixed(2)}</TableCell>
                    <TableCell align="right">{r.saldo.toFixed(2)}</TableCell>
                  </TableRow>
                ))}
                <TableRow>
                  <TableCell colSpan={2}><strong>TOTAL</strong></TableCell>
                  <TableCell align="right"><strong>{totalDebe.toFixed(2)}</strong></TableCell>
                  <TableCell align="right"><strong>{totalHaber.toFixed(2)}</strong></TableCell>
                  <TableCell align="right"><strong>{(totalDebe - totalHaber).toFixed(2)}</strong></TableCell>
                </TableRow>
              </TableBody>
            </Table>
            {cuadrado !== null && (
              <Box sx={{ p: 2 }}>
                <Typography color={cuadrado ? "success.main" : "error.main"}>
                  {cuadrado ? "Cuadrado" : "No cuadrado"}
                </Typography>
              </Box>
            )}
          </Paper>
        )}
      </Container>
    </>
  );
}
