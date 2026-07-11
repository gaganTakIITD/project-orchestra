'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import Header from '@/components/header';
import Footer from '@/components/footer';
import { taskStatusWorkerLabel, taskStatusTone } from '@/lib/state-labels';

interface TaskPageParams {
  params: {
    taskId: string;
  };
}

const mockCharter = {
  id: 'charter_logo',
  taskId: 'task_logo',
  outcomeTitle: 'HealthTrack Brand Identity',
  description:
    'Design a comprehensive brand identity including logo, color palette, typography guidelines, and usage rules for a health-tech startup.',
  scope: {
    included: ['Logo design', 'Color palette', 'Typography guide', 'Brand guidelines'],
    excluded: ['Social media templates', 'Ad creative', 'Website design'],
  },
  deliverables: ['Logo files (SVG, PNG, AI)', 'Brand book (PDF)', 'Figma design system'],
  timeline: '7 days',
  budget: '₹25,000',
};

const mockTaskPacket = {
  id: 'packet_logo',
  taskId: 'task_logo',
  title: 'Logo Design Checklist',
  checklist: [
    { id: 'initial_sketches', label: 'Initial sketches (3 concepts)', completed: true },
    { id: 'concept_review', label: 'Client feedback on concepts', completed: true },
    { id: 'refinement', label: 'Refine selected concept', completed: false },
    { id: 'variations', label: 'Create color & monochrome versions', completed: false },
    { id: 'final_export', label: 'Export to all formats', completed: false },
    { id: 'delivery', label: 'Deliver final files', completed: false },
  ],
};

const mockDiscussion = [
  {
    id: '1',
    author: 'Priya Sharma',
    role: 'Client',
    avatar: 'PS',
    timestamp: '2 hours ago',
    message: 'The initial sketches look great! I especially like concepts 1 and 3. Can we explore combining elements from both?',
  },
  {
    id: '2',
    author: 'Rohan Sharma',
    role: 'Worker',
    avatar: 'RS',
    timestamp: '1 hour ago',
    message: "Absolutely! I'll create a hybrid concept mixing the best of both. Should have it ready by tomorrow.",
  },
];

export default function WorkerTaskDetail({ params }: TaskPageParams) {
  const { taskId } = params;
  const [status, setStatus] = useState<'ready' | 'in_progress' | 'submitted' | 'completed'>('in_progress');
  const [discussion, setDiscussion] = useState(mockDiscussion);
  const [newMessage, setNewMessage] = useState('');

  const getToneColor = (taskStatus: string) => {
    const tone = taskStatusTone[taskStatus as keyof typeof taskStatusTone];
    const colors: Record<string, string> = {
      neutral: 'bg-gray-100 text-gray-800 border-gray-200',
      info: 'bg-blue-100 text-blue-800 border-blue-200',
      active: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      review: 'bg-amber-100 text-amber-800 border-amber-200',
      success: 'bg-green-100 text-green-800 border-green-200',
      danger: 'bg-red-100 text-red-800 border-red-200',
    };
    return colors[tone] || colors.neutral;
  };

  const handleSendMessage = () => {
    if (!newMessage.trim()) return;

    setDiscussion([
      ...discussion,
      {
        id: String(discussion.length + 1),
        author: 'Rohan Sharma',
        role: 'Worker',
        avatar: 'RS',
        timestamp: 'Just now',
        message: newMessage,
      },
    ]);
    setNewMessage('');
  };

  const completedItems = mockTaskPacket.checklist.filter((c) => c.completed).length;
  const totalItems = mockTaskPacket.checklist.length;
  const progress = Math.round((completedItems / totalItems) * 100);

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1 border-b border-border">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-20">
          {/* Header */}
          <div className="mb-12">
            <div className="flex items-start justify-between mb-6">
              <div>
                <Link
                  href="/worker"
                  className="text-xs font-mono tracking-widest uppercase text-primary hover:underline mb-4 inline-block"
                >
                  ← Back to inbox
                </Link>
                <h1 className="text-4xl font-bold tracking-tight mb-2">
                  {mockCharter.outcomeTitle}
                </h1>
                <p className="text-sm text-muted-foreground">{taskId}</p>
              </div>
              <span
                className={`inline-block px-4 py-2 text-sm font-mono border rounded ${getToneColor(
                  status
                )}`}
              >
                {taskStatusWorkerLabel[status]}
              </span>
            </div>
          </div>

          {/* Three-column layout */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* LEFT: Charter (frozen) */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="lg:col-span-1"
            >
              <div className="border border-border bg-muted/30 p-6 sticky top-24">
                <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-4">
                  Charter (read-only)
                </p>

                <div className="space-y-6">
                  {/* Description */}
                  <div>
                    <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">
                      Scope
                    </p>
                    <p className="text-sm leading-relaxed">{mockCharter.description}</p>
                  </div>

                  {/* Included */}
                  <div>
                    <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">
                      Included
                    </p>
                    <ul className="space-y-1">
                      {mockCharter.scope.included.map((item) => (
                        <li key={item} className="text-sm text-muted-foreground flex items-start gap-2">
                          <span className="text-primary mt-1">✓</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Excluded */}
                  <div>
                    <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">
                      Excluded
                    </p>
                    <ul className="space-y-1">
                      {mockCharter.scope.excluded.map((item) => (
                        <li key={item} className="text-sm text-muted-foreground flex items-start gap-2">
                          <span>✗</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Meta */}
                  <div className="border-t border-border pt-6 space-y-4">
                    <div>
                      <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-1">
                        Timeline
                      </p>
                      <p className="text-sm font-semibold">{mockCharter.timeline}</p>
                    </div>
                    <div>
                      <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-1">
                        Budget
                      </p>
                      <p className="text-sm font-semibold">{mockCharter.budget}</p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* MIDDLE: Task Packet (checklist) */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="lg:col-span-1"
            >
              <div className="border border-border p-6 space-y-6">
                <div>
                  <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-4">
                    Task Packet
                  </p>
                  <h2 className="text-lg font-bold mb-4">{mockTaskPacket.title}</h2>

                  {/* Progress bar */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs text-muted-foreground">
                        {completedItems} of {totalItems} complete
                      </p>
                      <p className="text-sm font-semibold">{progress}%</p>
                    </div>
                    <div className="h-2 bg-border rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-primary"
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.5 }}
                      />
                    </div>
                  </div>

                  {/* Checklist */}
                  <div className="space-y-3">
                    {mockTaskPacket.checklist.map((item) => (
                      <motion.label
                        key={item.id}
                        className="flex items-center gap-3 p-3 border border-border hover:bg-muted/50 cursor-pointer transition-colors"
                        whileHover={{ scale: 1.02 }}
                      >
                        <input
                          type="checkbox"
                          checked={item.completed}
                          onChange={() => {}}
                          className="w-4 h-4 rounded border-border cursor-pointer"
                        />
                        <span
                          className={`text-sm flex-1 ${
                            item.completed ? 'line-through text-muted-foreground' : ''
                          }`}
                        >
                          {item.label}
                        </span>
                      </motion.label>
                    ))}
                  </div>
                </div>

                {/* Action buttons */}
                <div className="border-t border-border pt-6 space-y-3">
                  {status === 'in_progress' && (
                    <>
                      <button className="w-full h-11 bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity">
                        Submit for review
                      </button>
                      <button className="w-full h-11 border border-border font-semibold hover:bg-muted transition-colors">
                        Request extension
                      </button>
                    </>
                  )}
                  {status === 'submitted' && (
                    <button className="w-full h-11 bg-green-600 text-white font-semibold hover:bg-green-700 transition-colors">
                      Mark as complete
                    </button>
                  )}
                </div>
              </div>
            </motion.div>

            {/* RIGHT: Discussion */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="lg:col-span-1"
            >
              <div className="border border-border p-6 flex flex-col h-full">
                <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-4">
                  Discussion
                </p>

                {/* Messages */}
                <div className="flex-1 space-y-4 mb-6 overflow-y-auto max-h-96">
                  {discussion.map((msg) => (
                    <div key={msg.id} className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-mono font-bold">
                          {msg.avatar}
                        </div>
                        <div>
                          <p className="text-xs font-semibold">{msg.author}</p>
                          <p className="text-xs text-muted-foreground">{msg.timestamp}</p>
                        </div>
                      </div>
                      <p className="text-sm bg-muted/50 p-3 rounded border border-border">
                        {msg.message}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Message input */}
                <div className="border-t border-border pt-4 space-y-3">
                  <textarea
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.ctrlKey) {
                        handleSendMessage();
                      }
                    }}
                    placeholder="Type a message... (Ctrl+Enter to send)"
                    className="w-full h-20 border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:border-primary transition-colors resize-none"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!newMessage.trim()}
                    className="w-full h-10 bg-secondary text-secondary-foreground text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
                  >
                    Send message
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
