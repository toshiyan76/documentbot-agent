'use client'
import { useState, useEffect, useRef } from 'react'

export default function ChatUI() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([])
  const [isLoading, setIsLoading] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)
  const retryCountRef = useRef(0)
  const MAX_RETRIES = 3

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // タイムアウト付きのfetch関数
  const fetchWithTimeout = async (
    url: string, 
    options: RequestInit & { timeoutMs?: number }
  ): Promise<Response> => {
    const { timeoutMs = 600000, ...fetchOptions } = options // デフォルト10分
    abortControllerRef.current = new AbortController()

    try {
      const fetchPromise = fetch(url, {
        ...fetchOptions,
        signal: abortControllerRef.current.signal,
      })

      const timeoutPromise = new Promise<Response>((_, reject) => {
        setTimeout(() => {
          if (abortControllerRef.current) {
            abortControllerRef.current.abort()
          }
          reject(new Error('Request timed out'))
        }, timeoutMs)
      })

      return await Promise.race([fetchPromise, timeoutPromise])
    } catch (error) {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      throw error
    }
  }

  const handleSubmit = async () => {
    if (!input || isLoading) return
    
    try {
      setIsLoading(true)
      const userMessage = { role: 'user', content: input }
      setMessages(prev => [...prev, userMessage])
      
      const response = await fetchWithTimeout('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
        timeoutMs: 600000, // 10分
      })

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('Response body is null')

      let assistantMessage = { role: 'assistant', content: '' }
      setMessages(prev => [...prev, assistantMessage])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        try {
          const parsedChunk = JSON.parse(chunk)
          assistantMessage.content = parsedChunk.response || parsedChunk
          setMessages(prev => 
            prev.map((msg, i) => 
              i === prev.length - 1 ? assistantMessage : msg
            )
          )
        } catch (e) {
          console.warn('Failed to parse chunk:', e)
          assistantMessage.content += chunk
          setMessages(prev => 
            prev.map((msg, i) => 
              i === prev.length - 1 ? assistantMessage : msg
            )
          )
        }
      }

      retryCountRef.current = 0
      
    } catch (error) {
      console.error('Error:', error)
      
      if (retryCountRef.current < MAX_RETRIES && 
          error instanceof Error && 
          (error.name === 'AbortError' || error.message.includes('socket') || error.message.includes('timeout'))) {
        retryCountRef.current++
        console.log(`Retrying... (${retryCountRef.current}/${MAX_RETRIES})`)
        setTimeout(() => handleSubmit(), 1000 * Math.pow(2, retryCountRef.current))
        return
      }

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'エラーが発生しました。もう一度お試しください。'
      }])
    } finally {
      setInput('')
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="border rounded-lg p-4 mb-4 h-[600px] overflow-y-auto bg-gray-50">
        {messages.map((msg, i) => (
          <div key={i} className={`mb-3 ${msg.role === 'user' ? 'text-right' : ''}`}>
            <div className={`inline-block p-3 rounded-lg max-w-[80%] whitespace-pre-wrap ${
              msg.role === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-white text-gray-800 border'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
          className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="プロジェクトの要件を入力してください..."
          disabled={isLoading}
        />
        <button
          onClick={handleSubmit}
          className={`px-6 py-2 rounded-lg text-white ${
            isLoading ? 'bg-gray-400' : 'bg-blue-500 hover:bg-blue-600'
          }`}
          disabled={isLoading}
        >
          {isLoading ? '生成中...' : '送信'}
        </button>
      </div>
    </div>
  )
} 