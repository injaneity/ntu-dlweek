"use client"

import { useState, useEffect, useRef } from "react"
import { Tweet } from "./Tweet"
import { Skeleton } from "./ui/skeleton"
import { Button } from "./ui/button"
import { RefreshCw } from "lucide-react"
import BlueskyLogin from "./BlueskyLogin"
import { TweetType } from "@/pages/api/tweets" // adjust path if needed

export function Timeline() {
  const [displayedTweets, setDisplayedTweets] = useState<TweetType[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const timelineRef = useRef<HTMLDivElement>(null)

  // Utility function to fetch tweets from the API.
  async function fetchTweets(): Promise<TweetType[]> {
    try {
      const res = await fetch("/api/tweets")
      const data: TweetType[] = await res.json()
      return data
    } catch (error) {
      console.error("Error fetching tweets:", error)
      return []
    }
  }

  // On mount, fetch tweets once.
  useEffect(() => {
    async function initialFetch() {
      const data = await fetchTweets()
      setDisplayedTweets(data)
      setLoading(false)
    }
    initialFetch()
  }, [])

  // Poll the API every 5 seconds to check for new tweets.
  useEffect(() => {
    const interval = setInterval(async () => {
      const newData = await fetchTweets()
      // If there are new tweets (or the top tweet changed), update the timeline.
      if (
        newData.length > 0 &&
        (displayedTweets.length === 0 ||
          newData[0].cid !== displayedTweets[0].cid)
      ) {
        setDisplayedTweets(newData)
      }
    }, 5000) // Poll every 5 seconds.
    return () => clearInterval(interval)
  }, [displayedTweets])

  // Autoscroll to top when new tweets are added.
  useEffect(() => {
    if (displayedTweets.length > 0 && timelineRef.current) {
      if (timelineRef.current.scrollTop < 50) {
        timelineRef.current.scrollTo({ top: 0, behavior: "smooth" })
      }
    }
  }, [displayedTweets])

  const handleRefresh = async () => {
    setRefreshing(true)
    const data = await fetchTweets()
    setDisplayedTweets(data)
    setRefreshing(false)
  }

  return (
    <div className="space-y-4">
      {/* <div>
        <BlueskyLogin />
      </div> */}
      <div className="flex justify-between items-center mb-4 sticky top-0 bg-white dark:bg-gray-900 z-10 py-2">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Latest Tweets</h2>
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleRefresh}
            disabled={refreshing}
            className="text-blue-500"
          >
            <RefreshCw
              className={`h-5 w-5 ${refreshing ? "animate-spin" : ""}`}
            />
            <span className="sr-only">Refresh</span>
          </Button>
          {/* <div className="h-8 w-8 rounded-full bg-blue-500 text-white flex items-center justify-center overflow-hidden">
            <img
              src="/placeholder.svg?height=32&width=32"
              alt="Profile"
              className="w-full h-full object-cover"
            />
          </div> */}
        </div>
      </div>

      <div
        ref={timelineRef}
        className="space-y-4 max-h-[calc(100vh-80px)] overflow-y-auto pr-2"
      >
        {displayedTweets
          .filter(
            (tweet): tweet is TweetType =>
              Boolean(tweet && (tweet.cid || tweet.uri))
          )
          .map((tweet, index) => (
            <div
              key={tweet.cid || tweet.uri} // Use cid as primary key, or uri as fallback.
              className={`transition-all duration-500 ease-out ${
                index === 0 ? "animate-slide-down" : ""
              }`}
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

        {!loading && displayedTweets.length === 0 && (
          <p className="text-center text-gray-500">No tweets available</p>
        )}
      </div>
    </div>
  )
}
