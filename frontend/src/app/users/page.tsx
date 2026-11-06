"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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
  CircularProgress,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";

type User = { id: number; email: string };

export default function UsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    (async () => {
      try {
        const list = await api("/users");
        setUsers(list);
      } catch {
        await clearSession();
        router.push("/login");
        return;
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const created = await api("/users", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setUsers((prev) => [...prev, created]);
      setEmail("");
      setPassword("");
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
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Nuevo usuario
              </Typography>
              <Box component="form" onSubmit={handleCreate} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required fullWidth />
                <TextField label="Contraseña" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required fullWidth />
                {error && <Alert severity="error">{error}</Alert>}
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
          </>
        )}
      </Container>
    </>
  );
}
