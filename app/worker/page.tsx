'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import Header from '@/components/header';
import Footer from '@/components/footer';
import { taskStatusWorkerLabel, taskStatusTone } from '@/lib/state-labels';

const mockTasks = [
  {
    id: 'task_logo',
    title: 'Design Health Tech Logo',
    client: 'HealthTrack',
    status: 'in_progress' as const,
    priority: 'high' as const,
    dueIn: 2,
    estimatedHours: 8,
  },
  {
    id: 'task_web',
    title: 'Frontend Development',
    client: 'FinanceApp',
    status: 'submitted' as const,
    priority: 'medium' as const,
    dueIn: 5,
    estimatedHours: 16,
  },
  {
    id: 'task_docs',
    title: 'API Documentation',
    client: 'DataFlow',
    status: 'ready' as const,
    priority: 'low' as const,
    dueIn: 10,
    estimatedHours: 6,
  },
];

const workerStats = {
  totalEarned: '₹145,000',
  activeProjects: 3,
  completedTasks: 24,
  rating: 4.8,
};

type StatusFilter = 'all' | 'in_progress' | 'submitted' | 'ready' | 'completed';

export default function WorkerDashboard() {
  const [filter, setFilter] = useState<StatusFilter>('all');

  const filteredTasks = useMemo(() => {
    if (filter === 'all') return mockTasks;
    return mockTasks.filter((t) => t.status === filter);
  }, [filter]);

  const getToneColor = (status: string) => {
    const tone = taskStatusTone[status as keyof typeof taskStatusTone];
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

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1 border-b border-border">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-20">
          {/* Header */}
          <div className="mb-12">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-2">
              Rohan's workspace
            </p>
            <h1 className="text-4xl lg:text-5xl font-bold tracking-tight mb-8">
              Welcome back, Rohan
            </h1>

            {/* Stats grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'Total Earned', value: workerStats.totalEarned },
                { label: 'Active Projects', value: workerStats.activeProjects },
                { label: 'Completed Tasks', value: workerStats.completedTasks },
                { label: 'Rating', value: `${workerStats.rating} ⭐` },
              ].map((stat) => (
                <motion.div
                  key={stat.label}
                  className="p-4 border border-border bg-muted/30 hover:border-primary transition-colors"
                  whileHover={{ y: -2 }}
                >
                  <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">
                    {stat.label}
                  </p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Task inbox */}
          <div>
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-2xl font-bold">Task Inbox</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  {filteredTasks.length} {filter === 'all' ? 'tasks' : filter} available
                </p>
              </div>
              <Link
                href="/worker/onboarding"
                className="text-xs font-mono tracking-widest uppercase text-primary hover:underline"
              >
                Update profile
              </Link>
            </div>

            {/* Filters */}
            <div className="flex gap-3 mb-8 overflow-x-auto pb-2">
              {(['all', 'in_progress', 'submitted', 'ready', 'completed'] as StatusFilter[]).map(
                (status) => {
                  const label = status === 'all' ? 'All' : status === 'in_progress' ? 'Active' : status === 'submitted' ? 'In Review' : status === 'ready' ? 'Available' : 'Completed';
                  return (
                    <button
                      key={status}
                      onClick={() => setFilter(status)}
                      className={`whitespace-nowrap h-10 px-4 text-sm font-semibold transition-colors ${
                        filter === status
                          ? 'border-b-2 border-primary text-primary'
                          : 'text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      {label}
                    </button>
                  );
                }
              )}
            </div>

            {/* Task cards */}
            <div className="space-y-3">
              {filteredTasks.length > 0 ? (
                filteredTasks.map((task) => (
                  <motion.div
                    key={task.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <Link
                      href={`/worker/tasks/${task.id}`}
                      className="block p-6 border border-border hover:border-primary hover:bg-muted/50 transition-all group"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold group-hover:text-primary transition-colors">
                            {task.title}
                          </h3>
                          <p className="text-sm text-muted-foreground mt-1">{task.client}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span
                            className={`inline-block px-3 py-1 text-xs font-mono border rounded ${getToneColor(
                              task.status
                            )}`}
                          >
                            {taskStatusWorkerLabel[task.status]}
                          </span>
                          {task.priority === 'high' && (
                            <span className="text-xs font-mono uppercase text-red-600 font-semibold">
                              Priority
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-6 text-sm text-muted-foreground">
                          <span>📋 {task.estimatedHours}h</span>
                          {task.dueIn <= 3 && (
                            <span className="text-amber-600 font-semibold">
                              ⏱ Due in {task.dueIn} days
                            </span>
                          )}
                          {task.dueIn > 3 && (
                            <span>📅 {task.dueIn} days left</span>
                          )}
                        </div>
                        <span className="text-xs font-mono text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                          View task →
                        </span>
                      </div>
                    </Link>
                  </motion.div>
                ))
              ) : (
                <div className="py-12 text-center border border-border border-dashed">
                  <p className="text-sm text-muted-foreground">No tasks in this category</p>
                  <button
                    onClick={() => setFilter('all')}
                    className="text-xs font-mono tracking-widest uppercase text-primary hover:underline mt-4"
                  >
                    View all tasks
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
