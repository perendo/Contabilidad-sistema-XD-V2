"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import { getToken, clearToken, api } from "@/lib/api";
import { NAV_ITEMS, type NavIcon } from "@/lib/nav";
import MenuBookIcon from "@mui/icons-material/MenuBook";
import FilterListIcon from "@mui/icons-material/FilterList";
import ArrowOutwardIcon from "@mui/icons-material/ArrowOutward";
import CallReceivedIcon from "@mui/icons-material/CallReceived";
import BalanceIcon from "@mui/icons-material/Balance";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import ShieldIcon from "@mui/icons-material/Shield";
import PeopleIcon from "@mui/icons-material/People";
import DownloadIcon from "@mui/icons-material/Download";
import type { SvgIconComponent } from "@mui/icons-material";
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";

const NAV_ICONS: Record<NavIcon, SvgIconComponent> = {
  book: MenuBookIcon,
  list: FilterListIcon,
  up: ArrowOutwardIcon,
  down: CallReceivedIcon,
  scale: BalanceIcon,
  trending: TrendingUpIcon,
  receipt: ReceiptLongIcon,
  shield: ShieldIcon,
  users: PeopleIcon,
  download: DownloadIcon,
};

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [company, setCompany] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState<string | null>(null);
  const [availableYears, setAvailableYears] = useState<string[]>([]);
  const { mode, toggle } = useThemeMode();

  useEffect(() => {
    if (typeof window !== "undefined") {
      setSelectedYear(sessionStorage.getItem("fiscal_year_selected"));
      try {
        const stored = sessionStorage.getItem("fiscal_years_available");
        if (stored) setAvailableYears(JSON.parse(stored));
      } catch {
        setAvailableYears([]);
      }
    }
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
        const configured = String(c.fiscal_year);
        setAvailableYears((prev) => {
          const base = prev.length ? prev : [];
          const next = base.includes(configured) ? base : [configured, ...base];
          if (typeof window !== "undefined") {
            sessionStorage.setItem("fiscal_years_available", JSON.stringify(next));
          }
          return next;
        });
        setSelectedYear((prev) => {
          if (prev) return prev;
          const def = configured;
          if (typeof window !== "undefined") {
            sessionStorage.setItem("fiscal_year_selected", def);
          }
          return def;
        });
      } catch {
        setCompany(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  function logout() {
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("fiscal_year_selected");
      sessionStorage.removeItem("fiscal_years_available");
    }
    clearToken();
    router.push("/login");
  }

  function chooseFiscalYear(year: string) {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("fiscal_year_selected", year);
    }
    setSelectedYear(year);
  }

  function addFiscalYear(year: string) {
    const trimmed = year.trim();
    if (!/^\d{4}$/.test(trimmed)) return;
    setAvailableYears((prev) => {
      if (prev.includes(trimmed)) return prev;
      const next = [...prev, trimmed].sort();
      if (typeof window !== "undefined") {
        sessionStorage.setItem("fiscal_years_available", JSON.stringify(next));
      }
      return next;
    });
    chooseFiscalYear(trimmed);
  }

  if (!getToken()) return null;

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Panel
          </Typography>
          {selectedYear && (
            <FormControl size="small" sx={{ mr: 2, minWidth: 110 }}>
              <InputLabel id="fiscal-year-label" sx={{ color: "inherit" }}>
                Ejercicio
              </InputLabel>
              <Select
                labelId="fiscal-year-label"
                value={selectedYear}
                label="Ejercicio"
                onChange={(e) => {
                  const value = e.target.value as string;
                  if (value === "__add__") {
                    const input = window.prompt("Nuevo ejercicio (año de 4 dígitos):");
                    if (input) addFiscalYear(input);
                  } else {
                    chooseFiscalYear(value);
                  }
                }}
                sx={{ color: "inherit", ".MuiOutlinedInput-notchedOutline": { borderColor: "rgba(255,255,255,0.5)" } }}
              >
                {availableYears.map((year) => (
                  <MenuItem key={year} value={year}>
                    {year}
                  </MenuItem>
                ))}
                <MenuItem value="__add__">Añadir ejercicio…</MenuItem>
              </Select>
            </FormControl>
          )}
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
                <Typography><strong>Periodo fiscal configurado:</strong> {company.fiscal_year}</Typography>
                {selectedYear && (
                  <Typography><strong>Ejercicio activo:</strong> {selectedYear}</Typography>
                )}
              </Box>
            ) : (
              <CompanyForm onSaved={setCompany} />
            )}
          </Paper>
        )}
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Accesos
          </Typography>
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr", md: "1fr 1fr 1fr" },
              gap: 2,
            }}
          >
            {NAV_ITEMS.map((item) => {
              const Icon = NAV_ICONS[item.icon];
              return (
                <Button
                  key={item.href}
                  component={Link}
                  href={item.href}
                  variant="outlined"
                  startIcon={<Icon />}
                  sx={{ justifyContent: "flex-start", textTransform: "none", py: 1.5 }}
                >
                  {item.label}
                </Button>
              );
            })}
          </Box>
        </Paper>
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
