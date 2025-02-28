// pages/api/tweets.ts
import type { NextApiRequest, NextApiResponse } from 'next'

export type TweetType = {
  author: string
  record: {
    created_at: string
    text: string
    labels?: any
    langs: string[]
  }
  uri: string
  cid: string
}

// Module-level variable for mock persistence
let tweets: TweetType[] = []
export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    res.status(200).json(tweets)
  } else if (req.method === 'POST') {
    let newTweet: TweetType | null = null
    try {
      // The payload might be a stringified JSON, so try to parse it.
      const { tweet } = req.body
      newTweet = typeof tweet === 'string' ? JSON.parse(tweet) : tweet
      console.log(newTweet)
    } catch (error) {
      return res.status(400).json({ error: 'Invalid tweet format' })
    }
    
    if (!newTweet) {
      return res.status(400).json({ error: 'No tweet provided' })
    }

    // Add the new tweet at the beginning of the list.
    tweets.unshift(newTweet)
    res.status(201).json(newTweet)
  } else {
    res.setHeader('Allow', ['GET', 'POST'])
    res.status(405).end(`Method ${req.method} Not Allowed`)
  }
}
