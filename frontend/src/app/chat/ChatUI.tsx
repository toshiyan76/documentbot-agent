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
      console.log('Starting fetch with options:', {
        url,
        method: options.method,
        headers: options.headers,
        timeout: timeoutMs
      })

      const fetchPromise = fetch(url, {
        ...fetchOptions,
        signal: abortControllerRef.current.signal,
      })

      const timeoutPromise = new Promise<Response>((_, reject) => {
        setTimeout(() => {
          if (abortControllerRef.current) {
            abortControllerRef.current.abort()
          }
          reject(new Error(`Request timed out after ${timeoutMs}ms`))
        }, timeoutMs)
      })

      return await Promise.race([fetchPromise, timeoutPromise])
    } catch (error) {
      console.error('Fetch error:', {
        error: error,
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      })
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
      
      console.log('Sending request to:', '/api/chat')
      const response = await fetchWithTimeout('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
        timeoutMs: 600000, // 10分
      })

      console.log('Response status:', response.status)
      console.log('Response headers:', Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        const errorText = await response.text()
        console.error('API Error Details:', {
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()),
          body: errorText
        })
        throw new Error(`API Error: ${response.status} - ${response.statusText}\nDetails: ${errorText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        console.error('Response body is null')
        throw new Error('Response body is null')
      }

      let assistantMessage = { role: 'assistant', content: '' }
      setMessages(prev => [...prev, assistantMessage])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        console.log('Received chunk:', chunk)
        try {
          const parsedChunk = JSON.parse(chunk)
          console.log('Parsed chunk:', parsedChunk)
          assistantMessage.content = parsedChunk.response || parsedChunk
          setMessages(prev => 
            prev.map((msg, i) => 
              i === prev.length - 1 ? assistantMessage : msg
            )
          )
        } catch (e) {
          console.warn('Failed to parse chunk:', {
            error: e,
            chunk: chunk,
            assistantMessage: assistantMessage
          })
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
      console.error('Error in handleSubmit:', {
        error: error,
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
        retryCount: retryCountRef.current
      })
      
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
        content: `エラーが発生しました: ${error instanceof Error ? error.message : '不明なエラー'}\n\n詳細はブラウザのコンソールを確認してください。`
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