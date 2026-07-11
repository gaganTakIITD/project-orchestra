import { Users, Zap, Clock, Workflow, TrendingUp, CheckCircle } from 'lucide-react';

const features = [
  {
    icon: Users,
    title: 'Your designer, from day one',
    description: 'A senior product designer fully dedicated to your company. Working like a founding designer, without the hiring process.',
  },
  {
    icon: Zap,
    title: 'Unlimited design requests',
    description: 'Submit as many tasks as you need. No per-task billing, no cap, no waiting list. Just continuous output.',
  },
  {
    icon: Clock,
    title: 'Delivered in 4 days or less',
    description: 'Every task is delivered within 4 days. Your roadmap keeps moving, your product keeps shipping.',
  },
  {
    icon: Workflow,
    title: 'Embedded in your workflow',
    description: 'Slack, Jira, Notion, Figma, Linear. We plug into whatever you use and work like part of your team.',
  },
  {
    icon: TrendingUp,
    title: 'Flexible and predictable',
    description: 'One flat subscription. No surprises, no contracts. Pause or cancel anytime. Scale design up or down as you grow.',
  },
  {
    icon: CheckCircle,
    title: 'Quality guaranteed',
    description: 'Our senior designers bring expertise from working with some of the world\'s most innovative companies.',
  },
];

export default function Features() {
  return (
    <section className="w-full py-20 md:py-32 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-16">
          <p className="text-muted-foreground text-sm uppercase tracking-wider mb-4">Why choose UMANO</p>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Everything you need to
            <br />
            scale your design
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl">
            We've designed the perfect balance of flexibility, quality, and predictability. Here's what you get when you work with us.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="group p-8 rounded-2xl border border-border hover:border-primary transition-all hover:shadow-lg bg-card hover:bg-slate-50"
              >
                <div className="mb-4 inline-flex p-3 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                  <Icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-bold mb-3 text-foreground">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>

        {/* CTA Section */}
        <div className="mt-20 p-12 rounded-2xl bg-gradient-to-r from-primary to-primary/80 text-primary-foreground">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h3 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to transform your design process?
              </h3>
              <p className="text-lg opacity-90">
                Join leading startups and companies that have already scaled their design with UMANO.
              </p>
            </div>
            <div className="flex justify-end">
              <button className="px-8 py-3 bg-primary-foreground text-primary rounded-full font-semibold hover:shadow-lg transition-shadow text-lg">
                Start your free trial
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
