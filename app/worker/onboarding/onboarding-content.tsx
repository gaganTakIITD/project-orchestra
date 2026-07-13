'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Footer from '@/components/footer';
import { useRouter } from 'next/navigation';

type Step = 'basics' | 'skills' | 'portfolio' | 'payout';

const steps: { id: Step; title: string; label: string }[] = [
  { id: 'basics', title: 'Basics', label: 'Who you are' },
  { id: 'skills', title: 'Skills & Tools', label: 'What you can do' },
  { id: 'portfolio', title: 'Portfolio', label: 'Show your work' },
  { id: 'payout', title: 'Payout', label: 'Get paid' },
];

interface ProfileData {
  fullName: string;
  bio: string;
  location: string;
  skills: string[];
  tools: string[];
  portfolioUrl: string;
  portfolioDescription: string;
  bankAccount: string;
  upiId: string;
}

export default function OnboardingContent() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<Step>('basics');
  const [profile, setProfile] = useState<ProfileData>({
    fullName: 'Rohan Sharma',
    bio: 'Full-stack developer passionate about building products',
    location: 'Bangalore, India',
    skills: ['React', 'Node.js', 'TypeScript'],
    tools: ['Figma', 'Git', 'Docker'],
    portfolioUrl: 'https://rohan.dev',
    portfolioDescription: 'Personal portfolio showcasing recent work',
    bankAccount: '••••••••3456',
    upiId: 'rohan@upi',
  });

  const completion = {
    basics: profile.fullName && profile.bio ? 100 : 50,
    skills: profile.skills.length >= 3 && profile.tools.length >= 2 ? 100 : profile.skills.length * 30,
    portfolio: profile.portfolioUrl ? 100 : 0,
    payout: profile.bankAccount || profile.upiId ? 100 : 0,
  };

  const totalCompletion = Math.round(
    (completion.basics + completion.skills + completion.portfolio + completion.payout) / 4
  );

  const canProceed = totalCompletion >= 70;

  const updateProfile = (field: keyof ProfileData, value: any) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
  };

  const handleNext = () => {
    const stepIndex = steps.findIndex((s) => s.id === currentStep);
    if (stepIndex < steps.length - 1) {
      setCurrentStep(steps[stepIndex + 1].id);
    }
  };

  const handlePrev = () => {
    const stepIndex = steps.findIndex((s) => s.id === currentStep);
    if (stepIndex > 0) {
      setCurrentStep(steps[stepIndex - 1].id);
    }
  };

  const handleComplete = () => {
    if (canProceed) {
      router.push('/worker');
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main id="main-content" className="flex-1 border-b border-border">
        <div className="max-w-4xl mx-auto px-6 lg:px-8 py-20">
          {/* Progress header */}
          <div className="mb-12">
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-xs font-mono tracking-widest uppercase text-primary mb-2">
                  Onboarding
                </p>
                <h1 className="text-3xl font-bold tracking-tight">
                  Complete your profile
                </h1>
                <p className="text-sm text-muted-foreground mt-2">
                  {totalCompletion}% complete • {canProceed ? 'Ready to work' : 'Complete 70% to continue'}
                </p>
              </div>
            </div>

            {/* Progress bar */}
            <div className="h-2 bg-border rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary"
                initial={{ width: 0 }}
                animate={{ width: `${totalCompletion}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>

          {/* Steps navigation */}
          <div className="grid grid-cols-4 gap-2 lg:gap-4 mb-12">
            {steps.map((step, idx) => (
              <motion.button
                key={step.id}
                onClick={() => setCurrentStep(step.id)}
                className={`p-4 border rounded-lg transition-all ${
                  currentStep === step.id
                    ? 'border-primary bg-primary/5'
                    : completion[step.id] === 100
                    ? 'border-secondary bg-secondary/5'
                    : 'border-border'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="flex flex-col items-start">
                  <p className="text-xs font-mono text-muted-foreground mb-1">
                    {String(idx + 1).padStart(2, '0')}
                  </p>
                  <p className="text-sm font-semibold text-left">{step.title}</p>
                  <p className="text-xs text-muted-foreground text-left mt-1">
                    {completion[step.id]}%
                  </p>
                </div>
              </motion.button>
            ))}
          </div>

          {/* Step content */}
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-12"
          >
            {currentStep === 'basics' && (
              <div className="space-y-6">
                <div>
                  <label className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2 block">
                    Full name
                  </label>
                  <input
                    type="text"
                    value={profile.fullName}
                    onChange={(e) => updateProfile('fullName', e.target.value)}
                    className="w-full h-11 border border-border bg-background px-4 text-sm focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                <div>
                  <label className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2 block">
                    Bio
                  </label>
                  <textarea
                    value={profile.bio}
                    onChange={(e) => updateProfile('bio', e.target.value)}
                    rows={4}
                    className="w-full border border-border bg-background px-4 py-3 text-sm focus:outline-none focus:border-primary transition-colors resize-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2 block">
                    Location
                  </label>
                  <input
                    type="text"
                    value={profile.location}
                    onChange={(e) => updateProfile('location', e.target.value)}
                    className="w-full h-11 border border-border bg-background px-4 text-sm focus:outline-none focus:border-primary transition-colors"
                  />
                </div>
              </div>
            )}

            {currentStep === 'skills' && (
              <div className="space-y-6">
                <div>
                  <label className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-3 block">
                    Skills (at least 3)
                  </label>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {profile.skills.map((skill, idx) => (
                      <div
                        key={idx}
                        className="inline-flex items-center gap-2 px-3 py-2 bg-primary/10 border border-primary text-sm font-mono"
                      >
                        {skill}
                        <button
                          onClick={() =>
                            updateProfile(
                              'skills',
                              profile.skills.filter((_, i) => i !== idx)
                            )
                          }
                          className="text-primary hover:text-primary/80"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                  <input
                    type="text"
                    placeholder="Add skill and press Enter"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.currentTarget.value) {
                        updateProfile('skills', [...profile.skills, e.currentTarget.value]);
                        e.currentTarget.value = '';
                      }
                    }}
                    className="w-full h-11 border border-border bg-background px-4 text-sm focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                <div>
                  <label className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-3 block">
                    Tools & Software (at least 2)
                  </label>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {profile.tools.map((tool, idx) => (
                      <div
                        key={idx}
                        className="inline-flex items-center gap-2 px-3 py-2 bg-secondary/10 border border-secondary text-sm font-mono"
                      >
                        {tool}
                        <button
                          onClick={() =>
                            updateProfile(
                              'tools',
                              profile.tools.filter((_, i) => i !== idx)
                            )
                          }
                          className="text-secondary hover:text-secondary/80"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                  <input
                    type="text"
                    placeholder="Add tool and press Enter"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.currentTarget.value) {
                        updateProfile('tools', [...profile.tools, e.currentTarget.value]);
                        e.currentTarget.value = '';
                      }
                    }}
                    className="w-full h-11 border border-border bg-background px-4 text-sm focus:outline-none focus:border-primary transition-colors"
                  />
                </div>
              </div>
            )}

            {currentStep === 'portfolio' && (
              <div className="space-y-6">
                <div>
                  <label className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2 block">
                    Portfolio URL
                  </label>
                  <input
                    type="url"
                    value={profile.portfolioUrl}
                    onChange={(e) => updateProfile('portfolioUrl', e.target.value)}
                    className="w-full h-11 border border-border bg-background px-4 text-sm focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                <div>
                  <label className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2 block">
                    Portfolio description
                  </label>
                  <textarea
                    value={profile.portfolioDescription}
                    onChange={(e) => updateProfile('portfolioDescription', e.target.value)}
                    rows={4}
                    className="w-full border border-border bg-background px-4 py-3 text-sm focus:outline-none focus:border-primary transition-colors resize-none"
                  />
                </div>
              </div>
            )}

            {currentStep === 'payout' && (
              <div className="space-y-6">
                <div>
                  <label className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2 block">
                    Bank account
                  </label>
                  <input
                    type="text"
                    value={profile.bankAccount}
                    onChange={(e) => updateProfile('bankAccount', e.target.value)}
                    placeholder="••••••••XXXX"
                    className="w-full h-11 border border-border bg-background px-4 text-sm focus:outline-none focus:border-primary transition-colors"
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    Your account info is encrypted and secure
                  </p>
                </div>

                <div>
                  <label className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2 block">
                    UPI ID (optional)
                  </label>
                  <input
                    type="text"
                    value={profile.upiId}
                    onChange={(e) => updateProfile('upiId', e.target.value)}
                    placeholder="yourname@upi"
                    className="w-full h-11 border border-border bg-background px-4 text-sm focus:outline-none focus:border-primary transition-colors"
                  />
                </div>
              </div>
            )}
          </motion.div>

          {/* Action buttons */}
          <div className="flex items-center justify-between">
            <button
              onClick={handlePrev}
              disabled={currentStep === 'basics'}
              className="h-11 px-6 border border-border text-sm font-semibold hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>

            {currentStep === 'payout' ? (
              <button
                onClick={handleComplete}
                disabled={!canProceed}
                className="h-11 px-8 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
              >
                {canProceed ? 'Start working' : 'Complete profile'}
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="h-11 px-6 bg-secondary text-secondary-foreground text-sm font-semibold hover:opacity-90 transition-opacity"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
