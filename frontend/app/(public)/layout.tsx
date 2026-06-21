import React from "react";

export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="theme-public min-h-screen flex flex-col font-body transition-colors duration-300">
      {children}
    </div>
  );
}
