"use client"

import { useState, useEffect, useRef } from "react"
import { Tweet } from "@/components/tweet"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { RefreshCw } from "lucide-react"
import Image from "next/image"

// Sample tweet data
const SAMPLE_TWEETS = [
  {
    id: "1",
    author: {
      name: "Jane Smith",
      handle: "@janesmith",
      avatar: "/placeholder.svg?height=48&width=48",
    },
    content: "Just launched my new website! Check it out at example.com #webdev #design",
    timestamp: "2m",
    likes: 15,
    retweets: 3,
    replies: 2,
  },
  {
    id: "2",
    author: {
      name: "Tech News",
      handle: "@technews",
      avatar: "/placeholder.svg?height=48&width=48",
    },
    content:
      "Breaking: New AI model can generate realistic images from text descriptions. This could revolutionize content creation.",
    timestamp: "10m",
    likes: 142,
    retweets: 57,
    replies: 23,
  },
  {
    id: "3",
    author: {
      name: "Travel Enthusiast",
      handle: "@travelbug",
      avatar: "/placeholder.svg?height=48&width=48",
    },
    content: "Sunrise at Mount Fuji. Worth waking up at 4am for this view! 🌄 #japan #travel",
    image: "/placeholder.svg?height=300&width=500",
    timestamp: "1h",
    likes: 324,
    retweets: 87,
    replies: 42,
  },
  {
    id: "4",
    author: {
      name: "Coding Tips",
      handle: "@codetips",
      avatar: "/placeholder.svg?height=48&width=48",
    },
    content:
      "Pro tip: Learn keyboard shortcuts for your code editor. It will save you hours in the long run. #programming #productivity",
    timestamp: "2h",
    likes: 89,
    retweets: 12,
    replies: 5,
  },
  {
    id: "5",
    author: {
      name: "Book Lover",
      handle: "@bookworm",
      avatar: "/placeholder.svg?height=48&width=48",
    },
    content:
      "Just finished reading 'Project Hail Mary' by Andy Weir. Absolutely brilliant sci-fi novel! Highly recommend. 📚 #books #reading",
    timestamp: "3h",
    likes: 56,
    retweets: 8,
    replies: 14,
  },
]

export function Timeline() {
  const [tweets, setTweets] = useState<typeof SAMPLE_TWEETS>([])
  const [loading, setLoading] = useState(true)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const timelineRef = useRef<HTMLDivElement>(null)

  // Simulate fetching tweets one by one
  useEffect(() => {
    if (currentIndex < SAMPLE_TWEETS.length && loading) {
      const timer = setTimeout(() => {
        setTweets((prevTweets) => [SAMPLE_TWEETS[currentIndex], ...prevTweets])
        setCurrentIndex((prevIndex) => prevIndex + 1)

        if (currentIndex === SAMPLE_TWEETS.length - 1) {
          setLoading(false)
          setHasMore(false)
        }
      }, 2000) // 2 second delay between tweets

      return () => clearTimeout(timer)
    }
  }, [currentIndex, loading])

  // Autoscroll to top when new tweet is added
  useEffect(() => {
    if (tweets.length > 0 && timelineRef.current) {
      const scrollPosition = timelineRef.current.scrollTop
      if (scrollPosition < 50) {
        // Only autoscroll if user is near the top
        timelineRef.current.scrollTo({
          top: 0,
          behavior: "smooth",
        })
      }
    }
  }, [tweets])

  const handleRefresh = () => {
    setRefreshing(true)
    // Simulate refresh
    setTimeout(() => {
      setTweets([])
      setCurrentIndex(0)
      setLoading(true)
      setHasMore(true)
      setRefreshing(false)
    }, 1000)
  }

  const loadMore = () => {
    // In a real app, you would fetch more tweets here
    // For this demo, we'll just show a message
    alert("In a real app, this would load more tweets!")
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4 sticky top-0 bg-white dark:bg-gray-900 z-10 py-2">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Latest Tweets</h2>
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="icon" onClick={handleRefresh} disabled={refreshing} className="text-blue-500">
            <RefreshCw className={`h-5 w-5 ${refreshing ? "animate-spin" : ""}`} />
            <span className="sr-only">Refresh</span>
          </Button>
          <div className="h-8 w-8 rounded-full bg-blue-500 text-white flex items-center justify-center overflow-hidden">
            <Image src="/placeholder.svg?height=32&width=32" alt="Profile" width={32} height={32} />
          </div>
        </div>
      </div>

      <div ref={timelineRef} className="space-y-4 max-h-[calc(100vh-80px)] overflow-y-auto pr-2">
        {tweets.map((tweet, index) => (
          <div
            key={tweet.id}
            className={`transition-all duration-500 ease-out ${index === 0 ? "animate-slide-down" : ""}`}
          >
            <Tweet tweet={tweet} />
          </div>
        ))}

        {loading && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-xl p-4 space-y-3">
            <div className="flex items-center space-x-3">
              <Skeleton className="h-12 w-12 rounded-full" />
              <div className="space-y-2 flex-1">
                <Skeleton className="h-4 w-1/4" />
                <Skeleton className="h-4 w-1/3" />
              </div>
            </div>
            <Skeleton className="h-16 w-full" />
            <div className="flex justify-between">
              <Skeleton className="h-8 w-8 rounded-full" />
              <Skeleton className="h-8 w-8 rounded-full" />
              <Skeleton className="h-8 w-8 rounded-full" />
              <Skeleton className="h-8 w-8 rounded-full" />
            </div>
          </div>
        )}

        {!loading && hasMore && (
          <Button
            variant="outline"
            className="w-full text-blue-500 border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950"
            onClick={loadMore}
          >
            Load more tweets
          </Button>
        )}
      </div>
    </div>
  )
}

