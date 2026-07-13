import type { ReactNode } from "react";
import WorkspaceHeader from "@/components/workspace-header";

export default function ScopeLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <WorkspaceHeader />
      {children}
    </>
  );
}
