import { ArrowRight } from 'lucide-react';

const testimonials = [
  {
    title: 'From complex data to clear financial decisions',
    duration: '3 months',
    tasks: '40 tasks delivered',
    description: 'Structured and designed the product from MVP to commercial launch, supporting the company in raising $4M',
    company: 'FinTech Startup',
  },
  {
    title: 'From multi-layer complexity to a platform ready to scale',
    duration: '8 months',
    tasks: '60 tasks delivered',
    description: 'Complete product redesign and UX overhaul that increased user engagement by 300% and improved retention rates.',
    company: 'SaaS Platform',
  },
  {
    title: 'Building the future of enterprise software',
    duration: '6 months',
    tasks: '50 tasks delivered',
    description: 'End-to-end design system creation and component library that reduced development time by 40%.',
    company: 'Enterprise Tech',
  },
];

export default function Testimonials() {
  return (
    <section className="w-full py-20 md:py-32 bg-slate-950 text-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Stories of
            <br />
            our clients.
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl">
            We&apos;ve already helped 50+ startups deliver products, features, and brands, to grow their business and raise money.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className="group cursor-pointer p-8 rounded-2xl bg-slate-900 border border-slate-800 hover:border-primary/50 hover:bg-slate-800 transition-all"
            >
              {/* Gradient background */}
              <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="relative">
                {/* Video placeholder */}
                <div className="w-full aspect-video bg-slate-800 rounded-lg mb-6 flex items-center justify-center border border-slate-700 group-hover:border-primary/30 transition-colors">
                  <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                    <svg className="w-6 h-6 text-primary" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                    </svg>
                  </div>
                </div>

                {/* Content */}
                <h3 className="text-lg font-bold mb-3 text-slate-100 group-hover:text-primary transition-colors">
                  {testimonial.title}
                </h3>

                <p className="text-slate-400 text-sm mb-6">
                  {testimonial.description}
                </p>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4 mb-6 py-4 border-y border-slate-800">
                  <div>
                    <p className="text-2xl font-bold text-primary">{testimonial.duration}</p>
                    <p className="text-xs text-slate-400 uppercase tracking-wider">Duration</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-primary">{testimonial.tasks}</p>
                    <p className="text-xs text-slate-400 uppercase tracking-wider">Delivered</p>
                  </div>
                </div>

                {/* Company */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">{testimonial.company}</span>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-primary transition-colors" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
