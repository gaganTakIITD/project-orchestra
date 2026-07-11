'use client';

import { useSkus } from '@/lib/hooks';
import { ArrowRight, Calendar } from 'lucide-react';
import Link from 'next/link';

export default function OutcomeCatalog() {
  const { data: skus, isLoading } = useSkus();

  return (
    <section id="outcomes" className="py-20 sm:py-32 bg-card/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">Our outcomes</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Choose from proven outcome packages, or describe your own and we&apos;ll price it.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {isLoading ? (
            // Skeleton loading state
            Array.from({ length: 3 }).map((_, idx) => (
              <div
                key={idx}
                className="bg-background border border-border rounded-lg p-6 animate-pulse"
              >
                <div className="h-6 bg-muted rounded w-2/3 mb-4" />
                <div className="h-4 bg-muted rounded w-full mb-2" />
                <div className="h-4 bg-muted rounded w-5/6 mb-8" />
                <div className="h-10 bg-muted rounded" />
              </div>
            ))
          ) : skus && skus.length > 0 ? (
            skus.map((sku) => (
              <div
                key={sku.id}
                className="group bg-background border border-border rounded-lg p-6 hover:border-primary hover:shadow-lg transition"
              >
                <div className="mb-4">
                  <h3 className="text-lg font-semibold mb-2">{sku.name}</h3>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {sku.description}
                  </p>
                </div>

                <div className="space-y-3 mb-6">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-primary">
                      ₹{sku.base_price.toLocaleString('en-IN')}
                    </span>
                    <span className="text-xs text-muted-foreground">base price</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="w-4 h-4" />
                    <span>~{sku.typical_days} days</span>
                  </div>
                </div>

                <Link
                  href="/start"
                  className="inline-flex items-center gap-2 text-primary font-medium text-sm hover:gap-3 transition"
                >
                  Start outcome
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ))
          ) : (
            <div className="col-span-full text-center py-12">
              <p className="text-muted-foreground">
                No outcomes available. Describe your own at{' '}
                <Link href="/start" className="text-primary font-medium hover:underline">
                  /start
                </Link>
                .
              </p>
            </div>
          )}
        </div>

        <div className="text-center mt-12">
          <p className="text-muted-foreground mb-4">
            Don&apos;t see what you need?
          </p>
          <Link
            href="/start"
            className="inline-flex items-center gap-2 px-8 py-3 border border-primary text-primary rounded-lg font-semibold hover:bg-primary hover:text-primary-foreground transition"
          >
            Describe a custom outcome
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
