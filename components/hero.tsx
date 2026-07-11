import { ArrowRight } from 'lucide-react';

export default function Hero() {
  return (
    <section className="relative w-full bg-primary py-20 md:py-32 overflow-hidden">
      {/* Background gradient effect */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-10 w-72 h-72 bg-white rounded-full blur-2xl" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          {/* Left content */}
          <div className="flex flex-col justify-center">
            <h1 className="text-5xl md:text-6xl font-bold text-primary-foreground leading-tight mb-6">
              Pause hiring.
              <br />
              Start designing.
            </h1>
            <p className="text-lg text-primary-foreground/90 mb-8 leading-relaxed">
              We design your <span className="font-semibold">website</span> without limits, for a fixed price.
            </p>
            <p className="text-sm text-primary-foreground/80 mb-8 leading-relaxed max-w-md">
              Finding a product designer takes months. Starting with UMANO takes minutes. Unlimited requests. Fixed monthly price. No commitment.
            </p>
            <button className="w-fit px-8 py-3 bg-primary-foreground text-primary rounded-full font-semibold hover:shadow-lg transition-shadow flex items-center gap-2">
              Get started
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Right - Phone mockup */}
          <div className="flex justify-center md:justify-end">
            <div className="relative w-64 h-96">
              {/* Phone frame */}
              <div className="absolute inset-0 bg-gradient-to-b from-slate-200 to-slate-100 rounded-3xl shadow-2xl overflow-hidden border-8 border-slate-800">
                {/* Notch */}
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-32 h-6 bg-slate-800 rounded-b-2xl z-10" />

                {/* Status bar */}
                <div className="pt-8 px-6 pb-4 text-xs font-semibold text-slate-700 flex justify-between items-center">
                  <span>9:41</span>
                </div>

                {/* Notification content */}
                <div className="px-4 pb-8 space-y-4">
                  <div className="bg-white rounded-2xl p-4 shadow-lg">
                    <div className="flex gap-3">
                      <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
                        <svg className="w-6 h-6 text-primary-foreground" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M10 20a10 10 0 1 1 0-20 10 10 0 0 1 0 20zm0-18a8 8 0 1 0 0 16 8 8 0 0 0 0-16z" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <p className="text-xs font-semibold text-slate-700">Get the job done</p>
                        <p className="text-sm font-bold text-slate-900">Your design has been delivered</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Social proof */}
        <div className="mt-16 pt-16 border-t border-primary-foreground/20">
          <p className="text-primary-foreground/80 text-sm mb-4">
            Our designers have been part of these teams.
          </p>
          <div className="flex flex-wrap gap-6 items-center">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-8 px-4 bg-primary-foreground/20 rounded-full text-primary-foreground text-xs font-medium">
                Company {i}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
