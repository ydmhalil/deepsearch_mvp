import { useState, useRef, useEffect } from 'react';
import { Send, Loader, FileText, MessageSquare, Bot, User } from 'lucide-react';
import { api } from '../utils/api';
import type { ChatMessage } from '../types';

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.ragQuery(input, sessionId, 'conversational');

      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_ai`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
        follow_up_questions: response.follow_up_questions,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: `msg_${Date.now()}_error`,
        role: 'assistant',
        content: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuestion = (question: string) => {
    setInput(question);
  };

  const quickQuestions = [
    'Güvenlik prosedürleri hakkında bilgi ver',
    'Radar sistemleri nasıl çalışır?',
    'Roket teknolojisi nedir?',
    'Savunma sistemleri hakkında özet',
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 h-[calc(100vh-8rem)]">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">RAG Chat</h1>
        <p className="text-gray-600">Belgelerinizle doğal dilde konuşun</p>
      </div>

      <div className="card h-[calc(100%-8rem)] flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <MessageSquare className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Konuşmaya başlayın
              </h3>
              <p className="text-gray-600 mb-6">
                Belgeleriniz hakkında soru sorun, AI size yardımcı olacak
              </p>

              <div className="max-w-2xl mx-auto">
                <p className="text-sm text-gray-500 mb-3">Hızlı sorular:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {quickQuestions.map((question) => (
                    <button
                      key={question}
                      onClick={() => handleQuickQuestion(question)}
                      className="text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm text-gray-700 transition-colors"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-[var(--primary-color)] flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
              )}

              <div
                className={`max-w-3xl ${
                  message.role === 'user'
                    ? 'bg-[var(--primary-color)] text-white'
                    : 'bg-gray-100 text-gray-900'
                } rounded-2xl px-6 py-4`}
              >
                <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>

                {message.sources && message.sources.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-300">
                    <p className="text-sm font-semibold mb-2">Kaynaklar:</p>
                    <div className="space-y-2">
                      {message.sources.map((source, idx) => (
                        <div
                          key={idx}
                          className="bg-white rounded-lg p-3 text-sm border border-gray-200"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <FileText className="w-4 h-4 text-gray-600" />
                            <span className="font-medium text-gray-900">
                              {source.file_path.split('/').pop()}
                            </span>
                            <span className="text-xs text-gray-500">
                              ({Math.round(source.score * 100)}% eşleşme)
                            </span>
                          </div>
                          <p className="text-gray-600 line-clamp-2">{source.chunk_text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {message.follow_up_questions && message.follow_up_questions.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-300">
                    <p className="text-sm font-semibold mb-2">Takip soruları:</p>
                    <div className="space-y-2">
                      {message.follow_up_questions.map((question, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleQuickQuestion(question)}
                          className="block w-full text-left p-2 bg-white hover:bg-gray-50 rounded-lg text-sm text-gray-700 transition-colors border border-gray-200"
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-gray-700" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-[var(--primary-color)] flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-gray-100 text-gray-900 rounded-2xl px-6 py-4">
                <div className="flex items-center gap-2">
                  <Loader className="w-5 h-5 animate-spin text-[var(--primary-color)]" />
                  <span>Yanıt oluşturuluyor...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Sorunuzu yazın..."
              className="input-field"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
              <span className="hidden sm:inline">Gönder</span>
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            AI belgelerinizi analiz ederek yanıt verecek
          </p>
        </form>
      </div>
    </div>
  );
}
