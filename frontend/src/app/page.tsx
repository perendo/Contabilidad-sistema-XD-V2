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
  CircularProgress,
} from "@mui/material";

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [company, setCompany] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { mode, toggle } = useThemeMode();

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    (async () => {
      try {
        const u = await api("/auth/me");
        setUser(u);
      } catch {
        clearToken();
        router.push("/login");
        return;
      }
      try {
        const c = await api("/company");
        setCompany(c);
      } catch {
        setCompany(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  function logout() {
    clearToken();
    router.push("/login");
  }

  if (!getToken()) return null;

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Panel
          </Typography>
          <Button color="inherit" onClick={toggle}>
            {mode === "dark" ? "Claro" : "Oscuro"}
          </Button>
          <Button color="inherit" onClick={logout}>
            Salir
          </Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }}>
        {user && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Usuario: {user.email}
          </Typography>
        )}
        {loading ? (
          <CircularProgress />
        ) : (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Empresa
            </Typography>
            {company ? (
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <Typography><strong>Nombre:</strong> {company.name}</Typography>
                <Typography><strong>NIF/CIF:</strong> {company.tax_id}</Typography>
                <Typography><strong>Dirección:</strong> {company.address}</Typography>
                <Typography><strong>Periodo fiscal:</strong> {company.fiscal_year}</Typography>
              </Box>
            ) : (
              <CompanyForm onSaved={setCompany} />
            )}
          </Paper>
        )}
        <Box sx={{ mt: 3, display: "flex", gap: 2 }}>
          <Button variant="contained" href="/accounts">
            Plan de cuentas
          </Button>
          <Button variant="contained" href="/journal">
            Libro diario
          </Button>
          <Button variant="contained" href="/invoices">
            Facturas emitidas
          </Button>
        </Box>
      </Container>
    </>
  );
}

function CompanyForm({ onSaved }: { onSaved: (c: any) => void }) {
  const [form, setForm] = useState({
    name: "",
    tax_id: "",
    address: "",
    fiscal_year: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const c = await api("/company", {
        method: "PUT",
        body: JSON.stringify(form),
      });
      onSaved(c);
    } catch (err: any) {
      setError(err.message || "Error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <TextField
        label="Nombre fiscal"
        value={form.name}
        onChange={(e) => setForm({ ...form, name: e.target.value })}
        required
        fullWidth
      />
      <TextField
        label="NIF/CIF"
        value={form.tax_id}
        onChange={(e) => setForm({ ...form, tax_id: e.target.value })}
        required
        fullWidth
      />
      <TextField
        label="Dirección"
        value={form.address}
        onChange={(e) => setForm({ ...form, address: e.target.value })}
        required
        fullWidth
      />
      <TextField
        label="Periodo fiscal (ej. 2026)"
        value={form.fiscal_year}
        onChange={(e) => setForm({ ...form, fiscal_year: e.target.value })}
        required
        fullWidth
      />
      {error && <Alert severity="error">{error}</Alert>}
      <Button type="submit" variant="contained" disabled={loading}>
        {loading ? "Guardando..." : "Guardar empresa"}
      </Button>
    </Box>
  );
}
