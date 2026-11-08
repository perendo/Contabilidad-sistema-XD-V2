"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import ErrorAlert from "@/components/ErrorAlert";
import { isAuthenticated, clearSession, api, errorMessage, fetchApi, ApiError } from "@/lib/api";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Paper,
  Box,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";

type Account = {
  id: number;
  code: string;
  name: string;
  is_detail: boolean;
};

type ImportResult = {
  iban: string;
  created: number;
  entry_ids: number[];
};

type MappingDetail = {
  headers: string[];
  message?: string;
};

function isMappingDetail(detail: unknown): detail is MappingDetail {
  if (
    typeof detail !== "object" ||
    detail === null ||
    !("headers" in detail)
  ) {
    return false;
  }
  const headers = (detail as { headers?: unknown }).headers;
  return (
    Array.isArray(headers) &&
    headers.every((header) => typeof header === "string")
  );
}

export default function BankImportsPage() {
  const router = useRouter();
  const { mode, toggle } = useThemeMode();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountId, setAccountId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ImportResult | null>(null);
  const [headers, setHeaders] = useState<string[] | null>(null);
  const [dateCol, setDateCol] = useState("");
  const [conceptCol, setConceptCol] = useState("");
  const [amountCol, setAmountCol] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    api("/accounts?limit=500")
      .then((data: Account[]) => {
        setAccounts(
          data
            .filter((account) => account.is_detail && account.code.startsWith("57"))
            .sort((a, b) => a.code.localeCompare(b.code))
        );
      })
      .catch(() => setError("No se pudieron cargar las cuentas bancarias"))
      .finally(() => setLoadingAccounts(false));
  }, [router]);

  async function logout() {
    await clearSession();
    router.push("/login");
  }

  async function importFile(mapping?: {
    date_column: string;
    concept_column: string;
    amount_column: string;
  }) {
    if (!file) return;
    setError("");
    setResult(null);
    setImporting(true);
    try {
      const body = new FormData();
      body.append("file", file);
      if (accountId) body.append("account_id", accountId);
      if (mapping) {
        body.append("date_column", mapping.date_column);
        body.append("concept_column", mapping.concept_column);
        body.append("amount_column", mapping.amount_column);
      }

      const response = await fetchApi("/bank-imports", {
        method: "POST",
        body,
      });
      setResult(await response.json());
      setFile(null);
      setHeaders(null);
    } catch (e) {
      if (e instanceof ApiError && isMappingDetail(e.detail)) {
        setHeaders(e.detail.headers);
        setDateCol(e.detail.headers[0] ?? "");
        setConceptCol(e.detail.headers[0] ?? "");
        setAmountCol(e.detail.headers[0] ?? "");
        setError(e.detail.message || "Se requiere mapeo de columnas");
      } else {
        // Si ya se envió un mapeo, un fallo de filas no debe borrar la selección.
        if (!mapping) setHeaders(null);
        setError(errorMessage(e, "Error al importar el fichero"));
      }
    } finally {
      setImporting(false);
    }
  }

  async function confirmMapping() {
    if (!dateCol || !conceptCol || !amountCol) {
      setError("Selecciona las tres columnas");
      return;
    }
    await importFile({
      date_column: dateCol,
      concept_column: conceptCol,
      amount_column: amountCol,
    });
  }

  if (!isAuthenticated()) return null;

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Importar movimientos bancarios
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
      <Container sx={{ mt: 4 }} maxWidth="sm">
        <Paper sx={{ p: 3 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Sube un Excel (.xlsx) o un fichero Norma 43 (.csb/.txt) de
            movimientos bancarios. Cada movimiento se creará como asiento en
            borrador, usando la cuenta 555 como contrapartida, para que lo
            revises antes de aceptarlo.
          </Typography>

          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Button variant="outlined" component="label" disabled={importing}>
              {file ? file.name : "Seleccionar fichero (.xlsx, .csb, .txt)"}
              <input
                type="file"
                accept=".xlsx,.csb,.txt"
                hidden
                onChange={(event) => {
                  setResult(null);
                  setError("");
                  setHeaders(null);
                  setFile(event.target.files?.[0] ?? null);
                }}
              />
            </Button>

            <FormControl fullWidth disabled={loadingAccounts || importing}>
              <InputLabel id="bank-account-label">Cuenta bancaria</InputLabel>
              <Select
                labelId="bank-account-label"
                label="Cuenta bancaria"
                value={accountId}
                onChange={(event) => setAccountId(event.target.value)}
              >
                <MenuItem value="">Automática (usar vínculo guardado)</MenuItem>
                {accounts.map((account) => (
                  <MenuItem key={account.id} value={String(account.id)}>
                    {account.code} — {account.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="caption" color="text.secondary">
              Si el IBAN del fichero todavía no está vinculado, selecciona su
              subcuenta del PGC. El vínculo se guardará para próximas
              importaciones.
            </Typography>

            {loadingAccounts && <CircularProgress size={24} />}
            {!loadingAccounts && accounts.length === 0 && (
              <Alert severity="info">
                No hay subcuentas de detalle bajo 57. Crea primero la cuenta del
                banco en el plan contable.
              </Alert>
            )}

            <Button
              variant="contained"
              onClick={() => importFile()}
              disabled={!file || importing}
            >
              {importing ? "Importando..." : "Importar movimientos"}
            </Button>
          </Box>

          {headers && (
            <Box sx={{ mt: 3, display: "flex", flexDirection: "column", gap: 2 }}>
              <Typography variant="subtitle2">
                Selecciona las columnas del fichero:
              </Typography>
              <FormControl fullWidth>
                <InputLabel id="date-col-label">Fecha</InputLabel>
                <Select
                  labelId="date-col-label"
                  label="Fecha"
                  value={dateCol}
                  onChange={(e) => setDateCol(e.target.value)}
                >
                  {headers.map((h) => (
                    <MenuItem key={h} value={h}>
                      {h}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel id="concept-col-label">Concepto</InputLabel>
                <Select
                  labelId="concept-col-label"
                  label="Concepto"
                  value={conceptCol}
                  onChange={(e) => setConceptCol(e.target.value)}
                >
                  {headers.map((h) => (
                    <MenuItem key={h} value={h}>
                      {h}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel id="amount-col-label">Importe</InputLabel>
                <Select
                  labelId="amount-col-label"
                  label="Importe"
                  value={amountCol}
                  onChange={(e) => setAmountCol(e.target.value)}
                >
                  {headers.map((h) => (
                    <MenuItem key={h} value={h}>
                      {h}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="contained"
                onClick={confirmMapping}
                disabled={importing || !dateCol || !conceptCol || !amountCol}
              >
                {importing ? "Importando..." : "Guardar perfil e importar"}
              </Button>
            </Box>
          )}

          <ErrorAlert message={error} sx={{ mt: 3 }} />

          {result && (
            <Alert
              severity="success"
              sx={{ mt: 3 }}
              action={
                <Button color="inherit" size="small" href="/journal">
                  Ver borradores
                </Button>
              }
            >
              {result.created} movimientos importados del IBAN {result.iban}{" "}
              como asientos en borrador.
            </Alert>
          )}
        </Paper>
      </Container>
    </>
  );
}
