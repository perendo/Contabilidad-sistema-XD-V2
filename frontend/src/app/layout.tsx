import type { Metadata } from "next";
import AppThemeProvider from "@/components/ThemeProvider";

export const metadata: Metadata = {
  title: "Contabilidad",
  description: "Sistema de contabilidad",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>
        <AppThemeProvider>{children}</AppThemeProvider>
      </body>
    </html>
  );
}
