'use client';

import { useState, useRef, useEffect } from 'react';
import { useDiscussion } from '@/lib/hooks';
import type { DiscussionThread, DiscussionMessage } from '@/lib/types';

interface DiscussionPanelProps {
  taskId: string;
}

export default function DiscussionPanel({ taskId }: DiscussionPanelProps) {
  const { data: thread, isLoading } = useDiscussion(taskId);
  const [newMessage, setNewMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const messages = thread?.messages || [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || isSending) return;

    setIsSending(true);
    try {
      // Mock send - in real implementation, call usePostDiscussion mutation
      setNewMessage('');
    } finally {
      setIsSending(false);
    }
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-12 bg-muted rounded animate-pulse" />
        <div className="h-64 bg-muted rounded animate-pulse" />
      </div>
    );
  }

  // Empty state
  if (!thread || messages.length === 0) {
    return (
      <div className="border border-border p-6 rounded-sm bg-muted/30 text-center">
        <p className="text-sm text-muted-foreground">No messages yet</p>
        <p className="text-xs text-muted-foreground mt-2">Start a conversation with your team</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-96 border border-border rounded-sm bg-background">
      {/* Messages list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg: DiscussionMessage) => (
          <div key={msg.id} className="flex gap-3">
            {/* Avatar */}
            <div className="flex-shrink-0">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-mono font-bold text-primary">
                {msg.sender_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
              </div>
            </div>

            {/* Message content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2 mb-1">
                <p className="text-sm font-semibold">{msg.sender_name}</p>
                <p className="text-xs text-muted-foreground">
                  {new Date(msg.created_at).toLocaleDateString('en-IN', { 
                    month: 'short', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
              <p className="text-sm text-foreground leading-relaxed break-words">{msg.body}</p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Divider */}
      <div className="border-t border-border" />

      {/* Message composer */}
      <form onSubmit={handleSendMessage} className="p-4 flex gap-3">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type a message..."
          disabled={isSending}
          className="flex-1 h-10 border border-border bg-background px-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!newMessage.trim() || isSending}
          className="h-10 px-4 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSending ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
