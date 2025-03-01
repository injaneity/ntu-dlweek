// Load environment variables
const handle = process.env.NEXT_PUBLIC_BSKY_HANDLE;
const password = process.env.NEXT_PUBLIC_BSKY_PASSWORD;

// Store the access token
let accessJwt: string | null = null;
let actor: string | null = 'did:plc:zlbw35luwsbu5lnv3psyyr3m';

export const loginToBluesky = async () => {
  try {
    if (!handle || !password) {
      throw new Error("❌ Missing Bluesky credentials in environment variables");
    }

    const response = await fetch("https://bsky.social/xrpc/com.atproto.server.createSession", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        identifier: handle, // Your Bluesky handle
        password: password, // Your App Password
      }),
    });

    if (!response.ok) {
      throw new Error(`❌ Login failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log("✅ Successfully logged in!", data);

    // Store access token for future API requests
    accessJwt = data.accessJwt;

    return {
      accessJwt: data.accessJwt,
      refreshJwt: data.refreshJwt,
      did: data.did,
      handle: data.handle,
    };
  } catch (error) {
    console.error("❌ Error logging in:", error);
    return null;
  }
};

// Fetch user profile with authentication
export const getProfile = async () => {
  try {
    if (!accessJwt) {
      console.error("❌ No access token found. Logging in...");
      await loginToBluesky(); // Ensure we have a token
    }

    const response = await fetch(`https://bsky.social/xrpc/app.bsky.actor.getProfile?actor=${actor}`, {
      method: "GET", // API typically expects GET, but using POST as requested
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessJwt}`, // Use the stored JWT token
      }
    });

    if (!response.ok) {
      throw new Error(`❌ Profile fetch failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log("✅ Profile fetched successfully!", data);

    return data;
  } catch (error) {
    console.error("❌ Failed to get profile:", error);
    return null;
  }
};