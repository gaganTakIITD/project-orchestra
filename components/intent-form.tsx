"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCreateIntent } from "@/lib/hooks";

export default function IntentForm() {
  const router = useRouter();
  const createIntent = useCreateIntent();
  
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    outcome: "",
    budget: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!formData.name.trim() || !formData.email.trim() || !formData.outcome.trim()) {
      alert("Please fill in all required fields");
      return;
    }

    try {
      const result = await createIntent.mutateAsync(formData.outcome);
      // Save intent ID and email to session for proposal page
      sessionStorage.setItem("intent_id", result.intent_id);
      sessionStorage.setItem("client_email", formData.email);
      sessionStorage.setItem("client_name", formData.name);
      
      // Navigate to proposal page with quote ID
      router.push(`/proposal/${result.quote_id}`);
    } catch (error) {
      alert("Failed to create intent. Please try again.");
      console.error("[v0] Intent creation failed:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <label htmlFor="name" className="text-xs font-mono tracking-widest uppercase text-muted-foreground">
          Your name
        </label>
        <input
          id="name"
          name="name"
          type="text"
          placeholder="Arjun Sharma"
          value={formData.name}
          onChange={handleChange}
          required
          className="h-11 border border-border bg-background px-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
        />
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="email" className="text-xs font-mono tracking-widest uppercase text-muted-foreground">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          placeholder="you@company.com"
          value={formData.email}
          onChange={handleChange}
          required
          className="h-11 border border-border bg-background px-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
        />
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="outcome" className="text-xs font-mono tracking-widest uppercase text-muted-foreground">
          Describe your outcome
        </label>
        <textarea
          id="outcome"
          name="outcome"
          rows={6}
          placeholder="e.g. I need a brand identity for my fintech startup — logo, color palette, and a mini brand guide. Launching in 3 weeks."
          value={formData.outcome}
          onChange={handleChange}
          required
          className="border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors resize-none leading-relaxed"
        />
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="budget" className="text-xs font-mono tracking-widest uppercase text-muted-foreground">
          Rough budget (optional)
        </label>
        <input
          id="budget"
          name="budget"
          type="text"
          placeholder="e.g. ₹15,000–₹25,000"
          value={formData.budget}
          onChange={handleChange}
          className="h-11 border border-border bg-background px-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
        />
      </div>

      <button
        type="submit"
        disabled={createIntent.isPending}
        className="inline-flex items-center justify-center h-11 px-8 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity self-start"
      >
        {createIntent.isPending ? "Submitting..." : "Submit outcome brief"}
      </button>

      <p className="text-xs text-muted-foreground">
        We&apos;ll send you a scoped plan within 24 hours. No commitment until you approve.
      </p>
    </form>
  );
}
