// pages/api/profile.ts
import type { NextApiRequest, NextApiResponse } from 'next'
import { BskyAgent } from '@atproto/api'

const agent = new BskyAgent({ service: 'https://bsky.social' })

// You could initialize the login once and reuse the session.
async function ensureLoggedIn() {
  if (!agent.session) {
    await agent.login({
      identifier: process.env.BSKY_IDENTIFIER || '',
      password: process.env.BSKY_PASSWORD || ''
    })
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { actor } = req.query
  if (!actor || typeof actor !== 'string') {
    return res.status(400).json({ error: 'Actor (DID) is required' })
  }

  try {
    await ensureLoggedIn()
    // Use the agent to fetch the profile data.
    const profile = await agent.getProfile({ actor })
    res.status(200).json(profile.data)
  } catch (error) {
    console.error('Error fetching profile:', error)
    res.status(500).json({ error: 'Internal Server Error' })
  }
}
