"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useThemeMode } from "@/components/ThemeProvider";
import { api, errorMessage } from "@/lib/api";
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Alert,
} from "@mui/material";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { mode, toggle } = useThemeMode();

  // Limpieza puntual del token legacy que versiones anteriores guardaban en localStorage.
  useEffect(() => {
    localStorage.removeItem("token");
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      router.push("/");
    } catch (err) {
      setError(errorMessage(err, "Error de autenticación"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "grey.100",
        p: 2,
      }}
    >
      <Card sx={{ width: "100%", maxWidth: 400 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            Iniciar sesión
          </Typography>
          <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
            <Button size="small" onClick={toggle}>
              {mode === "dark" ? "Modo claro" : "Modo oscuro"}
            </Button>
          </Box>
          <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              fullWidth
            />
            <TextField
              label="Contraseña"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              fullWidth
            />
            {error && <Alert severity="error">{error}</Alert>}
            <Button type="submit" variant="contained" disabled={loading} fullWidth>
              {loading ? "Entrando..." : "Entrar"}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
