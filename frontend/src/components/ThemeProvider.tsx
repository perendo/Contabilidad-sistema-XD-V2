"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";

type Mode = "dark" | "light";

interface ThemeContextValue {
  mode: Mode;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({ mode: "dark", toggle: () => {} });
export const useThemeMode = () => useContext(ThemeContext);

const darkPalette = {
  mode: "dark" as const,
  primary: { main: "#82AFF5" },
  secondary: { main: "#7ED9A8" },
  error: { main: "#E57373" },
  success: { main: "#7ED9A8" },
  background: { default: "#121212", paper: "#1E1E1E" },
  text: { primary: "#E1E1E1", secondary: "#A0A0A0" },
  divider: "#2E2E3E",
};

const lightPalette = {
  mode: "light" as const,
  primary: { main: "#3B82F6" },
  secondary: { main: "#10B981" },
  error: { main: "#EF4444" },
  success: { main: "#10B981" },
  background: { default: "#F5F5F0", paper: "#FFFFFF" },
  text: { primary: "#1F2937", secondary: "#6B7280" },
  divider: "#E2E8F0",
};

export default function AppThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<Mode>("dark");

  useEffect(() => {
    const stored = localStorage.getItem("theme-mode");
    // Se aplica después del montaje para que el HTML generado en el servidor
    // (tema oscuro por defecto) coincida con el primer render del cliente y no
    // se produzca un desajuste de hidratación. Es una sincronización puntual
    // con un almacén externo, no un estado derivado durante el render.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (stored === "light" || stored === "dark") setMode(stored);
  }, []);

  useEffect(() => {
    localStorage.setItem("theme-mode", mode);
    document.documentElement.setAttribute("data-theme", mode === "light" ? "light" : "dark");
  }, [mode]);

  const theme = createTheme({
    palette: mode === "dark" ? darkPalette : lightPalette,
    typography: { fontFamily: "Roboto, Arial, sans-serif" },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: "none",
          },
        },
      },
    },
  });

  return (
    <ThemeContext.Provider value={{ mode, toggle: () => setMode((m) => (m === "dark" ? "light" : "dark")) }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ThemeContext.Provider>
  );
}
