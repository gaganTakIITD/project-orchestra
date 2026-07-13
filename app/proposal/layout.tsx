import type { ReactNode } from "react";
import WorkspaceHeader from "@/components/workspace-header";

export default function ProposalLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <WorkspaceHeader />
      {children}
    </>
  );
}
