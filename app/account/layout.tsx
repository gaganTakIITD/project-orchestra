import type { ReactNode } from "react";
import WorkspaceHeader from "@/components/workspace-header";

export default function AccountLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <WorkspaceHeader />
      {children}
    </>
  );
}
