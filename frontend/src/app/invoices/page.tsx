"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import PaginationBar from "@/components/PaginationBar";
import ErrorAlert from "@/components/ErrorAlert";
import { isAuthenticated, clearSession, api, errorMessage } from "@/lib/api";
import { formatAmount, formatEuro, parseAmount } from "@/lib/format";
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
  Select,
  MenuItem,
  InputLabel,
  FormControl,
} from "@mui/material";

type ThirdParty = {
  id: number;
  name: string;
  tax_id: string;
  type: string;
};

type Invoice = {
  id: number;
  year: number;
  number: number;
  date: string;
  third_party_id: number;
  description: string;
  base_amount: number;
  vat_rate: number;
  vat_amount: number;
  total: number;
  entry_id: number | null;
};

const VAT_RATES = [21, 10, 4, 0];

const emptyForm = () => ({
  date: "",
  third_party_id: "",
  description: "",
  base_amount: "",
  vat_rate: "21",
});

function invoiceNumber(invoice: Invoice): string {
  return `${invoice.year}/${String(invoice.number).padStart(4, "0")}`;
}

function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

const PAGE_SIZE = 50;

export default function InvoicesPage() {
  const router = useRouter();
  const { mode, toggle } = useThemeMode();
  const [clients, setClients] = useState<ThirdParty[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [form, setForm] = useState(emptyForm());

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    // La fecha actual se calcula tras el montaje: `new Date()` no es estable
    // durante el prerender de Next.js.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setForm((prev) => ({
      ...prev,
      date: new Date().toLocaleDateString("sv-SE"),
    }));
    load();
  }, [router]);

  async function load(nextPage = page) {
    try {
      const [parties, invs] = await Promise.all([
        api("/third-parties?type=Cliente"),
        api(`/invoices?limit=${PAGE_SIZE}&offset=${nextPage * PAGE_SIZE}`),
      ]);
      setClients(parties);
      setInvoices(invs);
      setHasMore(invs.length === PAGE_SIZE);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  function goToPage(nextPage: number) {
    setPage(nextPage);
    load(nextPage);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!form.third_party_id) {
      setError("Selecciona un cliente");
      return;
    }
    setSubmitting(true);
    try {
      await api("/invoices", {
        method: "POST",
        body: JSON.stringify({
          date: form.date,
          third_party_id: Number(form.third_party_id),
          description: form.description,
          base_amount: parseAmount(form.base_amount),
          vat_rate: Number(form.vat_rate),
        }),
      });
      setForm({ ...emptyForm(), date: form.date });
      load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function logout() {
    await clearSession();
    router.push("/login");
  }

  if (!isAuthenticated()) return null;

  const clientName = (id: number) =>
    clients.find((c) => c.id === id)?.name ?? "—";

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Facturas emitidas
          </Typography>
          <Button color="inherit" onClick={toggle}>
            {mode === "dark" ? "Claro" : "Oscuro"}
          </Button>
          <Button color="inherit" href="/">
            Panel
          </Button>
          <Button color="inherit" href="/journal">
            Libro diario
          </Button>
          <Button color="inherit" onClick={logout}>
            Salir
          </Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }} maxWidth="lg">
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Nueva factura emitida
          </Typography>
          <Box component="form" onSubmit={handleCreate} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
              <TextField
                label="Fecha"
                type="date"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
                required
                slotProps={{ inputLabel: { shrink: true } }}
              />
              <FormControl sx={{ minWidth: 260 }}>
                <InputLabel id="client-label">Cliente</InputLabel>
                <Select
                  id="client"
                  labelId="client-label"
                  value={form.third_party_id}
                  label="Cliente"
                  displayEmpty
                  onChange={(e) => setForm({ ...form, third_party_id: e.target.value })}
                >
                  <MenuItem value="">
                    <em>Selecciona un cliente</em>
                  </MenuItem>
                  {clients.map((c) => (
                    <MenuItem key={c.id} value={String(c.id)}>
                      {c.name} · {c.tax_id}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                label="Concepto"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                sx={{ minWidth: 240, flexGrow: 1 }}
              />
            </Box>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
              <TextField
                label="Base imponible"
                type="text"
                inputMode="decimal"
                placeholder="0,00"
                value={form.base_amount}
                onChange={(e) => setForm({ ...form, base_amount: e.target.value })}
                onBlur={() =>
                  setForm({
                    ...form,
                    base_amount: form.base_amount ? formatAmount(parseAmount(form.base_amount)) : "",
                  })
                }
                required
                sx={{ width: 160 }}
              />
              <FormControl sx={{ minWidth: 140 }}>
                <InputLabel id="vat-rate-label">Tipo de IVA</InputLabel>
                <Select
                  id="vat-rate"
                  labelId="vat-rate-label"
                  value={form.vat_rate}
                  label="Tipo de IVA"
                  onChange={(e) => setForm({ ...form, vat_rate: e.target.value })}
                >
                  {VAT_RATES.map((rate) => (
                    <MenuItem key={rate} value={String(rate)}>
                      {rate}%
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button type="submit" variant="contained" disabled={submitting}>
                {submitting ? "Creando..." : "Crear factura"}
              </Button>
            </Box>
          </Box>
          <ErrorAlert message={error} sx={{ mt: 2 }} />
        </Paper>

        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Número</TableCell>
                <TableCell>Fecha</TableCell>
                <TableCell>Cliente</TableCell>
                <TableCell>Concepto</TableCell>
                <TableCell align="right">Base</TableCell>
                <TableCell align="right">IVA</TableCell>
                <TableCell align="right">Total</TableCell>
                <TableCell>Asiento</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {invoices.map((invoice) => (
                <TableRow key={invoice.id}>
                  <TableCell>{invoiceNumber(invoice)}</TableCell>
                  <TableCell>{formatDate(invoice.date)}</TableCell>
                  <TableCell>{clientName(invoice.third_party_id)}</TableCell>
                  <TableCell>{invoice.description}</TableCell>
                  <TableCell align="right">{formatEuro(invoice.base_amount)}</TableCell>
                  <TableCell align="right">
                    {invoice.vat_rate}% · {formatEuro(invoice.vat_amount)}
                  </TableCell>
                  <TableCell align="right">{formatEuro(invoice.total)}</TableCell>
                  <TableCell>{invoice.entry_id ? `#${invoice.entry_id}` : "—"}</TableCell>
                </TableRow>
              ))}
              {invoices.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    Sin facturas emitidas
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
