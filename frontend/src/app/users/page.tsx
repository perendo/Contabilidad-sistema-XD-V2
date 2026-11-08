"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import PaginationBar from "@/components/PaginationBar";
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
  CircularProgress,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";

type User = { id: number; email: string };

const PAGE_SIZE = 50;

export default function UsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  async function load(nextPage = page) {
    setLoadError("");
    try {
      const list = await api(
        `/users?limit=${PAGE_SIZE}&offset=${nextPage * PAGE_SIZE}`
      );
      setUsers(list);
      setHasMore(list.length === PAGE_SIZE);
    } catch (err) {
      setLoadError(errorMessage(err, "No se pudo cargar la lista de usuarios"));
    } finally {
      setLoading(false);
    }
  }

  function goToPage(nextPage: number) {
    setPage(nextPage);
    load(nextPage);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api("/users", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setEmail("");
      setPassword("");
      load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (!isAuthenticated()) return null;

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Usuarios
          </Typography>
          <Button color="inherit" onClick={() => { clearSession(); router.push("/login"); }}>
            Salir
          </Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }}>
        {loading ? (
          <CircularProgress />
        ) : (
          <>
            <ErrorAlert message={loadError} sx={{ mb: 2 }} />
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Nuevo usuario
              </Typography>
              <Box component="form" onSubmit={handleCreate} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required fullWidth />
                <TextField label="Contraseña" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required fullWidth />
                <ErrorAlert message={error} />
                <Button type="submit" variant="contained" disabled={saving}>
                  {saving ? "Guardando..." : "Crear usuario"}
                </Button>
              </Box>
            </Paper>
            <Paper sx={{ p: 3, mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Usuarios
              </Typography>
              <List>
                {users.map((u) => (
                  <ListItem key={u.id}>
                    <ListItemText primary={u.email} />
                  </ListItem>
                ))}
              </List>
            </Paper>
            <PaginationBar
              page={page}
              hasMore={hasMore}
              onPrevious={() => goToPage(page - 1)}
              onNext={() => goToPage(page + 1)}
            />
          </>
        )}
      </Container>
    </>
  );
}
