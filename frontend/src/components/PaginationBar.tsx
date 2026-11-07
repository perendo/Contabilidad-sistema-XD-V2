"use client";

import { Box, Button, Typography } from "@mui/material";

type Props = {
  page: number;
  hasMore: boolean;
  onPrevious: () => void;
  onNext: () => void;
};

export default function PaginationBar({ page, hasMore, onPrevious, onNext }: Props) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "flex-end",
        gap: 2,
        mt: 2,
      }}
    >
      <Button variant="outlined" disabled={page === 0} onClick={onPrevious}>
        Anterior
      </Button>
      <Typography variant="body2">Página {page + 1}</Typography>
      <Button variant="outlined" disabled={!hasMore} onClick={onNext}>
        Siguiente
      </Button>
    </Box>
  );
}
