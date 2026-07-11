'use client';

import Header from '@/components/header';
import Hero from '@/components/hero';
import HowItWorks from '@/components/how-it-works';
import WhyOrchestra from '@/components/why-orchestra';
import OutcomeCatalog from '@/components/outcome-catalog';
import AudienceSplit from '@/components/audience-split';
import TrustBand from '@/components/trust-band';
import FAQ from '@/components/faq';
import Footer from '@/components/footer';

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <Header />
      <main>
        <Hero />
        <HowItWorks />
        <WhyOrchestra />
        <OutcomeCatalog />
        <AudienceSplit />
        <TrustBand />
        <FAQ />
      </main>
      <Footer />
    </div>
  );
}
