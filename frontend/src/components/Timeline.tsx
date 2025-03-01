"use client";

import { useState, useEffect, useRef } from "react";
import { Tweet } from "./Tweet";
import { Skeleton } from "./ui/skeleton";
import { Button } from "./ui/button";
import { RefreshCw } from "lucide-react";

// Import the static tweets JSON — make sure the path is correct.
import tweetsData from "./tweets.json";

// Optionally, if you have a TweetType type, you can define it like this:
// interface TweetType {
//   record: {
//     created_at: string;
//     text: string;
//     labels: any;
//     langs: string[];
//   };
//   uri: string;
//   cid: string;
//   author: string;
//   label: number;
// }

export function Timeline() {
  // Start with the first tweet (if available); the rest will be added sequentially.
  const [displayedTweets, setDisplayedTweets] = useState(
    tweetsData.length > 0 ? [tweetsData[0]] : []
  );
  const [loading, setLoading] = useState(tweetsData.length === 0);
  const [refreshing, setRefreshing] = useState(false);
  const timelineRef = useRef<HTMLDivElement>(null);

  // Every 5 seconds, add the next tweet from tweetsData (if any)
  useEffect(() => {
    if (tweetsData.length > 0) {
      setLoading(false);
    }
    const interval = setInterval(() => {
      setDisplayedTweets((prev) => {
        const nextIndex = prev.length;
        if (nextIndex < tweetsData.length) {
          // Prepend the new tweet so that it appears at the top.
          return [tweetsData[nextIndex], ...prev];
        }
        return prev;
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to top when new tweets are added.
  useEffect(() => {
    if (displayedTweets.length > 0 && timelineRef.current) {
      if (timelineRef.current.scrollTop < 50) {
        timelineRef.current.scrollTo({ top: 0, behavior: "smooth" });
      }
    }
  }, [displayedTweets]);

  // Refresh handler: here we simply reset the timeline
  // back to the first tweet.
  const handleRefresh = () => {
    setRefreshing(true);
    setDisplayedTweets(tweetsData.length > 0 ? [tweetsData[0]] : []);
    setRefreshing(false);
  };

  return (
    <div className="space-y-4">
      <div
        className="flex justify-between items-center mb-4 sticky top-0 bg-white
                   dark:bg-gray-900 z-10 py-2"
      >
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Latest Tweets
        </h2>
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleRefresh}
            disabled={refreshing}
            className="text-blue-500"
          >
            <RefreshCw
              className={`h-5 w-5 ${
                refreshing ? "animate-spin" : ""
              }`}
            />
            <span className="sr-only">Refresh</span>
          </Button>
        </div>
      </div>

      <div
        ref={timelineRef}
        className="space-y-4 max-h-[calc(100vh-80px)] overflow-y-auto pr-2"
      >
        {displayedTweets
          .filter(
            (tweet) =>
              Boolean(tweet && (tweet.cid || tweet.uri))
          )
          .map((tweet, index) => (
            <div
              key={tweet.cid || tweet.uri}
              className={`transition-all duration-500 ease-out ${
                index === 0 ? "animate-slide-down" : ""
              }`}
            >
              {/* We pass down a "censor" prop if tweet.label is 1 */}
              <Tweet tweet={tweet} censor={tweet.label === 1} />
            </div>
          ))}

        {loading && (
          <div
            className="border border-gray-200 dark:border-gray-700 rounded-xl
                       p-4 space-y-3"
          >
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
          <p className="text-center text-gray-500">
            No tweets available
          </p>
        )}
      </div>
    </div>
  );
}
