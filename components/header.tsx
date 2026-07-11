'use client';

import Link from 'next/link';
import { Menu, X } from 'lucide-react';
import { useState } from 'react';

export default function Header() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-background border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">O</span>
            </div>
            <span className="font-bold text-lg hidden sm:inline">Orchestra</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-8">
            <Link href="#how-it-works" className="text-sm text-foreground hover:text-primary transition">
              How it works
            </Link>
            <Link href="#why-orchestra" className="text-sm text-foreground hover:text-primary transition">
              Why Orchestra
            </Link>
            <Link href="#outcomes" className="text-sm text-foreground hover:text-primary transition">
              Outcomes
            </Link>
            <Link href="#faq" className="text-sm text-foreground hover:text-primary transition">
              FAQ
            </Link>
          </nav>

          {/* CTA Button */}
          <div className="flex items-center gap-4">
            <Link
              href="/start"
              className="hidden sm:inline px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium text-sm hover:opacity-90 transition"
            >
              Describe outcome
            </Link>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="md:hidden p-2 hover:bg-card rounded-lg transition"
            >
              {isOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile Nav */}
        {isOpen && (
          <nav className="md:hidden pb-4 space-y-2">
            <Link
              href="#how-it-works"
              className="block text-sm text-foreground hover:text-primary py-2 transition"
              onClick={() => setIsOpen(false)}
            >
              How it works
            </Link>
            <Link
              href="#why-orchestra"
              className="block text-sm text-foreground hover:text-primary py-2 transition"
              onClick={() => setIsOpen(false)}
            >
              Why Orchestra
            </Link>
            <Link
              href="#outcomes"
              className="block text-sm text-foreground hover:text-primary py-2 transition"
              onClick={() => setIsOpen(false)}
            >
              Outcomes
            </Link>
            <Link
              href="#faq"
              className="block text-sm text-foreground hover:text-primary py-2 transition"
              onClick={() => setIsOpen(false)}
            >
              FAQ
            </Link>
            <Link
              href="/start"
              className="block mt-4 px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium text-sm hover:opacity-90 transition text-center"
              onClick={() => setIsOpen(false)}
            >
              Describe outcome
            </Link>
          </nav>
        )}
      </div>
    </header>
  );
}
