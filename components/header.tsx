import Link from 'next/link';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 w-full bg-background border-b border-border">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">U</span>
          </div>
          <span className="font-bold text-lg">UMANO</span>
        </div>

        <div className="hidden md:flex items-center gap-8">
          <Link href="#design-studio" className="text-sm hover:text-primary transition-colors">
            Design Studio
          </Link>
          <Link href="#academy" className="text-sm hover:text-primary transition-colors">
            Design Academy
          </Link>
        </div>

        <Link
          href="#start"
          className="px-6 py-2 bg-primary text-primary-foreground rounded-full text-sm font-medium hover:opacity-90 transition-opacity"
        >
          Start today
        </Link>
      </nav>
    </header>
  );
}
