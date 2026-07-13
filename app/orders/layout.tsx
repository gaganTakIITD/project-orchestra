import type { ReactNode } from "react";
import WorkspaceHeader from "@/components/workspace-header";

export default function OrdersLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <WorkspaceHeader />
      {children}
    </>
  );
}
