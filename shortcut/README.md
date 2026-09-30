# iOS Shortcut setup

## 1. Create a GitHub token for the Shortcut

GitHub → Settings → Developer settings → **Fine-grained tokens** → Generate new token
- Repository access: **Only select repositories** → `doomscroll_assistant`
- Permissions → Repository → **Contents: Read and write** (needed for `repository_dispatch`)
- Set an expiration you're comfortable with.

This token can only touch this one repo.

## 2. Build the Shortcut

Shortcuts app → **+** → name it **Save to Vault**.

1. Open the shortcut's settings: tap its **name at the top → Details** (iOS 17+) or the
   **ⓘ** button at the bottom (iOS 16). Turn on **Show in Share Sheet**, then tap **Done**.
2. A **Receive** block now appears at the top of the shortcut. (It isn't an action you can
   search for; it only appears once Show in Share Sheet is on.)
   - Tap *Images and 18 more* → **Clear** → select **URLs** and **Text**.
     Instagram sometimes shares the link as text.
   - Set **If there's no input** → **Get Clipboard**.
3. Add actions below it:
   - **Get URLs from Input**. This extracts the link even when it arrives as text.
   - **Ask for Input** → Text, prompt "Why save this? (optional)". There's no "allow empty"
     toggle: leave it blank and tap Done. If Done is disabled when empty, set Default Answer to `-`.
   - **Get Contents of URL**
     - URL: `https://api.github.com/repos/samuellvo/doomscroll_assistant/dispatches`
     - Method: **POST**
     - Headers:
       - `Authorization`: `Bearer <your token>`
       - `Accept`: `application/vnd.github+json`
     - Request Body: **JSON**
       - `event_type` (Text): `new-reel`
       - `client_payload` (Dictionary):
         - `url` (Text): *URLs* (the output of Get URLs from Input)
         - `note` (Text): *Provided Input*
   - **Show Notification** → "Sent to vault ✓"

GitHub returns `204 No Content` on success. Anything else means the token or URL is wrong.

## 3. Use it

Instagram → reel → **Share** (paper plane) → **Share to…** → **Save to Vault**.
Watch progress in the repo's **Actions** tab.

If you don't see Shortcuts in Instagram's share list, use **Copy link** and run the Shortcut
from the home screen instead; it falls back to the clipboard.
