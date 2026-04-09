# Data Segregation Audit Report
**Date**: 2026-04-06
**Project**: SPAR Store Monitor Dashboard
**Scope**: Multi-store data isolation across all dashboards and API endpoints

---

## Executive Summary

**CRITICAL ISSUE FOUND**: The `/api/dwell` endpoint is missing store code filtering, allowing data from one store to leak into another.

**Risk Level**: 🔴 **HIGH**
- Store footfall/visitor analytics can be mixed across locations
- Users can see dwell time data for stores they shouldn't have access to
- Potential compliance violation if sensitive store performance data is exposed

---

## Issues Found

### 1. ❌ CRITICAL: Missing Store Code Filter in `/api/dwell`

**File**: `app/routes/api.py` (lines 829-862)
**Severity**: 🔴 CRITICAL

**Current Code** (VULNERABLE):
```python
@api_bp.route("/dwell")
@login_required_api
def dwell():
    """Aggregate dwell-time bucket counts from sparServer.dwell_time_summary."""
    db = get_spar_db()
    date_from, date_to, date_to_ex = get_date_range()
    hour_from, hour_to = get_hour_range()

    daily_pipeline = [
        {"$match": {**str_date_filter(date_from, date_to_ex), **hour_expr_str(hour_from, hour_to)}},
        # ⚠️ NO STORE CODE FILTER - DATA NOT SEGREGATED!
        {"$group": {...}},
        {"$sort": {"_id": 1}}
    ]
```

**Problem**:
- No `store_code` filter in the `$match` stage
- Query aggregates dwell time data for ALL stores
- User selecting "Spar-20016" still receives data from "Spar-30008"

**Impact**:
- Store visitor behavior patterns leaked between stores
- Performance metrics mixed across locations
- Violates data isolation requirement

---

### 2. ⚠️ STRUCTURAL: Collection Missing Store Code Field

**Collection**: `sparServer.dwell_time_summary`
**Severity**: 🟡 MEDIUM

**Current Collection Schema**:
```json
{
  "date_time": "2026-04-05",
  "dwell_store_count_less_than_2_minutes": 45,
  "dwell_store_count_between_2_to_10_minutes": 120,
  "dwell_store_count_more_than_10_minutes": 80
}
```

**Missing Field**: `store_code` (should be present on all documents)

**Why This Matters**:
- Other collections (`footfall`, `heatmap`, `queue_length`, `age_group`) all have `store_code`
- Without `store_code` in the collection, queries cannot filter by store
- Indicates data ingestion may not be segregating stores properly

**Recommended Action**:
1. Add `store_code` field to all `dwell_time_summary` documents
2. Create index on `(store_code, date_time)` for performance
3. Update ingestion pipeline to populate `store_code`

---

### 3. ⚠️ AUTHORIZATION: No Role-Based Access Control

**Files**: `app/routes/auth.py`, `app/routes/api.py`
**Severity**: 🟡 MEDIUM

**Current Authorization Pattern**:
```python
def login_required_api(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated
```

**Problem**:
- Only checks if user is authenticated
- Does NOT verify if user has permission to access requested store
- Any authenticated user can access any store by changing `store_code` parameter

**Scenario**:
```
User A (for store A) could call:
GET /api/overview?store_code=Spar-30008-Langval-mall-Thanjavur

And receive data for store B, even though they shouldn't have access.
```

**Recommended Action**:
- Implement per-user store assignment in `dashboard_users` collection
- Add `allowed_stores` field: `["Spar-20016-TSM-Mall-Udupi"]`
- Validate `store_code` against user's `allowed_stores` before processing

---

### 4. ⚠️ FRONTEND: Store Codes Hardcoded

**File**: `app/templates/base.html` (lines 286-348)
**Severity**: 🟡 LOW-MEDIUM

**Current Code**:
```javascript
const STORE_CODES = [
  'Spar-20016-TSM-Mall-Udupi',
  'Spar-30008-Langval-mall-Thanjavur'
];
window.currentStoreCode = localStorage.getItem(STORE_CODE_KEY) || STORE_CODES[0];
```

**Problem**:
- Store codes hardcoded in frontend
- No validation - user could manually set localStorage to any value
- Combined with missing authorization, allows access to unauthorized stores

**Recommended Action**:
- Fetch allowed stores from backend (`GET /api/my-stores`)
- Validate store code on backend for every request
- Reject requests for stores user doesn't have access to

---

## Comprehensive Store Code Filtering Audit

### ✅ COMPLIANT Endpoints (10/11)

| Endpoint | Filter Applied | Status |
|----------|-----------------|--------|
| `/api/overview` | Yes | ✅ SECURE |
| `/api/trend` | Yes | ✅ SECURE |
| `/api/hourly` | Yes | ✅ SECURE |
| `/api/devices` | Yes | ✅ SECURE |
| `/api/export-footfall` | Yes | ✅ SECURE |
| `/api/heatmap-data` | Yes | ✅ SECURE |
| `/api/heatmap-table` | Yes | ✅ SECURE |
| `/api/heatmap-dates` | Yes | ✅ SECURE |
| `/api/queue-stats` | Yes | ✅ SECURE |
| `/api/age-group` | Yes | ✅ SECURE |
| **`/api/dwell`** | **No** | **❌ VULNERABLE** |

### Pattern: How Other Endpoints Filter Correctly

**Example from `/api/overview` (line 160)**:
```python
@api_bp.route("/overview")
@login_required_api
def overview():
    db = get_spar_db()
    store_code = get_store_code()  # ✅ Get store code
    date_from, date_to, date_to_ex = get_date_range()
    hour_from, hour_to = get_hour_range()

    # ✅ Apply store_code filter
    match_filter = {
        **str_date_filter(date_from, date_to_ex),
        "store_code": store_code  # CRITICAL LINE
    }

    pipeline = [
        {"$match": match_filter},
        # ... rest of query
    ]
```

---

## Recommended Fixes (Priority Order)

### Priority 1: IMMEDIATE - Fix `/api/dwell` Endpoint
**Impact**: Prevents data leakage
**Complexity**: Low (1-line fix)
**Time**: < 5 minutes

```python
# BEFORE (VULNERABLE):
daily_pipeline = [
    {"$match": {**str_date_filter(date_from, date_to_ex), **hour_expr_str(hour_from, hour_to)}},

# AFTER (SECURE):
store_code = get_store_code()
daily_pipeline = [
    {"$match": {
        **str_date_filter(date_from, date_to_ex),
        **hour_expr_str(hour_from, hour_to),
        "store_code": store_code  # ADD THIS LINE
    }},
```

### Priority 2: HIGH - Update MongoDB Collection Schema
**Impact**: Ensures data is stored with store codes
**Complexity**: Medium (requires migration)
**Time**: Depends on data volume

```javascript
// Add store_code field to dwell_time_summary collection
db.dwell_time_summary.updateMany(
  { store_code: { $exists: false } },
  [{ $set: { store_code: "$store_id_from_ingestion" } }]
);

// Create index for performance
db.dwell_time_summary.createIndex({
  store_code: 1,
  date_time: 1
});
```

### Priority 3: MEDIUM - Implement Role-Based Access Control
**Impact**: Prevents unauthorized access to stores
**Complexity**: High (requires auth system changes)
**Time**: 2-3 hours

1. Update `dashboard_users` schema:
```javascript
{
  username: "user1",
  password: "bcrypt_hash",
  allowed_stores: ["Spar-20016-TSM-Mall-Udupi"],
  role: "manager" // future: admin, viewer, analyst
}
```

2. Update `get_store_code()` to validate:
```python
def get_store_code():
    store_code = request.args.get("store_code", "").strip()
    user = session.get("user")

    # Validate user has access to this store
    db = get_spar_db()
    user_doc = db.dashboard_users.find_one({"username": user})

    if store_code not in user_doc.get("allowed_stores", []):
        return None  # Trigger 403 Forbidden

    return store_code
```

3. Update all API endpoints to handle `None` response:
```python
store_code = get_store_code()
if not store_code:
    return jsonify({"error": "Forbidden: No access to this store"}), 403
```

### Priority 4: LOW - Secure Frontend Store List
**Impact**: Prevents unauthorized store selection
**Complexity**: Low
**Time**: 30 minutes

```javascript
// Fetch allowed stores from backend on login
fetch('/api/my-stores')
  .then(r => r.json())
  .then(data => {
    window.STORE_CODES = data.stores; // Dynamic list
    // Validate currentStoreCode is in allowed list
    if (!window.STORE_CODES.includes(window.currentStoreCode)) {
      window.currentStoreCode = window.STORE_CODES[0];
    }
  });
```

---

## Data Segregation Matrix

| Component | Data Segregation | Risk | Fix |
|-----------|------------------|------|-----|
| **API: `/api/overview`** | ✅ Store code filtered | Low | None |
| **API: `/api/trend`** | ✅ Store code filtered | Low | None |
| **API: `/api/hourly`** | ✅ Store code filtered | Low | None |
| **API: `/api/devices`** | ✅ Store code filtered | Low | None |
| **API: `/api/export-footfall`** | ✅ Store code filtered | Low | None |
| **API: `/api/heatmap-data`** | ✅ Store code filtered | Low | None |
| **API: `/api/heatmap-table`** | ✅ Store code filtered | Low | None |
| **API: `/api/heatmap-dates`** | ✅ Store code filtered | Low | None |
| **API: `/api/queue-stats`** | ✅ Store code filtered | Low | None |
| **API: `/api/age-group`** | ✅ Store code filtered | Low | None |
| **API: `/api/dwell`** | ❌ **NO FILTER** | **CRITICAL** | **Add filter** |
| **DB: `footfall`** | ✅ Has store_code | Low | None |
| **DB: `heatmap`** | ✅ Has store_code | Low | None |
| **DB: `queue_length`** | ✅ Has store_code | Low | None |
| **DB: `age_group`** | ✅ Has store_code | Low | None |
| **DB: `dwell_time_summary`** | ⚠️ **UNKNOWN** | Medium | **Verify & add** |
| **Auth: Role-based access** | ❌ **MISSING** | Medium | **Implement** |
| **Frontend: Store list** | ⚠️ Hardcoded | Low-Medium | **Fetch from backend** |

---

## Testing Checklist

After implementing fixes, verify:

- [ ] `/api/dwell` returns only data for selected store
- [ ] `/api/dwell` with `store_code=Spar-20016` returns different data than `Spar-30008`
- [ ] User A cannot access dwell data for User B's store
- [ ] All dates include `store_code` field
- [ ] Admin can see audit log of store accesses (future)
- [ ] Frontend store dropdown only shows authorized stores
- [ ] Attempting unauthorized store access returns 403 Forbidden

---

## SQL/MongoDB Migration Scripts (When Needed)

```javascript
// Verify dwell_time_summary collection structure
db.dwell_time_summary.findOne();

// Add store_code to all documents (example - adjust per actual data):
db.dwell_time_summary.updateMany(
  {},
  [{ $set: { store_code: "Spar-20016-TSM-Mall-Udupi" } }]
);

// Verify index exists
db.dwell_time_summary.getIndexes();

// Create if missing
db.dwell_time_summary.createIndex({ store_code: 1, date_time: 1 });
```

---

## Compliance Notes

- **GDPR**: Store-specific data must not leak between stores
- **Data Privacy**: User access must be restricted to assigned stores
- **Audit Trail**: All store access should be logged (currently missing)

---

**Report Generated**: 2026-04-06
**Next Review Date**: After implementing all fixes
