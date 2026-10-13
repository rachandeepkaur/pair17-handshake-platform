import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorMessage } from '../services/api'
import { startConversation } from '../services/messageService'

// Opens (or reuses) the conversation with a student and jumps to it.
export function useMessageStudent() {
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const messageStudent = async (studentId) => {
    setBusy(true)
    setError('')
    try {
      const conversation = await startConversation(studentId)
      navigate(`/company/messages?c=${conversation.id}`)
    } catch (err) {
      setError(errorMessage(err, 'Could not open the conversation'))
      setBusy(false)
    }
  }

  return { messageStudent, busy, error }
}
