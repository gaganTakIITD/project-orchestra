import dynamic from "next/dynamic";
import Header from "@/components/header";
import Hero from "@/components/hero";
import HowItWorks from "@/components/how-it-works";
import OutcomeCatalog from "@/components/outcome-catalog";
import Footer from "@/components/footer";

// Code-split below-fold components for better initial load performance
const WhyOrchestra = dynamic(() => import("@/components/why-orchestra"), {
  loading: () => <div className="h-screen" />,
});

const AudienceSplit = dynamic(() => import("@/components/audience-split"), {
  loading: () => <div className="h-screen" />,
});

const TrustBand = dynamic(() => import("@/components/trust-band"), {
  loading: () => <div className="h-24" />,
});

const FAQ = dynamic(() => import("@/components/faq"), {
  loading: () => <div className="h-screen" />,
});

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <Header />
      <main id="main-content">
        <Hero aria-label="Hero section - Describe your outcome" />
        <HowItWorks />
        <OutcomeCatalog />
        <WhyOrchestra />
        <AudienceSplit />
        <TrustBand />
        <FAQ />
      </main>
      <Footer />
    </div>
  );
}
