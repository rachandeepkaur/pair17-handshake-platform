import { useRef, useState } from 'react'
import { Camera } from 'lucide-react'
import Avatar from '../ui/Avatar'
import Button from '../ui/Button'
import { apiUrl, errorMessage } from '../../services/api'

const MAX_BYTES = 2 * 1024 * 1024
const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp']

export default function ProfilePicture({ name, pictureUrl, onUpload }) {
  const inputRef = useRef(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const handleFile = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    if (!ACCEPTED.includes(file.type)) return setError('Choose a JPEG, PNG, or WebP image.')
    if (file.size > MAX_BYTES) return setError('Image must be 2 MB or smaller.')

    setError('')
    setUploading(true)
    try {
      await onUpload(file)
    } catch (err) {
      setError(errorMessage(err, 'Upload failed'))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="flex items-center gap-4">
      {pictureUrl ? (
        <img src={apiUrl(pictureUrl)} alt={`${name} logo`} className="h-20 w-20 rounded-2xl object-cover" />
      ) : (
        <Avatar name={name} size="lg" className="!h-20 !w-20 !rounded-2xl !text-xl" />
      )}
      <div>
        <input ref={inputRef} type="file" accept={ACCEPTED.join(',')} className="hidden" onChange={handleFile} />
        <Button
          type="button"
          variant="outline"
          size="sm"
          icon={Camera}
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
        >
          {uploading ? 'Uploading…' : pictureUrl ? 'Change picture' : 'Upload picture'}
        </Button>
        <p className="mt-1 text-xs text-gray-500">JPEG, PNG, or WebP · up to 2 MB</p>
        {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
      </div>
    </div>
  )
}
