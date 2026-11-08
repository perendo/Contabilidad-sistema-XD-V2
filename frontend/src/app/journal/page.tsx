"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import PaginationBar from "@/components/PaginationBar";
import ErrorAlert from "@/components/ErrorAlert";
import { isAuthenticated, clearSession, api, errorMessage } from "@/lib/api";
import { formatAmount, parseAmount } from "@/lib/format";
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
  Chip,
  Divider,
} from "@mui/material";

type Account = {
  id: number;
  code: string;
  name: string;
  type: string;
};

type JournalLine = {
  id: number;
  account_id: number;
  description: string;
  debit: number;
  credit: number;
};

type JournalEntry = {
  id: number;
  date: string;
  description: string;
  status: string;
  author: string | null;
  lines: JournalLine[];
};

type LineForm = {
  account_id: string;
  description: string;
  debit: string;
  credit: string;
};

const emptyLine = (): LineForm => ({ account_id: "", description: "", debit: "", credit: "" });

const STATUS_LABEL: Record<string, string> = {
  draft: "Borrador",
  accepted: "Aceptado",
  annulled: "Anulado",
};

const PAGE_SIZE = 50;

export default function JournalPage() {
  const router = useRouter();
  const { mode, toggle } = useThemeMode();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [error, setError] = useState("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [form, setForm] = useState(() => ({
    date: "",
    description: "",
    lines: [emptyLine(), emptyLine()],
  }));

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    // La fecha actual se calcula tras el montaje: `new Date()` no es estable
    // durante el prerender de Next.js.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setForm((prev) => ({ ...prev, date: new Date().toISOString().slice(0, 10) }));
    load();
  }, [router]);

  async function load(nextPage = page) {
    try {
      const [accs, ents] = await Promise.all([
        api("/accounts?limit=500"),
        api(`/journal-entries?limit=${PAGE_SIZE}&offset=${nextPage * PAGE_SIZE}`),
      ]);
      setAccounts(accs);
      setEntries(ents);
      setHasMore(ents.length === PAGE_SIZE);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  function goToPage(nextPage: number) {
    setPage(nextPage);
    load(nextPage);
  }

  function updateLine(index: number, patch: Partial<LineForm>) {
    setForm((prev) => ({
      ...prev,
      lines: prev.lines.map((line, i) => (i === index ? { ...line, ...patch } : line)),
    }));
  }

  function addLine() {
    setForm((prev) => ({ ...prev, lines: [...prev.lines, emptyLine()] }));
  }

  function removeLine(index: number) {
    setForm((prev) => ({ ...prev, lines: prev.lines.filter((_, i) => i !== index) }));
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/journal-entries", {
        method: "POST",
        body: JSON.stringify({
          date: form.date,
          description: form.description,
          lines: form.lines.map((line) => ({
            account_id: Number(line.account_id),
            description: line.description,
            debit: parseAmount(line.debit),
            credit: parseAmount(line.credit),
          })),
        }),
      });
      setForm({ date: "", description: "", lines: [emptyLine(), emptyLine()] });
      setForm((prev) => ({ ...prev, date: new Date().toISOString().slice(0, 10) }));
      load();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function logout() {
    await clearSession();
    router.push("/login");
  }

  if (!isAuthenticated()) return null;

  const totalDebit = form.lines.reduce((sum, l) => sum + parseAmount(l.debit), 0);
  const totalCredit = form.lines.reduce((sum, l) => sum + parseAmount(l.credit), 0);

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Libro diario
          </Typography>
          <Button color="inherit" onClick={toggle}>
            {mode === "dark" ? "Claro" : "Oscuro"}
          </Button>
          <Button color="inherit" href="/">
            Panel
          </Button>
          <Button color="inherit" href="/accounts">
            Plan de cuentas
          </Button>
          <Button color="inherit" onClick={logout}>
            Salir
          </Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }} maxWidth="lg">
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Nuevo asiento
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
              <TextField
                label="Concepto"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                fullWidth
                sx={{ flexGrow: 1 }}
              />
            </Box>

            <Divider />
            <Typography variant="subtitle2">Líneas</Typography>
            {form.lines.map((line, index) => (
              <Box key={index} sx={{ display: "flex", gap: 1, flexWrap: "wrap", alignItems: "center" }}>
                <FormControl sx={{ minWidth: 220 }}>
                  <InputLabel>Cuenta</InputLabel>
                  <Select
                    value={line.account_id}
                    label="Cuenta"
                    onChange={(e) => updateLine(index, { account_id: e.target.value })}
                    required
                  >
                    {accounts.map((a) => (
                      <MenuItem key={a.id} value={String(a.id)}>
                        {a.code} - {a.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <TextField
                  label="Detalle"
                  value={line.description}
                  onChange={(e) => updateLine(index, { description: e.target.value })}
                  sx={{ minWidth: 200, flexGrow: 1 }}
                />
                <TextField
                  label="Debe"
                  type="text"
                  inputMode="decimal"
                  placeholder="0,00"
                  value={line.debit}
                  onChange={(e) => updateLine(index, { debit: e.target.value })}
                  onBlur={() => updateLine(index, { debit: line.debit ? formatAmount(parseAmount(line.debit)) : "" })}
                  sx={{ width: 120 }}
                />
                <TextField
                  label="Haber"
                  type="text"
                  inputMode="decimal"
                  placeholder="0,00"
                  value={line.credit}
                  onChange={(e) => updateLine(index, { credit: e.target.value })}
                  onBlur={() => updateLine(index, { credit: line.credit ? formatAmount(parseAmount(line.credit)) : "" })}
                  sx={{ width: 120 }}
                />
                <Button onClick={() => removeLine(index)} disabled={form.lines.length <= 2}>
                  Quitar
                </Button>
              </Box>
            ))}
            <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
              <Button variant="outlined" onClick={addLine}>
                Añadir línea
              </Button>
              <Typography variant="body2" color={totalDebit === totalCredit ? "success.main" : "error.main"}>
                Debe: {formatAmount(totalDebit)} · Haber: {formatAmount(totalCredit)}
              </Typography>
            </Box>
            <Box>
              <Button type="submit" variant="contained">
                Crear asiento
              </Button>
            </Box>
          </Box>
          <ErrorAlert message={error} sx={{ mt: 2 }} />
        </Paper>

        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Fecha</TableCell>
                <TableCell>Concepto</TableCell>
                <TableCell>Autor</TableCell>
                <TableCell>Líneas</TableCell>
                <TableCell>Estado</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {entries.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell>{entry.id}</TableCell>
                  <TableCell>{entry.date}</TableCell>
                  <TableCell>{entry.description}</TableCell>
                  <TableCell>{entry.author || "Sin autor"}</TableCell>
                  <TableCell>
                    {entry.lines.map((line) => (
                      <div key={line.id}>
                        {line.account_id} · D {formatAmount(line.debit)} / H {formatAmount(line.credit)}
                      </div>
                    ))}
                  </TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={STATUS_LABEL[entry.status] || entry.status}
                      color={entry.status === "accepted" ? "success" : entry.status === "annulled" ? "default" : "warning"}
                    />
                  </TableCell>
                </TableRow>
              ))}
              {entries.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    Sin asientos
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