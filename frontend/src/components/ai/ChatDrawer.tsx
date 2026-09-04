import React, { useEffect, useRef, useState } from 'react';
import {
  X,
  Send,
  Sparkles,
  Bot,
  User,
  ShieldCheck,
  RotateCcw,
  AlertCircle,
} from 'lucide-react';
import { api } from '../../services/api';
import type { ChatStatusResponse } from '../../types/api';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  provider?: string;
  model?: string;
  grounded?: boolean;
  timestamp: string;
}

interface ChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

function renderInlineFormatted(text: string): React.ReactNode[] {
  // Regex matches **bold**, `code`, and *italic* / _italic_
  const parts = text.split(/(\*\*.*?\*\*|`.*?`|\*[^*\n]+?\*|_[^_\n]+?_)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
      return (
        <strong key={i} className="font-semibold text-slate-900 dark:text-slate-100">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
      return (
        <code
          key={i}
          className="px-1.5 py-0.5 mx-0.5 rounded bg-slate-200/60 dark:bg-slate-700 text-slate-800 dark:text-slate-200 font-mono text-xs"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    if (
      (part.startsWith('*') && part.endsWith('*') && part.length >= 2) ||
      (part.startsWith('_') && part.endsWith('_') && part.length >= 2)
    ) {
      return (
        <em key={i} className="italic text-slate-600 dark:text-slate-300">
          {part.slice(1, -1)}
        </em>
      );
    }
    return part;
  });
}

const FormattedMessage: React.FC<{ content: string; isUser: boolean }> = ({
  content,
  isUser,
}) => {
  if (isUser) {
    return <div className="whitespace-pre-wrap">{content}</div>;
  }

  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let currentList: string[] = [];

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="my-2 space-y-1 pl-1">
          {currentList.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2 text-slate-700 text-sm leading-relaxed">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-2 shrink-0" />
              <span className="flex-1">{renderInlineFormatted(item)}</span>
            </li>
          ))}
        </ul>
      );
      currentList = [];
    }
  };

  lines.forEach((rawLine, idx) => {
    const line = rawLine.trimEnd();
    const bulletMatch = line.match(/^(\s*[-*•]|\s*\d+\.)\s+(.*)$/);
    if (bulletMatch) {
      currentList.push(bulletMatch[2]);
    } else {
      flushList();
      if (line.trim() === '') {
        elements.push(<div key={`spacer-${idx}`} className="h-2" />);
      } else {
        elements.push(
          <p key={`p-${idx}`} className="my-1 text-slate-800 leading-relaxed">
            {renderInlineFormatted(line)}
          </p>
        );
      }
    }
  });

  flushList();

  return <div className="space-y-0.5">{elements}</div>;
};

export const ChatDrawer: React.FC<ChatDrawerProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const [chatStatus, setChatStatus] = useState<ChatStatusResponse | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadStatus() {
      try {
        const data = await api.getChatStatus();
        setChatStatus(data);
        if (messages.length === 0 && data.greeting) {
          setMessages([
            {
              id: 'init-greeting',
              sender: 'assistant',
              text: data.greeting,
              provider: data.provider,
              model: data.model,
              grounded: true,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            },
          ]);
        }
      } catch (err) {
        console.warn('Could not load chat status:', err);
      }
    }
    if (isOpen) {
      loadStatus();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (messageText?: string) => {
    const textToSend = (messageText || input).trim();
    if (!textToSend || isLoading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setError(null);
    setLastFailedMessage(null);
    setIsLoading(true);

    try {
      const response = await api.askChat(textToSend);
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: response.answer,
        provider: response.provider,
        model: response.model,
        grounded: response.grounded,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setLastFailedMessage(textToSend);
      setError(err?.message || 'Failed to get answer from Twin engine.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    if (!lastFailedMessage || isLoading) return;
    const retryMsg = lastFailedMessage;
    // Pop the trailing unresponded user message to prevent duplicate bubbles
    setMessages((prev) => {
      if (prev.length > 0 && prev[prev.length - 1].sender === 'user') {
        return prev.slice(0, -1);
      }
      return prev;
    });
    handleSend(retryMsg);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleReset = () => {
    if (chatStatus?.greeting) {
      setMessages([
        {
          id: `reset-${Date.now()}`,
          sender: 'assistant',
          text: chatStatus.greeting,
          provider: chatStatus.provider,
          model: chatStatus.model,
          grounded: true,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } else {
      setMessages([]);
    }
    setError(null);
    setLastFailedMessage(null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-full max-w-md bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col transition-transform duration-300">
      {/* Drawer Header */}
      <div className="p-4 border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between bg-slate-50/70 dark:bg-slate-950/70">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-xs">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Decision Assistant
              <Badge
                variant={
                  chatStatus?.provider === 'gemini'
                    ? 'indigo'
                    : chatStatus?.provider?.includes('fallback')
                    ? 'warning'
                    : 'default'
                }
                size="sm"
              >
                {chatStatus?.provider === 'gemini' ? (chatStatus.model || 'Gemini') : 'Deterministic'}
              </Badge>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
              Grounded in your real twin data
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleReset}
            title="Reset conversation"
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            title="Close panel"
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Suggested Questions (Chips) */}
      {chatStatus?.suggested_questions && chatStatus.suggested_questions.length > 0 && (
        <div className="px-4 py-2.5 bg-slate-50/40 dark:bg-slate-950/40 border-b border-slate-100 dark:border-slate-800 overflow-x-auto">
          <div className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1.5">
            Suggested Prompts
          </div>
          <div className="flex gap-1.5 overflow-x-auto pb-1 no-scrollbar">
            {chatStatus.suggested_questions.slice(0, 4).map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                disabled={isLoading}
                className="text-xs px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:border-indigo-300 dark:hover:border-indigo-500 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors whitespace-nowrap cursor-pointer shrink-0 shadow-2xs"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Message Thread */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex gap-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {m.sender === 'assistant' && (
              <div className="w-7 h-7 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-100 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 flex items-center justify-center shrink-0 mt-0.5">
                <Sparkles className="w-3.5 h-3.5" />
              </div>
            )}

            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                m.sender === 'user'
                  ? 'bg-indigo-600 text-white shadow-xs rounded-br-xs'
                  : 'bg-slate-50 dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700/80 text-slate-800 dark:text-slate-100 shadow-2xs rounded-bl-xs'
              }`}
            >
              <FormattedMessage content={m.text} isUser={m.sender === 'user'} />

              {/* Message metadata footer */}
              <div
                className={`text-[10px] mt-2 pt-1 border-t flex flex-wrap items-center justify-between gap-1.5 ${
                  m.sender === 'user'
                    ? 'border-indigo-500/40 text-indigo-200'
                    : 'border-slate-200/60 dark:border-slate-700/60 text-slate-400 dark:text-slate-400'
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span>{m.timestamp}</span>
                  {m.sender === 'assistant' && m.provider && (
                    <Badge
                      variant={
                        m.provider === 'gemini'
                          ? 'indigo'
                          : m.provider.includes('fallback')
                          ? 'warning'
                          : 'default'
                      }
                      size="sm"
                    >
                      {m.provider === 'gemini'
                        ? 'Gemini'
                        : m.provider === 'rule_based_fallback'
                        ? 'Deterministic Fallback'
                        : 'Deterministic'}
                    </Badge>
                  )}
                </div>

                {m.grounded && (
                  <span className="inline-flex items-center gap-1 font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200/60 dark:border-emerald-800/60 px-1.5 py-0.5 rounded-md text-[10px]">
                    <ShieldCheck className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                    Grounded in Live Twin Data
                  </span>
                )}
              </div>
            </div>

            {m.sender === 'user' && (
              <div className="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center shrink-0 mt-0.5">
                <User className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 justify-start items-center">
            <div className="w-7 h-7 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-100 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 flex items-center justify-center shrink-0">
              <Sparkles className="w-3.5 h-3.5 animate-spin" />
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80 rounded-2xl px-4 py-2.5 text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2 shadow-2xs">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-ping" />
              Twin is reasoning through your metrics...
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-xs text-rose-700 dark:text-rose-300 flex items-start justify-between gap-2 shadow-2xs">
            <div className="flex items-start gap-2 flex-1">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600 dark:text-rose-400" />
              <div className="flex-1">
                <span className="font-semibold">Assistant Error:</span> {error}
              </div>
            </div>
            {lastFailedMessage && (
              <button
                onClick={handleRetry}
                disabled={isLoading}
                className="shrink-0 inline-flex items-center gap-1 font-semibold text-rose-700 dark:text-rose-300 hover:text-rose-900 bg-rose-100/80 dark:bg-rose-900/50 hover:bg-rose-200 px-2.5 py-1 rounded-lg border border-rose-200 dark:border-rose-800 transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3 h-3" />
                Retry
              </button>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your finances, goals or study..."
            disabled={isLoading}
            className="flex-1 px-3.5 py-2.5 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-indigo-500 focus:bg-white dark:focus:bg-slate-850 transition-all text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
          />
          <Button
            variant="primary"
            size="md"
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            isLoading={isLoading}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <div className="mt-1 text-[11px] text-center text-slate-400 dark:text-slate-500">
          Deterministic twin calculations are never modified by conversational AI.
        </div>
      </div>
    </div>
  );
};
