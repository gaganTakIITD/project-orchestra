import { Metadata } from 'next';
import OnboardingContent from './onboarding-content';

export const metadata: Metadata = {
  title: 'Onboarding — Project Orchestra',
  description: 'Complete your profile to start taking projects',
};

export default function OnboardingPage() {
  return <OnboardingContent />;
}
