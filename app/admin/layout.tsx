import type { ReactNode } from "react";
import WorkspaceHeader from "@/components/workspace-header";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <WorkspaceHeader />
      {children}
    </>
  );
}
