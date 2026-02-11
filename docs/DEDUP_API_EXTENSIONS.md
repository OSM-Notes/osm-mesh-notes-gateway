# Possible Extensions: Global Deduplication API in OSM-Notes-API

This document describes a possible extension to [OSM-Notes-API](https://github.com/OSM-Notes/OSM-Notes-API) to support **global deduplication** of notes created by multiple LoRa/Meshtastic gateways, plus derived ideas that could be interesting for the ecosystem.

**Context:** When several gateways run the same mesh (or a moving node reaches different gateways over time), the same `#osmnote` message can be received by more than one gateway. Each gateway would create a note in OpenStreetMap, resulting in duplicate notes. Local deduplication (per-gateway SQLite) does not help because gateways do not share state.

---

## 1. Base feature: Check-before-create (content + position hash)

### 1.1 Idea

- **Content + position fingerprint:** `hash = H(normalized_text || cell_id)`  
  - Normalization: trim, collapse whitespace, same rules as gateway.  
  - Position: discretized to a **cell** (e.g. H3 index at a fixed resolution, or a custom grid) so that small GPS differences do not create different keys.  
- **Service:** A small, dedicated API (or a new module in OSM-Notes-API) that maintains a store: `fingerprint → { osm_note_id?, created_at }`.  
- **Flow:**  
  1. Gateway computes `fingerprint` from the message and the node’s position (mapped to cell).  
  2. **Check:** `GET /api/v1/dedup/check?fingerprint=<hex>` → `{ exists: boolean, osm_note_id?: number, osm_note_url?: string }`.  
  3. If `exists === false`, gateway creates the note via the official OSM Notes API, then **Register:** `POST /api/v1/dedup/register` with `{ fingerprint, osm_note_id }`.  
  4. If `exists === true`, gateway skips creation and can optionally inform the user (e.g. “duplicate, see existing note”).

### 1.2 Where it could live

- **Option A:** New microservice (e.g. “OSM-Notes-Dedup”) used only by gateways.  
- **Option B:** New routes and storage inside **OSM-Notes-API** (shared deployment, same auth/rate-limiting/monitoring).

Implementing this in OSM-Notes-API would centralize “notes-related” logic and reuse existing infra (PostgreSQL/Redis, docs, deployment).

### 1.3 Design choices to fix early

- **Cell scheme:** H3 (e.g. res 8 or 9), S2, or simple lat/lon rounding. Same algorithm must be used by all gateways and the API.  
- **Hash function:** e.g. SHA-256 (or truncated). No need to be reversible.  
- **Idempotent register:** If two gateways race, both might get `exists: false`. First `POST /register` wins; second can return “already registered” and gateway treats as duplicate.  
- **TTL / retention:** Whether to expire old fingerprints (e.g. after N days or when the OSM note is closed) to limit storage and avoid cross-year collisions.

---

## 2. Extensions and derived ideas

### 2.1 “Exists in area” (neighbour cells)

- **Problem:** Same report at the boundary of two cells gets two different fingerprints; both gateways might create a note.  
- **Idea:** Endpoint `GET /api/v1/dedup/check-near?fingerprint_content=<hex>&cell=<h3_or_id>` that checks the given cell and optionally a small set of neighbour cells (e.g. H3 k-ring).  
- **Use case:** Gateways send content hash + cell; API checks that cell and neighbours. Reduces duplicates at edges.  
- **Trade-off:** Slightly more storage/query complexity; need to store `(content_hash, cell_id) → osm_note_id` and query by content hash + cell set.

### 2.2 Source attribution (mesh / gateway)

- **Idea:** In the register request, gateways send optional metadata: `gateway_id`, `channel` (e.g. LongFast), `mesh_name` or network id.  
- **Storage:** Store `fingerprint → { osm_note_id, source: "meshtastic", gateway_id?, mesh?, registered_at }`.  
- **Use case:**  
  - Analytics: “how many notes come from LoRa mesh vs other sources”.  
  - Future “notes from the field” layer or dashboard.  
  - Debugging and abuse detection (e.g. one gateway misbehaving).

### 2.3 Read-only “get by fingerprint”

- **Idea:** `GET /api/v1/dedup/note?fingerprint=<hex>` → `{ exists, osm_note_id, osm_note_url }` (no side effects).  
- **Use case:**  
  - Gateway or third-party app checks if a note for this content+position already exists before showing “create note” UI.  
  - Bots or tools that want to avoid suggesting a note that would be a duplicate.

### 2.4 Batch check

- **Idea:** `POST /api/v1/dedup/check-batch` with `{ fingerprints: string[] }` → `{ results: { fingerprint, exists, osm_note_id? }[] }`.  
- **Use case:** Gateway with many pending messages (e.g. after being offline) can resolve many at once with one HTTP call, reducing latency and rate-limit pressure.

### 2.5 Link to existing notes in OSM-Notes-API

- **Idea:** OSM-Notes-API already exposes notes (e.g. by id, search). If the dedup store is inside the same API or shares the same DB, one could:  
  - Add an optional `fingerprint` (or `content_hash`, `cell_id`) to the note representation where available.  
  - Or add a search filter “notes that were deduplicated” / “notes with source = meshtastic” (if 2.2 is implemented).  
- **Use case:** Analytics, “notes from the field” views, and consistency between “dedup registry” and “note metadata”.

### 2.6 Retention and cleanup

- **Idea:**  
  - TTL: delete or archive fingerprint records older than X days.  
  - Or: when the corresponding OSM note is closed/resolved, remove or mark the fingerprint as inactive so the same content+position could be re-reported later if needed.  
- **Implementation:** Could be a periodic job in OSM-Notes-API (or in Ingestion/Analytics if they already handle note lifecycle).  
- **Use case:** Bounded storage; avoid treating very old notes as duplicates forever.

### 2.7 Rate limiting and abuse

- **Idea:** Apply rate limits to dedup endpoints (e.g. per IP or per `gateway_id` if present).  
- **Abuse:** If someone discovers the check/register API, they could poll or register junk. Mitigations: require a simple shared secret or API key for register; keep check public or more permissive; log and alert on unusual patterns.  
- Fits naturally if implemented inside OSM-Notes-API, which already has rate limiting and security practices.

### 2.8 Optional: “suggest note” for clients

- **Idea:** A public or semi-public endpoint that accepts `{ text, lat, lon }` (or cell), computes the fingerprint, and returns “a note with this content already exists here: url” or “no existing note”.  
- **Use case:** Mobile or web apps (not only gateways) that want to suggest creating a note but avoid duplicates.  
- **Privacy:** Only stores/content hashes and cell IDs, not raw text; optional and can be rate-limited strictly.

---

## 3. Summary table

| Extension              | Purpose                         | Depends on base |
|------------------------|----------------------------------|-----------------|
| Check-before-create    | Avoid duplicate notes (multi-gateway) | —               |
| Exists in area         | Fewer duplicates at cell edges   | Base (content hash + cells) |
| Source attribution     | Analytics, “from mesh” views     | Base + optional metadata |
| Get by fingerprint     | Read-only lookup                | Base            |
| Batch check            | Efficiency for gateways         | Base            |
| Link to notes in API   | Consistency, search, analytics  | Base + same API/DB |
| Retention / cleanup    | Bounded storage, lifecycle       | Base            |
| Rate limiting / abuse  | Security                        | Base            |
| “Suggest note” for clients | Non-gateway apps            | Base (optional) |

---

## 4. Suggested implementation order

1. **Base:** Check + register (with idempotent register and fixed cell scheme).  
2. **Get by fingerprint** (reuse same store).  
3. **Optional metadata** (gateway_id, source) on register for future analytics.  
4. **Retention policy** and cleanup job.  
5. Then, if needed: “exists in area”, batch check, and “suggest note” endpoint.

This document can be used as a design reference for an ADR or an issue/PR in [OSM-Notes-API](https://github.com/OSM-Notes/OSM-Notes-API) when implementing the deduplication feature.
