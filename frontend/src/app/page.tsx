"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import {
  isAuthenticated,
  clearSession,
  api,
  errorMessage,
  getActiveCompanyId,
  setActiveCompanyId,
} from "@/lib/api";
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
import UploadFileIcon from "@mui/icons-material/UploadFile";
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
  upload: UploadFileIcon,
};

type User = {
  email: string;
};

type Company = {
  id: number;
  name: string;
  tax_id: string;
  address: string;
  fiscal_year: string | number;
};

type CompanyFormValues = {
  name: string;
  tax_id: string;
  address: string;
  fiscal_year: string;
};

export default function HomePage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeCompanyId, setActiveCompanyIdState] = useState<number | null>(() => {
    const stored = getActiveCompanyId();
    return stored ? Number(stored) : null;
  });
  const [company, setCompany] = useState<Company | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return sessionStorage.getItem("fiscal_year_selected");
  });
  const [availableYears, setAvailableYears] = useState<string[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const stored = sessionStorage.getItem("fiscal_years_available");
      return stored ? (JSON.parse(stored) as string[]) : [];
    } catch {
      return [];
    }
  });
  const [showCompanyForm, setShowCompanyForm] = useState(false);
  const [editingCompany, setEditingCompany] = useState(false);
  const { mode, toggle } = useThemeMode();

  function applyFiscalYear(configured: string) {
    const next = [configured];
    if (typeof window !== "undefined") {
      sessionStorage.setItem("fiscal_years_available", JSON.stringify(next));
      sessionStorage.setItem("fiscal_year_selected", configured);
    }
    setAvailableYears(next);
    setSelectedYear(configured);
  }

  async function activateCompany(c: Company) {
    setActiveCompanyId(c.id);
    setActiveCompanyIdState(c.id);
    try {
      const fresh = await api("/company");
      setCompany(fresh);
      applyFiscalYear(String(fresh.fiscal_year));
    } catch {
      setCompany(c);
      applyFiscalYear(String(c.fiscal_year));
    }
  }

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    (async () => {
      try {
        const u = await api("/auth/me");
        setUser(u);
      } catch {
        await clearSession();
        router.push("/login");
        return;
      }
      try {
        const list = (await api("/companies")) as Company[];
        setCompanies(list);
        const stored = getActiveCompanyId();
        let toActivate: Company | null = null;
        if (stored) {
          toActivate = list.find((c) => String(c.id) === stored) || null;
        }
        if (!toActivate && list.length === 1) {
          toActivate = list[0];
        }
        if (toActivate) {
          await activateCompany(toActivate);
          setShowCompanyForm(false);
        } else {
          setActiveCompanyId(null);
          setActiveCompanyIdState(null);
          setCompany(null);
          setShowCompanyForm(list.length === 0);
        }
      } catch {
        setCompanies([]);
        setCompany(null);
        setShowCompanyForm(true);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  useEffect(() => {
    setMounted(true);
  }, []);

  async function logout() {
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("fiscal_year_selected");
      sessionStorage.removeItem("fiscal_years_available");
      setActiveCompanyId(null);
    }
    await clearSession();
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

  async function handleCreateCompany(values: CompanyFormValues) {
    const created = (await api("/companies", {
      method: "POST",
      body: JSON.stringify(values),
    })) as Company;
    setCompanies((prev) => [...prev, created]);
    await activateCompany(created);
    setShowCompanyForm(false);
  }

  async function handleEditCompany(values: CompanyFormValues) {
    const updated = (await api("/company", {
      method: "PUT",
      body: JSON.stringify(values),
    })) as Company;
    setCompany(updated);
    setCompanies((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    const configured = String(updated.fiscal_year);
    setAvailableYears((prev) => (prev.includes(configured) ? prev : [...prev, configured].sort()));
    if (typeof window !== "undefined") {
      const stored = sessionStorage.getItem("fiscal_years_available");
      const list = stored ? (JSON.parse(stored) as string[]) : [];
      if (!list.includes(configured)) {
        const next = [...list, configured].sort();
        sessionStorage.setItem("fiscal_years_available", JSON.stringify(next));
      }
    }
    setEditingCompany(false);
  }

  function handleSwitchCompany() {
    setActiveCompanyId(null);
    setActiveCompanyIdState(null);
    setCompany(null);
    setShowCompanyForm(false);
    setEditingCompany(false);
  }

  if (!mounted || !isAuthenticated()) return null;

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
          <>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Sociedad activa
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
                  <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
                    <Button variant="outlined" onClick={() => setEditingCompany(true)}>
                      Editar sociedad
                    </Button>
                    <Button variant="text" onClick={handleSwitchCompany}>
                      Cambiar sociedad
                    </Button>
                  </Box>
                  {editingCompany && (
                    <Box sx={{ mt: 2 }}>
                      <CompanyForm
                        initial={{
                          name: company.name,
                          tax_id: company.tax_id,
                          address: company.address,
                          fiscal_year: String(company.fiscal_year),
                        }}
                        submitLabel="Guardar cambios"
                        onSubmit={handleEditCompany}
                        onCancel={() => setEditingCompany(false)}
                      />
                    </Box>
                  )}
                </Box>
              ) : showCompanyForm ? (
                <CompanyForm
                  initial={{ name: "", tax_id: "", address: "", fiscal_year: "" }}
                  submitLabel={companies.length === 0 ? "Crear sociedad" : "Crear nueva sociedad"}
                  onSubmit={handleCreateCompany}
                  onCancel={companies.length > 0 ? () => setShowCompanyForm(false) : undefined}
                />
              ) : (
                <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  <Typography>Selecciona la sociedad con la que quieres trabajar:</Typography>
                  {companies.map((c) => (
                    <Paper key={c.id} variant="outlined" sx={{ p: 2, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <Box>
                        <Typography><strong>{c.name}</strong></Typography>
                        <Typography variant="body2" color="text.secondary">
                          {c.tax_id} · {c.address} · Ejercicio {c.fiscal_year}
                        </Typography>
                      </Box>
                      <Button variant="contained" onClick={() => activateCompany(c)}>
                        Seleccionar
                      </Button>
                    </Paper>
                  ))}
                  <Button variant="outlined" onClick={() => setShowCompanyForm(true)}>
                    Nueva sociedad
                  </Button>
                </Box>
              )}
            </Paper>
            {company && (
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
            )}
          </>
        )}
      </Container>
    </>
  );
}

type CompanyFormProps = {
  initial: CompanyFormValues;
  submitLabel: string;
  onSubmit: (values: CompanyFormValues) => Promise<void>;
  onCancel?: () => void;
};

function CompanyForm({ initial, submitLabel, onSubmit, onCancel }: CompanyFormProps) {
  const [form, setForm] = useState<CompanyFormValues>(initial);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await onSubmit(form);
    } catch (err) {
      setError(errorMessage(err));
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
      <Box sx={{ display: "flex", gap: 1 }}>
        <Button type="submit" variant="contained" disabled={loading}>
          {loading ? "Guardando..." : submitLabel}
        </Button>
        {onCancel && (
          <Button type="button" variant="text" onClick={onCancel} disabled={loading}>
            Cancelar
          </Button>
        )}
      </Box>
    </Box>
  );
}
