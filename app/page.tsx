'use client';

import { useState } from 'react';
import Header from '@/components/header';
import Hero from '@/components/hero';
import Features from '@/components/features';
import Testimonials from '@/components/testimonials';
import FAQ from '@/components/faq';
import Footer from '@/components/footer';

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <Header />
      <main>
        <Hero />
        <Features />
        <Testimonials />
        <FAQ />
      </main>
      <Footer />
    </div>
  );
}
