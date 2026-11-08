"use client";

import { AppBar, Toolbar, Typography, Button } from "@mui/material";

export function AppHeader({
  title,
  mode,
  toggle,
  onNavigateToPanel,
  onLogout,
  extra,
}: {
  title: string;
  mode: "dark" | "light";
  toggle: () => void;
  onNavigateToPanel: () => void;
  onLogout: () => void;
  extra?: React.ReactNode;
}) {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          {title}
        </Typography>
        {extra}
        <Button color="inherit" onClick={toggle}>
          {mode === "dark" ? "Claro" : "Oscuro"}
        </Button>
        <Button color="inherit" onClick={onNavigateToPanel}>
          Panel
        </Button>
        <Button color="inherit" onClick={onLogout}>
          Salir
        </Button>
      </Toolbar>
    </AppBar>
  );
}
