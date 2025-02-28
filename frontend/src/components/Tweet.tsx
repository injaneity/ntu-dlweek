import { Heart, MessageCircle, Repeat2, Share } from "lucide-react"
import { Button } from "./ui/button"

interface TweetProps {
  tweet: {
    id: string
    author: {
      name: string
      handle: string
      avatar: string
    }
    content: string
    image?: string
    timestamp: string
    likes: number
    retweets: number
    replies: number
  }
}

export function Tweet({ tweet }: TweetProps) {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-xl p-4 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50">
      <div className="flex gap-3">
        <div className="flex-shrink-0">
          <img
            src={tweet.author.avatar || "/placeholder.svg"}
            alt={tweet.author.name}
            className="w-12 h-12 rounded-full"
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1">
            <p className="font-semibold text-gray-900 dark:text-white truncate">{tweet.author.name}</p>
            <p className="text-gray-500 dark:text-gray-400 truncate">{tweet.author.handle}</p>
            <span className="text-gray-500 dark:text-gray-400">·</span>
            <p className="text-gray-500 dark:text-gray-400">{tweet.timestamp}</p>
          </div>

          <p className="mt-1 text-gray-900 dark:text-white whitespace-pre-wrap">{tweet.content}</p>

          {tweet.image && (
            <div className="mt-3 rounded-xl overflow-hidden">
              <img src={tweet.image || "/placeholder.svg"} alt="Tweet image" className="w-full h-auto object-cover" />
            </div>
          )}

          <div className="mt-3 flex justify-between max-w-md">
            <Button
              variant="ghost"
              size="icon"
              className="text-gray-500 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-full"
            >
              <MessageCircle className="h-5 w-5" />
              <span className="sr-only">Reply</span>
              {tweet.replies > 0 && <span className="ml-2 text-xs">{tweet.replies}</span>}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-gray-500 hover:text-green-500 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-full"
            >
              <Repeat2 className="h-5 w-5" />
              <span className="sr-only">Retweet</span>
              {tweet.retweets > 0 && <span className="ml-2 text-xs">{tweet.retweets}</span>}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full"
            >
              <Heart className="h-5 w-5" />
              <span className="sr-only">Like</span>
              {tweet.likes > 0 && <span className="ml-2 text-xs">{tweet.likes}</span>}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-gray-500 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-full"
            >
              <Share className="h-5 w-5" />
              <span className="sr-only">Share</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

