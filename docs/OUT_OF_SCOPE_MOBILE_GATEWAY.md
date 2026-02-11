# Out-of-scope improvement: Mobile gateways and distributed store-and-forward

This document describes a **possible future improvement** that extends the idea of this project (LoRa/Meshtastic → OSM Notes) but **falls outside the current scope**. The current project focuses on a **fixed gateway** (e.g. Raspberry Pi + serial Meshtastic). What follows is a separate line of work: **mobile clients as potential note creators**.

---

## Current scope vs. this idea

| Aspect | Current project | This idea (out of scope) |
|--------|-----------------|--------------------------|
| **Hardware** | Fixed gateway (e.g. RPi + USB Meshtastic) | Mobile phone + Meshtastic device (e.g. Bluetooth T-Echo) |
| **Connectivity** | Gateway has (or is expected to have) internet | Phone may be offline when receiving; creates notes when internet is available later |
| **Who creates notes** | Only the gateway(s) that receive the message | Any device that received the message and later gets online (gateways + phones) |
| **Deployment** | Single codebase: this repo (Python, systemd, etc.) | New app(s): mobile client(s), different stack (e.g. Kotlin/Swift, React Native, etc.) |

---

## Idea in short

- **Problem:** Messages that never reach any fixed gateway are lost; no OSM note is created.
- **Idea:** A **mobile app** that:
  - Listens to the **public channel** (same as the gateway).
  - Receives `#osmnote` messages when the user (and their Meshtastic device) is in range of the mesh.
  - **Stores** those messages locally (store-and-forward).
  - When the phone has **internet**, **creates the note in OSM** (same flow as the gateway: validate, then POST to OSM Notes API).
- **Result:** Any phone with the app can act as a **mobile gateway** when no fixed gateway is in range. Reports are not lost just because there was no RPi nearby.

---

## Why it’s out of scope for this project

1. **Different platform:** This repo is a Python service for Linux (e.g. RPi). A mobile gateway is an app for Android (and possibly iOS), with different APIs (Bluetooth to Meshtastic, mobile UX, background/foreground limits).
2. **Different product:** This project is “the gateway service.” A mobile app is a separate product (even if it reuses the same protocol and dedup logic).
3. **No mobile code here:** The current codebase has no mobile app; adding one would be a new repository and delivery artifact (e.g. Play Store / F-Droid).

So the **improvement** is conceptual and product-level (“don’t lose reports; let phones help”), but the **implementation** belongs in another project (e.g. “OSM-Mesh-Notes-Mobile” or similar).

---

## Distributed creators and importance of global dedup

If both **fixed gateways** and **mobile apps** can create notes from the same public-channel messages:

- Many devices can receive the same message (gateways + several phones).
- Each can store it and later try to create an OSM note when online.
- **Without a global “already created?” check**, each would create a note → many duplicate notes in OSM.

So **check-before-create** (and register-after-create) becomes **essential**, not optional. The first device to get online and create the note “wins”; the others must see that it already exists and skip creation. That’s exactly what a **global dedup API** (e.g. in [OSM-Notes-API](https://github.com/OSM-Notes/OSM-Notes-API)) provides; see [DEDUP_API_EXTENSIONS.md](./DEDUP_API_EXTENSIONS.md).

Summary: the mobile-gateway idea **reinforces the need** for the dedup API; both are complementary and the dedup work is in scope of OSM-Notes-API / gateway logic, while the mobile app is the out-of-scope improvement described here.

---

## “Everyone keeps a copy”

A possible design is that **every listener** (gateways and phones) keeps a **local copy** of every `#osmnote` message it receives. So:

- No single point of failure: if one device never gets online, another might.
- Redundancy: the same report can be carried by several devices until one succeeds in creating the note.
- The **dedup API** ensures that only one note is created; the rest only need to check and then discard or mark as “already in OSM.”

This fits the current gateway’s store-and-forward model, extended to many independent nodes.

---

## What would be needed (for a future mobile project)

- **App** that connects to a Meshtastic device (e.g. over Bluetooth), subscribes to the public channel, and parses `#osmnote` (same format as gateway).
- **Local storage** for received messages (and optionally position cache if the app can derive or receive position).
- **When online:** same flow as gateway: normalize text, compute fingerprint (message + position cell), **call dedup API to check**; if not exists, create note via OSM Notes API, then **register** fingerprint in dedup API.
- **UX:** e.g. list of “pending notes,” retry, and optionally show “already created” when check returns exists.
- **Battery / background:** policy for when to listen (e.g. only when app in foreground, or “field mode”) to avoid draining the phone.

None of this is in the current repository; it would be a separate codebase and release.

---

## Summary

- **Improvement:** Mobile app(s) that receive public-channel `#osmnote` messages and create OSM notes when the phone has internet, so reports are not lost when no fixed gateway is in range.
- **Relationship to this project:** Same protocol and same need for global dedup; different product and platform, hence **out of scope** for this repo.
- **Dependency:** A global dedup API (e.g. in OSM-Notes-API) is important for the current multi-gateway case and **critical** once many mobile devices can also create notes.

This document is only a description of a possible future direction; it does not imply any commitment to implement it in this project.
