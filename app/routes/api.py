from flask import Blueprint, jsonify, request, session, Response
from datetime import datetime, timedelta
from ..db import get_spar_db
import pytz
import csv
import io
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

api_bp = Blueprint("api", __name__)

IST = pytz.timezone("Asia/Kolkata")

def login_required_api(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def get_date_range():
    """Parse from/to query params (YYYY-MM-DD), default last 30 days."""
    now = datetime.now(IST)
    default_from = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    default_to = now.strftime("%Y-%m-%d")
    date_from = request.args.get("from", default_from)
    date_to   = request.args.get("to",   default_to)
    # Add one day to to_date to make it inclusive
    try:
        dt_to = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        date_to_exclusive = dt_to.strftime("%Y-%m-%d")
    except Exception:
        date_to_exclusive = date_to
    return date_from, date_to, date_to_exclusive

def str_date_filter(from_str, to_exclusive_str, field="date_time"):
    """Return a MongoDB filter for string-based date_time fields."""
    return {field: {"$gte": from_str, "$lt": to_exclusive_str}}


def get_hour_range():
    """Parse hour_from/hour_to query params (0-23), default 9 AM – 10 PM."""
    hour_from = max(0, min(23, int(request.args.get("hour_from", 9))))
    hour_to   = max(0, min(23, int(request.args.get("hour_to",  22))))
    return hour_from, hour_to


def hour_expr_str(hour_from, hour_to):
    """$expr hour filter for string date_time fields."""
    if hour_from == 0 and hour_to == 23:
        return {}
    return {"$expr": {"$and": [
        {"$gte": [{"$substr": ["$date_time", 11, 2]}, f"{hour_from:02d}"]},
        {"$lte": [{"$substr": ["$date_time", 11, 2]}, f"{hour_to:02d}"]},
    ]}}

def get_pin_filters():
    """Parse cross-chart pin filter params."""
    pin_date   = request.args.get("pin_date",   "").strip()
    pin_hour   = request.args.get("pin_hour",   "").strip()
    pin_gender = request.args.get("pin_gender", "").strip()
    pin_age    = request.args.get("pin_age",    "").strip()
    try:
        ph = int(pin_hour) if pin_hour != "" else None
    except (ValueError, TypeError):
        ph = None
    return (pin_date or None), ph, (pin_gender or None), (pin_age or None)

def gender_count_expr(pin_gender=None):
    """MongoDB $sum expression for visitor counts, optionally filtered to one gender."""
    def conv(f):
        return {"$convert": {"input": f"${f}", "to": "int", "onError": 0, "onNull": 0}}
    if pin_gender == "male":   return conv("count_male")
    if pin_gender == "female": return conv("count_female")
    if pin_gender == "child":  return conv("count_child")
    return {"$add": [conv("count_male"), conv("count_female"), conv("count_child")]}

def pin_date_filt(pin_date):
    """Build a one-day str_date_filter from a pin_date string."""
    next_d = (datetime.strptime(pin_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    return str_date_filter(pin_date, next_d)

def get_today_range():
    now = datetime.now(IST)
    today = now.strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    return today, tomorrow

def get_yesterday_range():
    now = datetime.now(IST)
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")
    return yesterday, today

def get_this_week_range():
    now = datetime.now(IST)
    week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    return week_start, tomorrow

def get_last_week_range():
    now = datetime.now(IST)
    week_start = now - timedelta(days=now.weekday())
    last_week_start = (week_start - timedelta(weeks=1)).strftime("%Y-%m-%d")
    last_week_end = week_start.strftime("%Y-%m-%d")
    return last_week_start, last_week_end

def get_this_month_range():
    now = datetime.now(IST)
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    return month_start, tomorrow

def get_last_month_range():
    now = datetime.now(IST)
    this_month_start = now.replace(day=1)
    last_month_end = this_month_start.strftime("%Y-%m-%d")
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1).strftime("%Y-%m-%d")
    return last_month_start, last_month_end

def footfall_sum(col, from_str, to_exclusive_str):
    """Aggregate visitor footfall totals from sparServer.footfall."""
    def conv(f): return {"$convert": {"input": f"${f}", "to": "int", "onError": 0, "onNull": 0}}
    pipeline = [
        {"$match": str_date_filter(from_str, to_exclusive_str)},
        {"$group": {"_id": None, "total": {"$sum": {"$add": [
            conv("count_male"), conv("count_female"), conv("count_child")
        ]}}}},
    ]
    res = list(col.aggregate(pipeline))
    return res[0]["total"] if res else 0

# ─────────────────────────────────────────────
#  OVERVIEW
# ─────────────────────────────────────────────
@api_bp.route("/overview")
@login_required_api
def overview():
    ff_col = get_spar_db().footfall

    date_from, date_to, date_to_ex = get_date_range()
    hour_from, hour_to = get_hour_range()

    # Period comparison — visitor counts (no hour filter on chips)
    periods = {}
    for label, (f, t) in [
        ("today",      get_today_range()),
        ("yesterday",  get_yesterday_range()),
        ("this_week",  get_this_week_range()),
        ("last_week",  get_last_week_range()),
        ("this_month", get_this_month_range()),
        ("last_month", get_last_month_range()),
    ]:
        periods[label] = footfall_sum(ff_col, f, t)

    pin_date, pin_hour, pin_gender, pin_age = get_pin_filters()

    # Effective date+hour filter (pin overrides range)
    bd_filt = pin_date_filt(pin_date) if pin_date else str_date_filter(date_from, date_to_ex)
    eff_h_from = pin_hour if pin_hour is not None else hour_from
    eff_h_to   = pin_hour if pin_hour is not None else hour_to
    bd_filt.update(hour_expr_str(eff_h_from, eff_h_to))

    if pin_age:
        # Gender breakdown from age_group collection for that age group
        age_docs = list(get_spar_db().age_group.aggregate([
            {"$match": {"age_group": pin_age, **bd_filt}},
            {"$group": {"_id": "$gender", "count": {"$sum": 1}}},
        ]))
        breakdown = {"male": 0, "female": 0, "child": 0, "staff": 0}
        for d in age_docs:
            if d["_id"] in breakdown:
                breakdown[d["_id"]] = d["count"]
    else:
        def conv(f): return {"$convert": {"input": f"${f}", "to": "int", "onError": 0, "onNull": 0}}
        ff = list(ff_col.aggregate([
            {"$match": bd_filt},
            {"$group": {
                "_id":    None,
                "male":   {"$sum": conv("count_male")},
                "female": {"$sum": conv("count_female")},
                "child":  {"$sum": conv("count_child")},
                "staff":  {"$sum": conv("count_staff")},
            }}
        ]))
        breakdown = ff[0] if ff else {"male": 0, "female": 0, "child": 0, "staff": 0}
        breakdown.pop("_id", None)
    total_visitors = breakdown.get("male", 0) + breakdown.get("female", 0) + breakdown.get("child", 0)

    return jsonify({
        "periods":        periods,
        "breakdown":      breakdown,
        "total_visitors": total_visitors,
        "date_from":      date_from,
        "date_to":        date_to,
    })

# ─────────────────────────────────────────────
#  DAILY FOOTFALL TREND
# ─────────────────────────────────────────────
@api_bp.route("/trend")
@login_required_api
def trend():
    col = get_spar_db().footfall
    date_from, date_to, date_to_ex = get_date_range()
    hour_from, hour_to = get_hour_range()

    pin_date, pin_hour, pin_gender, _ = get_pin_filters()
    vis_expr = gender_count_expr(pin_gender)
    stf_expr = {"$convert": {"input": "$count_staff", "to": "int", "onError": 0, "onNull": 0}}

    if pin_date:
        # Switch to hourly mode: show 24 hourly slots for that specific date
        filt = pin_date_filt(pin_date)
        if pin_hour is not None:
            filt.update(hour_expr_str(pin_hour, pin_hour))
        group_id = {"$substr": ["$date_time", 11, 2]}   # "HH"
        mode = "hourly"
    else:
        filt = str_date_filter(date_from, date_to_ex)
        h_from = pin_hour if pin_hour is not None else hour_from
        h_to   = pin_hour if pin_hour is not None else hour_to
        filt.update(hour_expr_str(h_from, h_to))
        group_id = {"$substr": ["$date_time", 0, 10]}   # "YYYY-MM-DD"
        mode = "daily"

    rows = list(col.aggregate([
        {"$match": filt},
        {"$group": {"_id": group_id, "visitors": {"$sum": vis_expr}, "staff": {"$sum": stf_expr}}},
        {"$sort": {"_id": 1}}
    ]))

    labels   = [r["_id"]      for r in rows]
    visitors = [r["visitors"] for r in rows]
    staff    = [r["staff"]    for r in rows]
    return jsonify({"labels": labels, "visitors": visitors, "staff": staff, "mode": mode})

# ─────────────────────────────────────────────
#  HOURLY FOOTFALL
# ─────────────────────────────────────────────
@api_bp.route("/hourly")
@login_required_api
def hourly():
    col = get_spar_db().footfall
    date_from, date_to, date_to_ex = get_date_range()
    pin_date, _ph, pin_gender, _ = get_pin_filters()
    vis_expr = gender_count_expr(pin_gender)
    hour_from, hour_to = get_hour_range()
    hour_map = {f"{h:02d}": 0 for h in range(hour_from, hour_to + 1)}

    if pin_date:
        # Actual counts for that specific date (not average)
        filt = {**pin_date_filt(pin_date), **hour_expr_str(hour_from, hour_to)}
        rows = list(col.aggregate([
            {"$match": filt},
            {"$group": {"_id": {"$substr": ["$date_time", 11, 2]}, "total": {"$sum": vis_expr}}},
            {"$sort": {"_id": 1}}
        ]))
        for r in rows:
            if r["_id"] in hour_map:
                hour_map[r["_id"]] = r["total"]
        is_avg = False
    else:
        # Average across date range
        rows = list(col.aggregate([
            {"$match": {**str_date_filter(date_from, date_to_ex), **hour_expr_str(hour_from, hour_to)}},
            {"$group": {
                "_id":   {"$substr": ["$date_time", 11, 2]},
                "total": {"$sum": vis_expr},
                "dates": {"$addToSet": {"$substr": ["$date_time", 0, 10]}},
            }},
            {"$sort": {"_id": 1}}
        ]))
        for r in rows:
            if r["_id"] in hour_map:
                n = len(r["dates"])
                hour_map[r["_id"]] = round(r["total"] / n) if n else 0
        is_avg = True

    labels = [f"{h:02d}:00" for h in range(hour_from, hour_to + 1)]
    values = [hour_map[f"{h:02d}"] for h in range(hour_from, hour_to + 1)]
    return jsonify({"labels": labels, "values": values,
                    "date_from": date_from, "date_to": date_to,
                    "pin_date": pin_date, "is_avg": is_avg})

# ─────────────────────────────────────────────
#  DEVICE STATUS (derived from last data received)
# ─────────────────────────────────────────────
@api_bp.route("/devices")
@login_required_api
def devices():
    db = get_spar_db()
    now = datetime.now(IST)

    results = []
    for col_name, label in [("footfall", "Footfall Camera"), ("heatmap", "Heatmap Camera")]:
        col = db[col_name]
        total = col.count_documents({})
        if total == 0:
            continue
        devices_in_col = col.distinct("device_serial_id")
        for dev_id in devices_in_col:
            last_doc = col.find_one({"device_serial_id": dev_id}, sort=[("date_time", -1)])
            if not last_doc:
                continue
            last_seen_str = last_doc.get("date_time","")
            camera = last_doc.get("camera_no","")
            store  = last_doc.get("store_code","")
            # Parse last seen
            try:
                last_seen_dt = datetime.strptime(last_seen_str[:19], "%Y-%m-%d %H:%M:%S")
                last_seen_dt = IST.localize(last_seen_dt)
                diff_minutes = (now - last_seen_dt).total_seconds() / 60
                if diff_minutes < 20:
                    status = "online"
                elif diff_minutes < 120:
                    status = "warning"
                else:
                    status = "offline"
                last_seen_friendly = last_seen_str[:16]
            except Exception:
                status = "offline"
                last_seen_friendly = last_seen_str[:16]
                diff_minutes = 9999

            results.append({
                "device_id": dev_id,
                "collection": col_name,
                "label": label,
                "camera": camera,
                "store": store,
                "last_seen": last_seen_friendly,
                "status": status,
                "minutes_ago": round(diff_minutes),
            })

    return jsonify({"devices": results})

# ─────────────────────────────────────────────
#  EXPORT FOOTFALL EXCEL
# ─────────────────────────────────────────────
@api_bp.route("/export-footfall")
@login_required_api
def export_footfall():
    col = get_spar_db().footfall
    date_from, date_to, date_to_ex = get_date_range()
    hour_from, hour_to = get_hour_range()

    docs = list(col.find(
        {**str_date_filter(date_from, date_to_ex), **hour_expr_str(hour_from, hour_to)}
    ).sort("date_time", -1).limit(5000))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Footfall"

    header_fill = PatternFill("solid", fgColor="DA291C")
    header_font = Font(bold=True, color="FFFFFF", size=11)

    headers = ["Date/Time", "Male", "Female", "Child", "Staff", "Total Visitors"]
    for ci, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=ci, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for ri, d in enumerate(docs, 2):
        m  = int(d.get("count_male",  0) or 0)
        f_ = int(d.get("count_female",0) or 0)
        c  = int(d.get("count_child", 0) or 0)
        s  = int(d.get("count_staff", 0) or 0)
        ws.cell(row=ri, column=1, value=d.get("date_time", ""))
        ws.cell(row=ri, column=2, value=m)
        ws.cell(row=ri, column=3, value=f_)
        ws.cell(row=ri, column=4, value=c)
        ws.cell(row=ri, column=5, value=s)
        ws.cell(row=ri, column=6, value=m + f_ + c)

    for i, col_dim in enumerate(ws.columns, 1):
        ws.column_dimensions[get_column_letter(i)].width = 18

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        buf.read(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment;filename=spar_footfall_{date_from}_{date_to}.xlsx"}
    )

# ─────────────────────────────────────────────
#  HEATMAP DATA
# ─────────────────────────────────────────────

# Camera → background image, location label, actual MongoDB camera_no value
# All cameras are in sparServer.heatmap
CAMERA_MAP = {
    "ChannelNo02": {"image": "channel_2",  "location": "location1",  "label": "Cosmetics (Ch 02)",         "cam_no": 2},
    "ChannelNo03": {"image": "channel_3",  "location": "location2",  "label": "Alcohol (Ch 03)",            "cam_no": 3},
    "ChannelNo05": {"image": "channel_5",  "location": "location3",  "label": "Alcohol & Perfumes (Ch 05)", "cam_no": 5},
    "ChannelNo06": {"image": "channel_6",  "location": "location4",  "label": "Alcohol (Ch 06)",            "cam_no": 6},
    "ChannelNo07": {"image": "channel_7",  "location": "location5",  "label": "Alcohol (Ch 07)",            "cam_no": 7},
    "ChannelNo15": {"image": "channel_15", "location": "location6",  "label": "Bags (Ch 15)",               "cam_no": 15},
    "ChannelNo16": {"image": "channel_16", "location": "location7",  "label": "Confectionaries (Ch 16)",    "cam_no": 16},
}

@api_bp.route("/heatmap-data")
@login_required_api
def heatmap_data():
    from collections import OrderedDict
    camera    = request.args.get("camera", "ChannelNo03")
    hour_from = int(request.args.get("hour_from", 0))
    hour_to   = int(request.args.get("hour_to",  23))

    if camera not in CAMERA_MAP:
        return jsonify({"error": "Unknown camera"}), 400

    col    = get_spar_db().heatmap
    cam_no = CAMERA_MAP[camera]["cam_no"]

    # Accept comma-separated dates or single date (backwards compat)
    dates_param = request.args.get("dates", "") or request.args.get("date", "")
    dates = [d.strip() for d in dates_param.split(",") if d.strip()]

    if not dates:
        latest = col.find_one({"camera_no": cam_no}, sort=[("date_time", -1)])
        dates = [latest["date_time"][:10]] if latest else ["2026-02-25"]

    # Build per-date hour-range conditions
    or_conditions = []
    for d in dates:
        tf = f"{d} {hour_from:02d}:00:00"
        tt_h = hour_to + 1
        if tt_h >= 24:
            next_d = (datetime.strptime(d, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            tt = f"{next_d} 00:00:00"
        else:
            tt = f"{d} {tt_h:02d}:00:00"
        or_conditions.append({"date_time": {"$gte": tf, "$lt": tt}})

    if len(or_conditions) == 1:
        filt = {"camera_no": cam_no, **or_conditions[0]}
    else:
        filt = {"camera_no": cam_no, "$or": or_conditions}

    docs = list(col.find(
        filt,
        {"date_time": 1, "count": 1, "person_bbox_list": 1, "_id": 0}
    ).sort("date_time", 1))

    # Group by HH:MM — merge bboxes & counts across all selected dates
    slots  = OrderedDict()   # keyed by HH:MM
    total  = {"male": 0, "female": 0, "child": 0, "staff": 0}
    multi  = len(dates) > 1

    for doc in docs:
        ts = doc["date_time"][11:16]   # HH:MM
        if ts not in slots:
            slots[ts] = {
                "datetime": ts if multi else doc["date_time"],
                "time":     ts,
                "count":    {"male": 0, "female": 0, "child": 0, "staff": 0},
                "bboxes":   {"male": [], "female": [], "child": [], "staff": []},
            }
        slot = slots[ts]

        cnt = doc.get("count") or {}
        if isinstance(cnt, str):
            import ast
            try: cnt = ast.literal_eval(cnt)
            except: cnt = {}

        bbl = doc.get("person_bbox_list") or {}
        if isinstance(bbl, str):
            import ast
            try: bbl = ast.literal_eval(bbl)
            except: bbl = {}

        for cat in ("male", "female", "child", "staff"):
            raw  = bbl.get(cat, []) or []
            slot["bboxes"][cat].extend([b for b in raw if isinstance(b, list) and len(b) == 4])
            c = int(cnt.get(cat, 0))
            slot["count"][cat] += c
            total[cat] += c

        # Keep full datetime label for single-date view
        if not multi:
            slot["datetime"] = doc["date_time"]

    cam_info = CAMERA_MAP[camera]
    return jsonify({
        "camera":    camera,
        "image":     cam_info["image"],
        "location":  cam_info["location"],
        "dates":     dates,
        "hour_from": hour_from,
        "hour_to":   hour_to,
        "frames":    list(slots.values()),
        "total":     total,
        "cameras":   [{"id": k, "label": v["label"]} for k, v in CAMERA_MAP.items()],
    })

@api_bp.route("/heatmap-dates")
@login_required_api
def heatmap_dates():
    """Return distinct dates available per camera."""
    camera = request.args.get("camera", "ChannelNo03")
    if camera not in CAMERA_MAP:
        return jsonify({"dates": []})
    col    = get_spar_db().heatmap
    cam_no = CAMERA_MAP[camera]["cam_no"]
    docs = list(col.find({"camera_no": cam_no}, {"date_time": 1, "_id": 0}))
    dates = sorted({d["date_time"][:10] for d in docs})
    return jsonify({"dates": dates})

# ─────────────────────────────────────────────
#  QUEUE & WAIT ANALYSIS (sparServer.queue_length)
# ─────────────────────────────────────────────
@api_bp.route("/queue-stats")
@login_required_api
def queue_stats():
    db = get_spar_db()
    date_from, date_to, date_to_ex = get_date_range()
    col = db.queue_length

    # date_time format: "YYYY-MM-DD_HH-MM-SS"
    # str_date_filter still works — lexicographic ordering is preserved
    filt = str_date_filter(date_from, date_to_ex)

    docs = list(col.find(filt, {
        "camera_no": 1, "date_time": 1,
        "avg_wait_time": 1, "person_detections": 1,
        "_id": 0
    }))

    # Per-camera accumulators
    cam_stats = {}
    for doc in docs:
        cam = doc.get("camera_no")
        if cam is None:
            continue
        if cam not in cam_stats:
            cam_stats[cam] = {
                "wait_times":   [],
                "queue_lengths":[],
                "hourly_wait":  {},   # int hour -> [values]
                "hourly_queue": {},
            }
        cs = cam_stats[cam]

        # Wait time already in minutes — average non-zero
        wait = doc.get("avg_wait_time")
        if wait and isinstance(wait, (int, float)) and wait > 0:
            cs["wait_times"].append(float(wait))

        # Queue length: flatten person_detections list-of-lists, avg non-zero
        pdet = doc.get("person_detections") or []
        flat = []
        for sublist in pdet:
            if isinstance(sublist, list):
                flat.extend(v for v in sublist if isinstance(v, (int, float)) and v > 0)
        ql = (sum(flat) / len(flat)) if flat else None
        if ql is not None:
            cs["queue_lengths"].append(ql)

        # Hourly bucket: date_time[11:13] = "HH" for "YYYY-MM-DD_HH-MM-SS"
        dt_str = doc.get("date_time", "")
        if len(dt_str) >= 13:
            try:
                h = int(dt_str[11:13])
                if wait and wait > 0:
                    cs["hourly_wait"].setdefault(h, []).append(float(wait))
                if ql is not None:
                    cs["hourly_queue"].setdefault(h, []).append(ql)
            except ValueError:
                pass

    # Build per-camera summary list
    cameras = []
    for cam_no in sorted(cam_stats.keys()):
        cs  = cam_stats[cam_no]
        wt  = cs["wait_times"]
        qlv = cs["queue_lengths"]
        cameras.append({
            "camera_no":    cam_no,
            "label":        f"Counter {cam_no}",
            "avg_wait_min": round(sum(wt)  / len(wt),  2) if wt  else 0,
            "avg_queue":    round(sum(qlv) / len(qlv), 1) if qlv else 0,
            "max_queue":    round(max(qlv), 1)             if qlv else 0,
            "observations": len(wt),
        })

    # Overall KPIs
    all_waits  = [w for cs in cam_stats.values() for w in cs["wait_times"]]
    all_queues = [q for cs in cam_stats.values() for q in cs["queue_lengths"]]
    overall_avg_wait  = round(sum(all_waits)  / len(all_waits),  2) if all_waits  else 0
    overall_avg_queue = round(sum(all_queues) / len(all_queues), 1) if all_queues else 0
    active_counters   = len([c for c in cameras if c["observations"] > 0])

    # Global hourly averages (all counters combined)
    g_hw, g_hq = {}, {}
    for cs in cam_stats.values():
        for h, vals in cs["hourly_wait"].items():
            g_hw.setdefault(h, []).extend(vals)
        for h, vals in cs["hourly_queue"].items():
            g_hq.setdefault(h, []).extend(vals)

    hourly_labels = [f"{h:02d}:00" for h in range(24)]
    hourly_wait_vals  = [
        round(sum(g_hw[h]) / len(g_hw[h]), 2) if g_hw.get(h) else None
        for h in range(24)
    ]
    hourly_queue_vals = [
        round(sum(g_hq[h]) / len(g_hq[h]), 1) if g_hq.get(h) else None
        for h in range(24)
    ]

    # Per-counter hourly breakdown (for multi-line charts)
    per_counter_hourly = []
    for cam_no in sorted(cam_stats.keys()):
        cs = cam_stats[cam_no]
        hw, hq = [], []
        for h in range(24):
            wvals = cs["hourly_wait"].get(h, [])
            qvals = cs["hourly_queue"].get(h, [])
            hw.append(round(sum(wvals) / len(wvals), 2) if wvals else None)
            hq.append(round(sum(qvals) / len(qvals), 1) if qvals else None)
        per_counter_hourly.append({
            "camera_no": cam_no,
            "label":     f"Counter {cam_no}",
            "wait":      hw,
            "queue":     hq,
        })

    return jsonify({
        "cameras":            cameras,
        "overall_avg_wait":   overall_avg_wait,
        "overall_avg_queue":  overall_avg_queue,
        "active_counters":    active_counters,
        "total_observations": len(docs),
        "date_from":          date_from,
        "date_to":            date_to,
        "hourly_labels":      hourly_labels,
        "hourly_wait":        hourly_wait_vals,
        "hourly_queue":       hourly_queue_vals,
        "per_counter_hourly": per_counter_hourly,
    })

# ─────────────────────────────────────────────
#  DWELL TIME (sparServer)
# ─────────────────────────────────────────────
@api_bp.route("/dwell")
@login_required_api
def dwell():
    """Aggregate dwell-time bucket counts from sparServer.dwell_time_summary."""
    db = get_spar_db()
    date_from, date_to, date_to_ex = get_date_range()
    hour_from, hour_to = get_hour_range()

    daily_pipeline = [
        {"$match": {**str_date_filter(date_from, date_to_ex), **hour_expr_str(hour_from, hour_to)}},
        {"$group": {
            "_id":   {"$substr": ["$date_time", 0, 10]},
            "lt2":   {"$sum": "$dwell_store_count_less_than_2_minutes"},
            "b2_10": {"$sum": "$dwell_store_count_between_2_to_10_minutes"},
            "gt10":  {"$sum": "$dwell_store_count_more_than_10_minutes"},
        }},
        {"$sort": {"_id": 1}}
    ]
    rows = list(db.dwell_time_summary.aggregate(daily_pipeline))

    labels = [r["_id"]    for r in rows]
    lt2    = [r["lt2"]    for r in rows]
    b2_10  = [r["b2_10"]  for r in rows]
    gt10   = [r["gt10"]   for r in rows]

    return jsonify({
        "labels":       labels,
        "lt2":          lt2,
        "b2_10":        b2_10,
        "gt10":         gt10,
        "total_lt2":    sum(lt2),
        "total_b2_10":  sum(b2_10),
        "total_gt10":   sum(gt10),
    })

# ─────────────────────────────────────────────
#  AGE GROUP (sparServer)
# ─────────────────────────────────────────────
@api_bp.route("/age-group")
@login_required_api
def age_group():
    """Aggregate age-group counts from sparServer.age_group."""
    db = get_spar_db()
    date_from, date_to, date_to_ex = get_date_range()
    hour_from, hour_to = get_hour_range()

    pin_date, pin_hour, pin_gender, _ = get_pin_filters()

    filt = pin_date_filt(pin_date) if pin_date else str_date_filter(date_from, date_to_ex)
    eff_h_from = pin_hour if pin_hour is not None else hour_from
    eff_h_to   = pin_hour if pin_hour is not None else hour_to
    filt.update(hour_expr_str(eff_h_from, eff_h_to))

    VALID_GROUPS = {"18-25", "25-35", "35-45", "45+"}
    filt["age_group"] = {"$in": list(VALID_GROUPS)}
    if pin_gender:
        filt["gender"] = pin_gender

    rows = list(db.age_group.aggregate([
        {"$match": filt},
        {"$group": {"_id": "$age_group", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))
    LABEL_MAP = {"18-25": "18–25", "25-35": "25–35", "35-45": "35–45", "45+": "45+"}
    buckets = [
        {"key": r["_id"], "label": LABEL_MAP[r["_id"]], "count": r["count"]}
        for r in rows if r["_id"] in VALID_GROUPS
    ]
    return jsonify({"buckets": buckets})
