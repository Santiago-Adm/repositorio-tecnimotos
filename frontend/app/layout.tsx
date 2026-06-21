import type { Metadata } from "next";
import { Quicksand, Nunito_Sans, Fira_Code } from "next/font/google";
import "./globals.css";

const displayFont = Quicksand({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "500", "600", "700"],
});

const bodyFont = Nunito_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["300", "400", "600", "700", "800"],
});

const monoFont = Fira_Code({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Tecnimotos Santi — Sistema de Gestión",
  description: "Sistema de Asistencia y Núcleo Técnico Integral (SANTI) de Tecnimotos Santi",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body
        className={`${displayFont.variable} ${bodyFont.variable} ${monoFont.variable} font-body antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
