"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
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
  Alert,
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

type Account = {
  id: number;
  code: string;
  name: string;
  type: string;
  is_detail: boolean;
};

type ReceivedInvoice = {
  id: number;
  date: string;
  third_party_id: number;
  supplier_number: string;
  description: string;
  base_amount: number;
  vat_rate: number;
  vat_amount: number;
  total: number;
  expense_account_id: number;
  entry_id: number | null;
};

const VAT_RATES = [21, 10, 4, 0];

const emptyForm = () => ({
  date: "",
  third_party_id: "",
  supplier_number: "",
  description: "",
  base_amount: "",
  vat_rate: "21",
  expense_account_id: "",
});

function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

export default function ReceivedInvoicesPage() {
  const router = useRouter();
  const { mode, toggle } = useThemeMode();
  const [suppliers, setSuppliers] = useState<ThirdParty[]>([]);
  const [expenseAccounts, setExpenseAccounts] = useState<Account[]>([]);
  const [invoices, setInvoices] = useState<ReceivedInvoice[]>([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
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

  async function load() {
    try {
      const [parties, accounts, invs] = await Promise.all([
        api("/third-parties?type=Proveedor"),
        api("/accounts?limit=500"),
        api("/received-invoices"),
      ]);
      setSuppliers(parties);
      setExpenseAccounts(
        accounts.filter((a: Account) => a.type === "Gasto" && a.is_detail)
      );
      setInvoices(invs);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!form.third_party_id) {
      setError("Selecciona un proveedor");
      return;
    }
    if (!form.expense_account_id) {
      setError("Selecciona una cuenta de gasto");
      return;
    }
    setSubmitting(true);
    try {
      await api("/received-invoices", {
        method: "POST",
        body: JSON.stringify({
          date: form.date,
          third_party_id: Number(form.third_party_id),
          supplier_number: form.supplier_number,
          description: form.description,
          base_amount: parseAmount(form.base_amount),
          vat_rate: Number(form.vat_rate),
          expense_account_id: Number(form.expense_account_id),
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

  const supplierName = (id: number) =>
    suppliers.find((s) => s.id === id)?.name ?? "—";

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Facturas recibidas
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
          <Button color="inherit" href="/invoices">
            Facturas emitidas
          </Button>
          <Button color="inherit" onClick={logout}>
            Salir
          </Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }} maxWidth="lg">
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Nueva factura recibida
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
              <FormControl sx={{ minWidth: 240 }}>
                <InputLabel id="supplier-label">Proveedor</InputLabel>
                <Select
                  id="supplier"
                  labelId="supplier-label"
                  value={form.third_party_id}
                  label="Proveedor"
                  displayEmpty
                  onChange={(e) => setForm({ ...form, third_party_id: e.target.value })}
                >
                  <MenuItem value="">
                    <em>Selecciona un proveedor</em>
                  </MenuItem>
                  {suppliers.map((s) => (
                    <MenuItem key={s.id} value={String(s.id)}>
                      {s.name} · {s.tax_id}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                label="Nº factura del proveedor"
                value={form.supplier_number}
                onChange={(e) => setForm({ ...form, supplier_number: e.target.value })}
                required
                sx={{ minWidth: 200 }}
              />
              <TextField
                label="Concepto"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                sx={{ minWidth: 220, flexGrow: 1 }}
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
              <FormControl sx={{ minWidth: 280 }}>
                <InputLabel id="expense-account-label">Cuenta de gasto</InputLabel>
                <Select
                  id="expense-account"
                  labelId="expense-account-label"
                  value={form.expense_account_id}
                  label="Cuenta de gasto"
                  displayEmpty
                  onChange={(e) => setForm({ ...form, expense_account_id: e.target.value })}
                >
                  <MenuItem value="">
                    <em>Selecciona una cuenta de gasto</em>
                  </MenuItem>
                  {expenseAccounts.map((a) => (
                    <MenuItem key={a.id} value={String(a.id)}>
                      {a.code} · {a.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button type="submit" variant="contained" disabled={submitting}>
                {submitting ? "Creando..." : "Crear factura"}
              </Button>
            </Box>
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
                <TableCell>Nº proveedor</TableCell>
                <TableCell>Fecha</TableCell>
                <TableCell>Proveedor</TableCell>
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
                  <TableCell>{invoice.supplier_number}</TableCell>
                  <TableCell>{formatDate(invoice.date)}</TableCell>
                  <TableCell>{supplierName(invoice.third_party_id)}</TableCell>
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
                    Sin facturas recibidas
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Paper>
      </Container>
    </>
  );
}
