export type NavIcon =
  | "book"
  | "list"
  | "up"
  | "down"
  | "scale"
  | "trending"
  | "receipt"
  | "shield"
  | "users"
  | "download"
  | "upload";

export type NavItem = {
  label: string;
  href: string;
  icon: NavIcon;
};

export const NAV_ITEMS: NavItem[] = [
  { label: "Plan Contable PGC", href: "/accounts", icon: "book" },
  { label: "Libro Diario", href: "/journal", icon: "list" },
  { label: "Importar Banco", href: "/bank-imports", icon: "upload" },
  { label: "Facturas Emitidas", href: "/invoices", icon: "up" },
  { label: "Facturas Recibidas", href: "/received-invoices", icon: "down" },
  { label: "Balance Sumas y Saldos", href: "/reports/balance", icon: "scale" },
  { label: "Pérdidas y Ganancias", href: "/reports/pyg", icon: "trending" },
  { label: "Liquidación IVA (Mod. 303)", href: "/taxes/iva", icon: "receipt" },
  { label: "Retenciones IRPF (Mod. 111)", href: "/taxes/irpf", icon: "shield" },
  { label: "Modelo 347 Anual", href: "/taxes/347", icon: "users" },
  { label: "Usuarios", href: "/users", icon: "users" },
  { label: "Exportación Oficial", href: "/reports/export", icon: "download" },
];
