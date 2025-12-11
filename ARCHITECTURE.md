# Auphere Backend Architecture

## 🎯 Current Role: API Gateway + Temporary Enrichment

### ✅ **Correct Responsibilities** (API Gateway)

- **Authentication**: Supabase integration
- **Routing**: Forward requests to microservices
- **CORS**: Cross-origin configuration
- **Rate Limiting**: Protect microservices
- **Request/Response transformation**: Normalize data formats

### ⚠️ **Temporary Responsibilities** (TO BE MIGRATED)

These responsibilities are currently in the backend but should be moved to appropriate microservices:

#### `/app/enrichment/` Module

**Current Location**: `auphere-backend`  
**Target Location**: `auphere-places` (Rust)  
**Migration Priority**: HIGH

Files:

- `feature_inference.py` → `auphere-places/src/services/enrichment/features.rs`
- `amenities_mapper.py` → `auphere-places/src/services/enrichment/amenities.rs`
- `google_places_popular_times.py` → `auphere-places/src/services/enrichment/popular_times.rs`

**Why it should move**: These are data enrichment operations specific to places, which is the domain of auphere-places.

#### `/app/enrichment/perplexity_search.py`

**Current Location**: `auphere-backend`  
**Decision Needed**: Should go to either:

- **Option A**: `auphere-places` - If used for data enrichment
- **Option B**: `auphere-agent` - If used for AI context

**Migration Priority**: MEDIUM

---

## 🏗️ Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TARGET STATE                             │
└─────────────────────────────────────────────────────────────┘

auphere-backend (Python/FastAPI) - API Gateway ONLY
    │
    ├─── auth.py          ✅ Supabase authentication
    ├─── places.py        ✅ Proxy to auphere-places
    ├─── plans.py         ✅ Proxy to auphere-agent
    ├─── chat.py          ✅ Proxy to auphere-agent
    │
    └─── ❌ NO enrichment logic
    └─── ❌ NO business logic
    └─── ❌ NO data transformations

auphere-places (Rust/Actix-Web) - Places Domain
    │
    ├─── CRUD operations
    ├─── Search & filtering
    ├─── Geospatial queries
    │
    └─── services/enrichment/  ← MOVE enrichment HERE
         ├─── features.rs
         ├─── amenities.rs
         ├─── popular_times.rs
         └─── web_enrichment.rs

auphere-agent (Python/FastAPI) - AI/Agent Domain
    │
    ├─── Intent classification
    ├─── Agent execution
    ├─── Memory management
    ├─── Tool orchestration
    │
    └─── tools/
         ├─── place_tool.py    ✅ Calls auphere-places
         ├─── plan_tool.py     ✅ Planning logic
         └─── ❌ NO direct API calls to Google/Perplexity
```

---

## 📋 Migration Checklist

### Phase 1: Organize (DONE ✅)

- [x] Create `/app/enrichment/` module
- [x] Move enrichment files
- [x] Add temporary warning comments
- [x] Document architecture

### Phase 2: Isolate (IN PROGRESS ⏳)

- [ ] Update imports in `places.py` router
- [ ] Create enrichment middleware (optional)
- [ ] Document API contracts

### Phase 3: Migrate to Rust (TODO 📅)

- [ ] Create `auphere-places/src/services/enrichment/mod.rs`
- [ ] Implement features.rs
- [ ] Implement amenities.rs
- [ ] Implement popular_times.rs
- [ ] Add Redis caching in Rust
- [ ] Add tests

### Phase 4: Cutover (TODO 📅)

- [ ] Deploy new auphere-places with enrichment
- [ ] Update auphere-backend to proxy-only
- [ ] Remove `/app/enrichment/` module
- [ ] Verify all tests pass
- [ ] Monitor performance

---

## 🚀 Running the Backend

### Development

```bash
cd auphere-backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Environment Variables

```env
# Supabase (Authentication)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_PUBLISHABLE_KEY=eyJ...
SUPABASE_API_KEY=eyJ...

# Microservices
PLACES_SERVICE_URL=http://localhost:8002
GPT_BACKEND_URL=http://localhost:8001

# Redis (for enrichment caching - temporary)
REDIS_HOST=localhost
REDIS_PORT=6379

# APIs (temporary - should be in auphere-places)
GOOGLE_PLACES_API_KEY=AIza...
PERPLEXITY_API_KEY=pplx-...
```

---

## 🔍 Current Issues

### ⚠️ Architectural Smells

1. **Backend has business logic** (enrichment)

   - Should be proxy-only
   - Violates single responsibility

2. **Enrichment logic is in Python**

   - Should be in Rust for performance
   - Duplicates functionality

3. **Multiple services call Google API**
   - auphere-backend calls it
   - auphere-places calls it
   - Should be centralized in auphere-places

### ✅ What's Good

1. **Clear module separation** (`/app/enrichment/`)
2. **Well-documented temporary state**
3. **Existing functionality maintained**
4. **Clear migration path**

---

## 📚 Related Documentation

- `/docs/ARCHITECTURE_DIAGRAMS.md` - Visual architecture
- `/docs/IMPLEMENTATION_PLAN.md` - Full implementation plan
- `auphere-places/README.md` - Places service docs
- `auphere-agent/README.md` - Agent service docs

---

**Last Updated**: Dec 10, 2024  
**Status**: Refactoring in Progress - Pragmatic Approach  
**Next Review**: After enrichment migration to Rust
