import React from "react";

export default function InternalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="theme-internal min-h-screen flex flex-col font-body transition-colors duration-300">
      {children}
    </div>
  );
}
