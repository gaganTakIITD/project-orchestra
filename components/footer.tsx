import Link from "next/link";

const product = [
  { href: "/start", label: "For clients" },
  { href: "/join", label: "For talent" },
  { href: "#how", label: "How it works" },
  { href: "#outcomes", label: "Outcomes" },
];

const company = [
  { href: "#faq", label: "FAQ" },
  { href: "/blog", label: "Blog" },
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
];

const social = [
  { href: "https://x.com", label: "X (Twitter)" },
  { href: "https://github.com", label: "GitHub" },
  { href: "https://linkedin.com", label: "LinkedIn" },
];

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t-4 border-foreground bg-foreground text-background">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">

        <div className="grid grid-cols-2 md:grid-cols-4 gap-12 lg:gap-16 mb-16 pb-16 border-b-2 border-background">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1 flex flex-col gap-6">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-6 h-6 bg-accent border border-background" aria-hidden="true" />
              <span className="text-xs font-mono font-bold tracking-widest uppercase text-background">Orchestra</span>
            </Link>
            <p className="text-sm leading-relaxed max-w-[200px] font-mono">
              Tell us the result. We deliver it.
            </p>
          </div>

          {/* Product */}
          <div className="flex flex-col gap-6">
            <p className="text-xs font-mono tracking-widest uppercase text-background font-bold border-b-2 border-background pb-2">Product</p>
            <ul className="flex flex-col gap-3">
              {product.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-sm text-background hover:text-accent transition-colors font-mono underline">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div className="flex flex-col gap-6">
            <p className="text-xs font-mono tracking-widest uppercase text-background font-bold border-b-2 border-background pb-2">Company</p>
            <ul className="flex flex-col gap-3">
              {company.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-sm text-background hover:text-accent transition-colors font-mono underline">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Social */}
          <div className="flex flex-col gap-6">
            <p className="text-xs font-mono tracking-widest uppercase text-background font-bold border-b-2 border-background pb-2">Follow us</p>
            <ul className="flex flex-col gap-3">
              {social.map((l) => (
                <li key={l.href}>
                  <a
                    href={l.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-background hover:text-accent transition-colors font-mono underline"
                  >
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <p className="text-xs font-mono text-background">
            &copy; {currentYear} Project Orchestra. All rights reserved.
          </p>
          <p className="text-xs font-mono text-background">
            Built by IIT Delhi — for outcome-driven builders.
          </p>
        </div>

      </div>
    </footer>
  );
}
