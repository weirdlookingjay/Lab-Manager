export interface Computer {
  ip_address: string
  label: string
  last_seen: string
  is_online: boolean
  model: string | null
  last_transfer: string | null
  total_transfers: number
  successful_transfers: number
  failed_transfers: number
  total_bytes_transferred: number
  os_version: string | null
  user_profile: string | null
}
