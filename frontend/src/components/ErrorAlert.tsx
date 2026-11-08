"use client";

import { Alert, type AlertProps } from "@mui/material";

type Props = {
  message: string;
  sx?: AlertProps["sx"];
};

export default function ErrorAlert({ message, sx }: Props) {
  if (!message) return null;
  return (
    <Alert severity="error" sx={sx}>
      {message}
    </Alert>
  );
}
