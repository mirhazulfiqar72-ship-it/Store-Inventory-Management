# Store Inventory Management — authenticated Firebase setup (v1.0.95)

## What changed
- Firebase Realtime Database uses project `store-inventory-a46b0` as before.
- Firebase Rules currently require `auth != null`. The old Windows app did not pass an ID token; therefore its unauthenticated HTTP requests returned 401.
- Updated app signs in with Firebase **Email/Password** via Google's Identity Toolkit REST API and sends an ID token with every RTDB read/write, lock, and background refresh.
- Password is **never saved** and is only sent to Google's HTTPS sign-in endpoint. A refresh token can be cached with **Windows DPAPI** (tied to current Windows account); never in plaintext.
- The clean 102-code dataset is stored in `store_inventory_v2/data`. This path is separate from legacy `store_inventory/data`, so pre-update Windows installations cannot re-upload thousands of old codes into clean v2.
- Initial migration backs up the old online snapshot and SQLite to `C:\StoreInventoryManagement\Backups`; existing MTO, parties, and users are carried over. Old legacy inventory transactions are excluded per original 102-code reset request.
- After initialization, **new** Inventory Codes and transactions in v2 are preserved on every subsequent app start.

## First PC: login inside the updated Windows program
1. Enable **Authentication → Sign-in method → Email/Password** in Firebase Console (already completed).
2. In **Authentication → Users**, create a Firebase user (already completed). Do **not** share the password in chat, GitHub, or screenshots.
3. Find your Firebase **Web API Key** in **Project settings → General → Web API Key**. This key is a public client identifier, not a private service account key.
4. Close older Store Inventory Management versions on every PC.
5. Install the new version and run. In the **Firebase Online Sign-in** dialog, paste your project's Web API Key, your Firebase user email, and password.
6. The app obtains a short-lived ID token, then initializes or reads the clean inventory under `store_inventory_v2`.
7. Confirm the Inventory Codes screen displays **102** records before editing, importing, or entering transactions. If it does not, stop and retain the backup.

## Second PC
- Install the same updated version and sign in using an authorized Firebase account belonging to the **same project**.
- Only the clean `store_inventory_v2` dataset is synced.
- Do not use an old version with the v2 dataset.

## Improve Firebase Security Rules
Important: Existing rules `.read: auth != null`, `.write: auth != null` allow **Anonymous** Firebase users too when the Anonymous provider is enabled. This is not an adequate access restriction for production inventory.

After the first clean v2 backup and verified login, use a UID allowlist (replace `YOUR_FIREBASE_USER_UID` with the complete UID in **Authentication → Users**):

```json
{
  "rules": {
    ".read": false,
    ".write": false,
    "store_inventory": {
      ".read": "auth != null && auth.uid === 'YOUR_FIREBASE_USER_UID'",
      ".write": false
    },
    "store_inventory_v2": {
      ".read": "auth != null && auth.uid === 'YOUR_FIREBASE_USER_UID'",
      ".write": "auth != null && auth.uid === 'YOUR_FIREBASE_USER_UID'"
    }
  }
}
```

For additional authorized accounts, use explicit UID allowlisting (or properly configured Firebase custom claims). Ensure you back up and verify permissions in the Rules Playground before publishing. **Do not change root rules to `true`**, do not share passwords or service-account private keys.

## Verification caveat
GitHub Actions run mock/offline security and migration regression tests. The CI build environment intentionally has **no real Firebase login credentials**, so it cannot prove live production access. Production login and online 102-code count must be verified on the user's authenticated Windows installation. Prior CI 401 errors were caused by unauthenticated test requests and do not themselves prove that correctly authenticated reads/writes fail.
