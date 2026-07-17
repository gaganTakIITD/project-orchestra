import { Metadata } from "next";
import OnboardingContent from "./onboarding-content";

export const metadata: Metadata = {
  title: "Talent profile — Project Orchestra",
  description:
    "Build a matchable worker profile: identity, capabilities, proof of work, and capacity.",
};

export default function OnboardingPage() {
  return <OnboardingContent />;
}
