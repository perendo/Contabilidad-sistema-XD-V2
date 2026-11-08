"use client";

import { Button, CircularProgress, Typography } from "@mui/material";
import ErrorAlert from "./ErrorAlert";

type Props = {
  loading: boolean;
  items: unknown[];
  error?: string | null;
  onRetry: () => void;
};

export function ListState({ loading, items, error, onRetry }: Props) {
  if (loading) {
    return <CircularProgress />;
  }
  if (error) {
    return (
      <div>
        <ErrorAlert message={error} />
        <Button variant="outlined" onClick={onRetry}>
          Reintentar
        </Button>
      </div>
    );
  }
  if (items.length === 0) {
    return <Typography variant="body2" color="text.secondary">Sin datos</Typography>;
  }
  return null;
}
