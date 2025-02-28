import { useState, useEffect } from "react";
import { loginToBluesky, getProfile } from "../lib/bluesky";

export default function BlueskyLogin() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const fetchUser = async () => {
      const session = await loginToBluesky();
      if (session) {
        const profile = await getProfile();
        setUser(profile);
      }
    };
    fetchUser();
  }, []);

  return (
    <div className="p-4 border rounded shadow-lg max-w-md mx-auto bg-gray-900">
      <h2 className="text-xl font-bold mb-4 text-white">Bluesky Auto Login</h2>
  
      {user ? (
        <div className="mt-4 p-4 border rounded">
          <h3 className="font-bold text-lg text-white">{user.displayName}</h3>
          <p className="text-white">@{user.handle}</p>
          {user.avatar && <img src={user.avatar} alt="Avatar" className="w-16 h-16 rounded-full mt-2" />}
        </div>
      ) : (
        <p className="text-white">Logging in...</p>
      )}
    </div>
  );
}