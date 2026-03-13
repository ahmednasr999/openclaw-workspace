import type { MessageHandler } from '../../types'

export const handle: MessageHandler = async ({ message, channel, send }) => {
  const text = message.content?.text?.toLowerCase() || ''
  
  // Trigger keywords
  const triggers = ['list models', 'show models', 'model picker', 'pick model', '/models']
  const isTriggered = triggers.some(t => text.includes(t))
  
  if (!isTriggered) return
  
  // Model list
  const models = [
    { num: '1', id: 'minimax-m2.5', name: 'MiniMax M2.5', desc: 'Default, crons, quick (free)' },
    { num: '2', id: 'gpt54', name: 'GPT-5.4', desc: 'Coding, agentic work' },
    { num: '3', id: 'gpt54pro', name: 'GPT-5.4 Pro', desc: 'Maximum performance' },
    { num: '4', id: 'gpt53codex', name: 'GPT-5.3 Codex', desc: 'Legacy coding' },
    { num: '5', id: 'opus46', name: 'Claude Opus 4.6', desc: 'Deep strategy, CVs' },
    { num: '6', id: 'sonnet46', name: 'Claude Sonnet 4.6', desc: 'Drafting, content' },
    { num: '7', id: 'haiku', name: 'Claude Haiku 4.5', desc: 'Fast, lightweight' },
    { num: '8', id: 'kimi', name: 'Kimi K2.5', desc: 'Long context' },
  ]
  
  let response = '*Available models:*\n\n'
  for (const m of models) {
    response += `${m.num}. ${m.name} — ${m.desc}\n`
  }
  response += '\n_Reply with the number to switch._'
  
  await send(response)
}
