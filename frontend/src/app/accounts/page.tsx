"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import PaginationBar from "@/components/PaginationBar";
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
  Checkbox,
  FormControlLabel,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
} from "@mui/material";

type Account = {
  id: number;
  code: string;
  name: string;
  type: string;
  level: number;
  is_detail: boolean;
  parent_id: number | null;
};

const TYPES = ["Activo", "Pasivo", "Patrimonio Neto", "Ingreso", "Gasto"];
const PAGE_SIZE = 50;

export default function AccountsPage() {
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [search, setSearch] = useState("");
  const { mode, toggle } = useThemeMode();
  const [error, setError] = useState("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [form, setForm] = useState({
    code: "",
    name: "",
    type: "Activo",
    level: 1,
    is_detail: false,
    parent_id: "",
  });

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    load();
  }, [router]);

  async function load(q?: string, nextPage = page) {
    try {
      const params = new URLSearchParams();
      if (q) params.set("search", q);
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String(nextPage * PAGE_SIZE));
      const data = await api(`/accounts?${params.toString()}`);
      setAccounts(data);
      setHasMore(data.length === PAGE_SIZE);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  function goToPage(nextPage: number) {
    setPage(nextPage);
    load(search, nextPage);
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(0);
    load(search, 0);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/accounts", {
        method: "POST",
        body: JSON.stringify({
          code: form.code,
          name: form.name,
          type: form.type,
          level: Number(form.level),
          is_detail: form.is_detail,
          parent_id: form.parent_id ? Number(form.parent_id) : null,
        }),
      });
      setForm({ code: "", name: "", type: "Activo", level: 1, is_detail: false, parent_id: "" });
      load(search);
    } catch (err) {
      setError(errorMessage(err));
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
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Plan de cuentas
          </Typography>
          <Button color="inherit" onClick={toggle}>
            {mode === "dark" ? "Claro" : "Oscuro"}
          </Button>
          <Button color="inherit" href="/">
            Panel
          </Button>
          <Button color="inherit" onClick={logout}>
            Salir
          </Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }} maxWidth="lg">
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box component="form" onSubmit={handleSearch} sx={{ display: "flex", gap: 2 }}>
            <TextField
              label="Buscar por código o nombre"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              fullWidth
            />
            <Button type="submit" variant="outlined">
              Buscar
            </Button>
          </Box>
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Nueva cuenta
          </Typography>
          <Box component="form" onSubmit={handleCreate} sx={{ display: "flex", flexWrap: "wrap", gap: 2, alignItems: "center" }}>
            <TextField
              label="Código"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              required
              sx={{ minWidth: 120 }}
            />
            <TextField
              label="Nombre"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
              sx={{ minWidth: 220, flexGrow: 1 }}
            />
            <FormControl sx={{ minWidth: 160 }}>
              <InputLabel>Tipo</InputLabel>
              <Select
                value={form.type}
                label="Tipo"
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                {TYPES.map((t) => (
                  <MenuItem key={t} value={t}>
                    {t}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Nivel"
              type="number"
              value={form.level}
              onChange={(e) => setForm({ ...form, level: Number(e.target.value) })}
              required
              sx={{ width: 90 }}
              slotProps={{ htmlInput: { min: 1, max: 8 } }}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={form.is_detail}
                  onChange={(e) => setForm({ ...form, is_detail: e.target.checked })}
                />
              }
              label="Registro"
            />
            <TextField
              label="ID padre (opcional)"
              value={form.parent_id}
              onChange={(e) => setForm({ ...form, parent_id: e.target.value })}
              sx={{ width: 140 }}
            />
            <Button type="submit" variant="contained">
              Crear
            </Button>
          </Box>
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </Paper>

        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Código</TableCell>
                <TableCell>Nombre</TableCell>
                <TableCell>Tipo</TableCell>
                <TableCell>Nivel</TableCell>
                <TableCell>Registro</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {accounts.map((a) => (
                <TableRow key={a.id}>
                  <TableCell sx={{ fontFamily: "monospace" }}>{a.code}</TableCell>
                  <TableCell>{a.name}</TableCell>
                  <TableCell>{a.type}</TableCell>
                  <TableCell>{a.level}</TableCell>
                  <TableCell>{a.is_detail ? "Sí" : "No"}</TableCell>
                </TableRow>
              ))}
              {accounts.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    Sin cuentas
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Paper>
        <PaginationBar
          page={page}
          hasMore={hasMore}
          onPrevious={() => goToPage(page - 1)}
          onNext={() => goToPage(page + 1)}
        />
      </Container>
    </>
  );
}
