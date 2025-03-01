"use client";

import { useState, useEffect } from "react";
import {
  Heart,
  MessageCircle,
  Repeat2,
  Share,
} from "lucide-react";
import { Button } from "./ui/button";

interface TweetProps {
  tweet: {
    uri: string;
    cid: string;
    record: {
      created_at: string;
      text: string;
      langs: string[];
      censor_value: number;
    };
    author: string; // e.g. a DID
  };
}

function getRelativeTime(timestamp: string): string {
  const now = Date.now();
  const tweetTime = new Date(timestamp).getTime();
  const diffInSeconds = Math.floor((now - tweetTime) / 1000);

  if (diffInSeconds < 60) {
    return `${diffInSeconds} second${diffInSeconds !== 1 ? "s" : ""} ago`;
  }
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes} minute${diffInMinutes !== 1 ? "s" : ""} ago`;
  }
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours} hour${diffInHours !== 1 ? "s" : ""} ago`;
  }
  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays} day${diffInDays !== 1 ? "s" : ""} ago`;
}

export function Tweet({ tweet }: TweetProps) {
  const text = tweet.record?.text || "No content";
  const rawTimestamp = tweet.record?.created_at;
  const timestamp = rawTimestamp
    ? getRelativeTime(rawTimestamp)
    : "unknown time";

  // Initialize internal state based on censor_value.
  const [isBlurred, setIsBlurred] = useState(
    tweet.record?.censor_value === 1
  );

  // Derive the author name by stripping "did:plc:" from the DID.
  const didPrefix = "did:plc:";
  const authorName = tweet.author.startsWith(didPrefix)
    ? tweet.author.slice(didPrefix.length + 10)
    : tweet.author;
  // Set a fixed handle value.
  const authorHandle = "@anonymous";

  // Random avatar from the internet using Picsum Photos.
  const [randomAvatar, setRandomAvatar] = useState<string>("");

  useEffect(() => {
    const randomSeed = Math.floor(Math.random() * 10000);
    setRandomAvatar(`https://picsum.photos/seed/${randomSeed}/48`);
  }, []);

  const avatar = randomAvatar || "/placeholder.svg";

  // Handler to remove blur on click.
  const handleUncensor = () => {
    console.log("handleUncensor clicked");
    if (isBlurred) {
      setIsBlurred(false);
    }
  };

  return (
    <div
      className="border border-gray-200 dark:border-gray-700 rounded-xl
                 p-4 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
    >
      <div className="flex gap-3">
        <div className="flex-shrink-0">
          <img
            src={avatar}
            alt={authorName}
            className="w-12 h-12 rounded-full"
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1">
            <p className="font-semibold text-gray-900 dark:text-white truncate">
              {authorName}
            </p>
            <p className="text-gray-500 dark:text-gray-400 truncate">
              {authorHandle}
            </p>
            <span className="text-gray-500 dark:text-gray-400">·</span>
            <p className="text-gray-500 dark:text-gray-400">{timestamp}</p>
          </div>
          <p
            onClick={handleUncensor}
            className={`mt-1 text-gray-900 dark:text-white whitespace-pre-wrap ${
              isBlurred ? "blur-sm cursor-pointer" : ""
            }`}
            title={isBlurred ? "Censored. Click to reveal." : undefined}
          >
            {text}
          </p>
          <div className="mt-3 flex justify-between max-w-md">
            <Button
              variant="ghost"
              size="icon"
              className="text-gray-500 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-full"
            >
              <MessageCircle className="h-5 w-5" />
              <span className="sr-only">Reply</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-gray-500 hover:text-green-500 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-full"
            >
              <Repeat2 className="h-5 w-5" />
              <span className="sr-only">Retweet</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full"
            >
              <Heart className="h-5 w-5" />
              <span className="sr-only">Like</span>
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
  );
}
