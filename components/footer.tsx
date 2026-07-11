import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="w-full bg-slate-950 text-slate-400 py-12 md:py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-4 gap-8 mb-12 pb-12 border-b border-slate-800">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">U</span>
              </div>
              <span className="font-bold text-slate-100">UMANO</span>
            </div>
            <p className="text-sm text-slate-500">
              Your dedicated senior product designer, always available.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="font-semibold text-slate-100 mb-4">Product</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="#" className="hover:text-slate-200 transition-colors">
                  Design Studio
                </Link>
              </li>
              <li>
                <Link href="#" className="hover:text-slate-200 transition-colors">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="#" className="hover:text-slate-200 transition-colors">
                  Features
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-semibold text-slate-100 mb-4">Company</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="#" className="hover:text-slate-200 transition-colors">
                  About
                </Link>
              </li>
              <li>
                <Link href="#" className="hover:text-slate-200 transition-colors">
                  Blog
                </Link>
              </li>
              <li>
                <Link href="#" className="hover:text-slate-200 transition-colors">
                  Careers
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-semibold text-slate-100 mb-4">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="#" className="hover:text-slate-200 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="#" className="hover:text-slate-200 transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="#" className="hover:text-slate-200 transition-colors">
                  Contact
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="flex flex-col md:flex-row items-center justify-between">
          <p className="text-sm text-slate-500">
            © 2024 UMANO Design Studio. All rights reserved.
          </p>
          <div className="flex gap-6 mt-4 md:mt-0">
            <a href="#" className="text-slate-500 hover:text-slate-200 transition-colors">
              Twitter
            </a>
            <a href="#" className="text-slate-500 hover:text-slate-200 transition-colors">
              LinkedIn
            </a>
            <a href="#" className="text-slate-500 hover:text-slate-200 transition-colors">
              Instagram
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
