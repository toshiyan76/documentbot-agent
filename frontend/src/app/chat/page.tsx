import ChatUI from './ChatUI'

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-gray-100 py-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          要件定義生成チャット
        </h1>
        <ChatUI />
      </div>
    </div>
  )
} 