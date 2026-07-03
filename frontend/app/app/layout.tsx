'use client'

import { useAuth } from '@/src/context/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import { ThemeProvider } from '@/src/context/ThemeContext'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, token, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !token) {
      router.replace('/login')
    }
  }, [loading, token, router])

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-surface-dark flex items-center justify-center">
        <LoadingIndicator />
      </div>
    )
  }

  return (
    <ThemeProvider>
      {children}
    </ThemeProvider>
  )
}
