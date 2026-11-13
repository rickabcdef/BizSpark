# BizSpark Privacy Policy

**Last updated: 2026-11-13 · Applies to BizSpark 1.0.0 (Windows, macOS)**

BizSpark is a one-time purchase desktop application that helps a single person pick a small business idea and print a one-page plan. This policy is deliberately short, because the app does very little with your information.

## The short version

- We do not have an account system. You never give us your name, email, or password to use the app.
- Your answers, saved ideas, and exported plans stay on your own device.
- We do not run analytics, telemetry, advertising SDKs, or crash reporting.
- Nothing you type is uploaded to us. There is no server that receives your answers.

## What is stored, and where

Everything the app knows lives in a local application data folder on your device:

| Stored locally | Why | Leaves the device? |
| --- | --- | --- |
| Your quiz answers (5 questions) | To compute and re-open your recommendations | No |
| Saved ideas and their notes | So the Library screen can list them later | No |
| Settings (language, theme, export folder) | To remember your preferences | No |
| The idea library and its monthly update | The business ideas themselves, shipped with the app | No |
| License state (if you activate a code) | To keep the app unlocked on this device | No |

Deleting the application data folder removes all of the above. Uninstalling the app is enough for most people; the folder is listed in the app's Settings screen so you can find it.

## The one network request the app can make

The idea library receives an optional monthly content update. When the app checks for it, it performs a single HTTPS `GET` for a static manifest file, with a 3-second timeout. If the check fails, times out, or you are offline, the app silently keeps using the local library — you will not see an error dialog, and nothing is blocked.

That request carries **no** personal data: no answers, no identifiers, no usage events. Our content host sees an ordinary web request for a public file, the same as downloading a page. There is no other outbound traffic in the app — the build enforces this with a network guard that blocks sockets outside that one call.

## Device fingerprint (only when you activate a license code)

If you enter a license code, the app computes a one-way SHA-256 hash derived from stable hardware attributes. It contains no IP address, no MAC address, and no raw machine identifier, and it cannot be reversed into a description of your computer. It is used for exactly one purpose: counting how many devices a code has been activated on, so a code cannot be shared unlimited times.

- The hash is stored locally with the license record.
- It is never combined with your answers or your saved ideas.
- No email address, name, or payment detail is stored by the app — the store handles the purchase, not us.

## Children

BizSpark is a general-audience business tool. It is not directed at children and collects no information from anyone, including children.

## Your choices

- **Use it fully offline.** Turn off the network and every core feature still works; only the optional library update is skipped.
- **Delete your data.** Remove the application data folder, or uninstall the app. There is no cloud copy to delete because there is no cloud copy.
- **Do not activate.** The app runs without a license code for evaluation; activation is what creates the device hash.

## Changes

If this policy ever changes in a way that affects what is stored or sent, the updated version ships with the next app release and the date at the top changes. Because the app is local-first, a policy change cannot retroactively move old data anywhere — there is nothing on our side to move.

## Contact

Questions about privacy, or a request to confirm what the app stores: **support@bizspark.app**

We answer support mail by hand. There is no ticket portal, no chat widget, and no marketing list.
