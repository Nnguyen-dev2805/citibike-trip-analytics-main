"""
Script tự động tạo toàn bộ datasets, charts và dashboard trên Apache Superset
thông qua REST API.
"""
import requests
import json
import sys

SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"

# Thay thế bằng requests.Session() để duy trì session auth
SESSION = requests.Session()

# ─────────────────────────────────────────────
# 1. Auth + CSRF token
# ─────────────────────────────────────────────
def login():
    # Bước 1: lấy JWT
    r = SESSION.post(f"{SUPERSET_URL}/api/v1/security/login", json={
        "username": USERNAME, "password": PASSWORD,
        "provider": "db", "refresh": True
    })
    r.raise_for_status()
    token = r.json()["access_token"]

    # Bước 2: lấy CSRF token (bắt buộc cho mọi POST/PUT/DELETE)
    csrf_r = SESSION.get(
        f"{SUPERSET_URL}/api/v1/security/csrf_token/",
        headers={"Authorization": f"Bearer {token}"}
    )
    csrf_r.raise_for_status()
    csrf_token = csrf_r.json()["result"]

    print("✅ Đăng nhập & lấy CSRF token thành công")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token,
        "Referer": SUPERSET_URL,
    }

# ─────────────────────────────────────────────
# 2. Lấy database ID
# ─────────────────────────────────────────────
def get_database_id(headers):
    r = requests.get(f"{SUPERSET_URL}/api/v1/database/", headers=headers)
    r.raise_for_status()
    for db in r.json()["result"]:
        if "citi" in db["database_name"].lower() or "lakehouse" in db["database_name"].lower() or "trino" in db["database_name"].lower():
            print(f"✅ Database tìm thấy: [{db['id']}] {db['database_name']}")
            return db["id"]
    # fallback: in ra tất cả để debug
    print("❌ Không tìm thấy database Citi Bike. Danh sách hiện có:")
    for db in r.json()["result"]:
        print(f"   [{db['id']}] {db['database_name']}")
    sys.exit(1)

# ─────────────────────────────────────────────
# 3. Tạo dataset (bỏ qua nếu đã tồn tại)
# ─────────────────────────────────────────────
def ensure_dataset(headers, db_id, table_name, schema="default"):
    # Tìm dataset theo tên trong tất cả dataset hiện có
    r = SESSION.get(f"{SUPERSET_URL}/api/v1/dataset/", headers=headers,
                    params={"q": json.dumps({
                        "page_size": 100
                    })})
    all_datasets = r.json().get("result", [])
    for ds in all_datasets:
        if ds.get("table_name") == table_name:
            ds_id = ds["id"]
            print(f"  ⚡ Dataset '{table_name}' đã tồn tại (id={ds_id}), dùng lại")
            return ds_id

    # Nếu chưa tồn tại thì tạo mới
    payload = {"database": db_id, "schema": schema, "table_name": table_name}
    r = SESSION.post(f"{SUPERSET_URL}/api/v1/dataset/", headers=headers, json=payload)
    if r.status_code in (200, 201):
        ds_id = r.json()["id"]
        print(f"  ✅ Dataset '{table_name}' tạo thành công (id={ds_id})")
        return ds_id
    else:
        print(f"  ⚠️  Dataset '{table_name}' lỗi {r.status_code}: {r.text[:200]}")
        return None

# ─────────────────────────────────────────────
# 4. Tạo chart
# ─────────────────────────────────────────────
def create_chart(headers, slice_name, viz_type, datasource_id, params):
    payload = {
        "slice_name": slice_name,
        "viz_type": viz_type,
        "datasource_id": datasource_id,
        "datasource_type": "table",
        "params": json.dumps(params),
    }
    r = SESSION.post(f"{SUPERSET_URL}/api/v1/chart/", headers=headers, json=payload)
    if r.status_code in (200, 201):
        chart_id = r.json()["id"]
        print(f"  ✅ Chart '{slice_name}' tạo thành công (id={chart_id})")
        return chart_id
    else:
        print(f"  ❌ Chart '{slice_name}' lỗi {r.status_code}: {r.text[:300]}")
        return None

# ─────────────────────────────────────────────
# 5. Tạo dashboard và gắn charts
# ─────────────────────────────────────────────
def create_dashboard(headers, title, chart_ids):
    # Tạo dashboard trống trước
    payload = {
        "dashboard_title": title,
        "published": True,
    }
    r = SESSION.post(f"{SUPERSET_URL}/api/v1/dashboard/", headers=headers, json=payload)
    if r.status_code not in (200, 201):
        print(f"❌ Dashboard lỗi {r.status_code}: {r.text[:300]}")
        return None

    dash_id = r.json()["id"]

    # Gắn các charts vào dashboard qua endpoint riêng
    put_payload = {"json_metadata": "{}", "slices": chart_ids}
    r2 = SESSION.put(
        f"{SUPERSET_URL}/api/v1/dashboard/{dash_id}",
        headers=headers,
        json=put_payload
    )
    if r2.status_code in (200, 201):
        print(f"\n✅ Dashboard '{title}' tạo thành công! → http://localhost:8088/superset/dashboard/{dash_id}/")
    else:
        # Charts đã được tạo riêng lẻ, user có thể kéo thả vào dashboard
        print(f"\n✅ Dashboard '{title}' tạo thành công (id={dash_id})!")
        print(f"   ⚠️  Gắn charts tự động lỗi nhỏ, bạn vào Superset kéo thả charts vào dashboard nhé.")
        print(f"   → http://localhost:8088/dashboard/{dash_id}/edit")
    return dash_id

# ─────────────────────────────────────────────
# 6. Dọn dẹp tài nguyên cũ
# ─────────────────────────────────────────────
def cleanup_existing_charts(headers):
    print("🧹 Đang kiểm tra và xóa các charts trùng tên cũ...")
    r = SESSION.get(f"{SUPERSET_URL}/api/v1/chart/", headers=headers, params={"q": json.dumps({"page_size": 200})})
    if r.status_code == 200:
        charts = r.json().get("result", [])
        target_names = [
            "📈 Số chuyến đi mỗi ngày (2024)",
            "📊 Member vs Casual theo ngày",
            "🔥 Heatmap nhu cầu: Giờ × Thứ",
            "🚉 Top 20 trạm xuất phát",
            "🏁 Top 20 trạm đích",
            "🥧 Tỷ lệ Member vs Casual",
            "📋 Hành vi Member vs Casual",
            "🚲 Tỷ lệ sử dụng theo loại xe",
            "🗺️ Top cặp trạm xuất phát – đích",
            "📈 Xu hướng chuyến đi theo tháng (MoM)",
            "📋 Báo cáo tổng hợp theo tháng (MoM)",
            "Số chuyến đi mỗi ngày (2024)",
            "Member vs Casual theo ngày",
            "Heatmap nhu cầu: Giờ × Thứ",
            "Top 20 trạm xuất phát",
            "Top 20 trạm đích",
            "Tỷ lệ Member vs Casual",
            "Hành vi Member vs Casual",
            "Tỷ lệ sử dụng theo loại xe",
            "Top cặp trạm xuất phát – đích",
            "Xu hướng chuyến đi theo tháng (MoM)",
            "Báo cáo tổng hợp theo tháng (MoM)"
        ]
        for c in charts:
            if c["slice_name"] in target_names:
                cid = c["id"]
                dr = SESSION.delete(f"{SUPERSET_URL}/api/v1/chart/{cid}", headers=headers)
                if dr.status_code == 200:
                    print(f"  ❌ Đã xóa chart cũ: {c['slice_name']} (id={cid})")

def cleanup_existing_dashboards(headers):
    print("🧹 Đang kiểm tra và xóa dashboard cũ...")
    r = SESSION.get(f"{SUPERSET_URL}/api/v1/dashboard/", headers=headers, params={"q": json.dumps({"page_size": 100})})
    if r.status_code == 200:
        dashboards = r.json().get("result", [])
        target_titles = [
            "🚴 NYC Citi Bike Lakehouse Analytics",
            "NYC Citi Bike Lakehouse Analytics"
        ]
        for d in dashboards:
            if d["dashboard_title"] in target_titles:
                did = d["id"]
                dr = SESSION.delete(f"{SUPERSET_URL}/api/v1/dashboard/{did}", headers=headers)
                if dr.status_code == 200:
                    print(f"  ❌ Đã xóa dashboard cũ: {d['dashboard_title']} (id={did})")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    headers = login()
    db_id = get_database_id(headers)
    SESSION.headers.update(headers)

    # Dọn dẹp tài nguyên cũ để tránh trùng lặp
    cleanup_existing_charts(headers)
    cleanup_existing_dashboards(headers)

    # Đăng ký / lấy dataset IDs động từ Superset
    dataset_names = [
        "gold_daily_rides",
        "gold_bike_type_usage",
        "gold_hourly_demand",
        "gold_station_od_pairs",
        "gold_top_end_stations",
        "gold_top_start_stations",
        "gold_user_type_behavior",
        "gold_monthly_summary"
    ]
    ds = {}
    print("📊 Đang đồng bộ hóa datasets trên Superset...")
    for t in dataset_names:
        ds_id = ensure_dataset(headers, db_id, t)
        if ds_id:
            ds[t] = ds_id
            
    print(f"✅ Đã nhận {len(ds)}/{len(dataset_names)} datasets hoạt động, tiến hành tạo charts...\n")

    print("🎨 Đang tạo các charts mới...")
    chart_ids = []

    # ── Chart 1: Số chuyến đi theo ngày ──────────────────────────────────
    if ds.get("gold_daily_rides"):
        cid = create_chart(headers,
            slice_name="Số chuyến đi mỗi ngày (2024)",
            viz_type="echarts_timeseries_line",
            datasource_id=ds["gold_daily_rides"],
            params={
                "x_axis": "ride_date",
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "total_rides"}, "aggregate": "SUM", "label": "Tổng chuyến đi"}],
                "groupby": [],
                "time_grain_sqla": "P1D",
                "x_axis_title": "Ngày",
                "y_axis_title": "Số chuyến đi",
                "rich_tooltip": True,
                "show_legend": True,
            }
        )
        if cid: chart_ids.append(cid)

    # ── Chart 2: Member vs Casual theo ngày (Stacked Bar) ─────────────────
    if ds.get("gold_daily_rides"):
        cid = create_chart(headers,
            slice_name="Member vs Casual theo ngày",
            viz_type="echarts_timeseries_bar",
            datasource_id=ds["gold_daily_rides"],
            params={
                "x_axis": "ride_date",
                "metrics": [
                    {"expressionType": "SIMPLE", "column": {"column_name": "member_rides"}, "aggregate": "SUM", "label": "Member"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "casual_rides"}, "aggregate": "SUM", "label": "Casual"},
                ],
                "groupby": [],
                "stack": True,
                "x_axis_title": "Ngày",
                "y_axis_title": "Số chuyến đi",
            }
        )
        if cid: chart_ids.append(cid)

    # ── Chart 3: Heatmap nhu cầu ─────────────────────────────────────────
    if ds.get("gold_hourly_demand"):
        cid = create_chart(headers,
            slice_name="Heatmap nhu cầu: Giờ × Thứ",
            viz_type="heatmap",
            datasource_id=ds["gold_hourly_demand"],
            params={
                "all_columns_x": "start_hour",
                "all_columns_y": "day_of_week",
                "metric": {"expressionType": "SIMPLE", "column": {"column_name": "total_rides"}, "aggregate": "SUM", "label": "Tổng chuyến"},
                "normalize_across": "heatmap",
                "left_margin": "auto",
                "bottom_margin": "auto",
                "legend_position": "right",
            }
        )
        if cid: chart_ids.append(cid)

    # ── Chart 4: Top 20 trạm xuất phát ───────────────────────────────────
    if ds.get("gold_top_start_stations"):
        cid = create_chart(headers,
            slice_name="Top 20 trạm xuất phát",
            viz_type="dist_bar",
            datasource_id=ds["gold_top_start_stations"],
            params={
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "total_starts"}, "aggregate": "SUM", "label": "Lượt xuất phát"}],
                "columns": [],
                "groupby": ["start_station_name"],
                "row_limit": 20,
                "order_desc": True,
                "horiz": True,
                "y_axis_label": "Lượt xuất phát",
                "x_axis_label": "Trạm",
            }
        )
        if cid: chart_ids.append(cid)

    # ── Chart 5: Top 20 trạm đích ─────────────────────────────────────────
    if ds.get("gold_top_end_stations"):
        cid = create_chart(headers,
            slice_name="Top 20 trạm đích",
            viz_type="dist_bar",
            datasource_id=ds["gold_top_end_stations"],
            params={
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "total_ends"}, "aggregate": "SUM", "label": "Lượt đến"}],
                "columns": [],
                "groupby": ["end_station_name"],
                "row_limit": 20,
                "order_desc": True,
                "horiz": True,
            }
        )
        if cid: chart_ids.append(cid)

    # ── Chart 6: Pie – Member vs Casual ──────────────────────────────────
    if ds.get("gold_user_type_behavior"):
        cid = create_chart(headers,
            slice_name="Tỷ lệ Member vs Casual",
            viz_type="pie",
            datasource_id=ds["gold_user_type_behavior"],
            params={
                "groupby": ["member_casual"],
                "metric": {"expressionType": "SIMPLE", "column": {"column_name": "total_rides"}, "aggregate": "SUM", "label": "Tổng chuyến"},
                "donut": True,
                "show_legend": True,
                "label_type": "key_percent",
                "show_labels_threshold": 5,
                "number_format": ",d",
            }
        )
        if cid: chart_ids.append(cid)

    # ── Chart 7: Bảng hành vi Member vs Casual ────────────────────────────
    if ds.get("gold_user_type_behavior"):
        cid = create_chart(headers,
            slice_name="Hành vi Member vs Casual",
            viz_type="table",
            datasource_id=ds["gold_user_type_behavior"],
            params={
                "groupby": ["member_casual"],
                "metrics": [
                    {"expressionType": "SIMPLE", "column": {"column_name": "total_rides"}, "aggregate": "SUM", "label": "Tổng chuyến đi"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "avg_duration_minutes"}, "aggregate": "AVG", "label": "Thời gian TB (phút)"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "avg_distance_km"}, "aggregate": "AVG", "label": "Khoảng cách TB (km)"},
                ],
                "table_timestamp_format": "smart_date",
                "include_search": False,
                "order_desc": True,
            }
        )
        if cid: chart_ids.append(cid)

    # ── Chart 8: Loại xe ─────────────────────────────────────────────────
    if ds.get("gold_bike_type_usage"):
        cid = create_chart(headers,
            slice_name="Tỷ lệ sử dụng theo loại xe",
            viz_type="dist_bar",
            datasource_id=ds["gold_bike_type_usage"],
            params={
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "total_rides"}, "aggregate": "SUM", "label": "Tổng chuyến"}],
                "columns": [],
                "groupby": ["rideable_type"],
                "row_limit": 10,
                "order_desc": True,
            }
        )
        if cid: chart_ids.append(cid)

    # ── Chart 9: Bảng cặp trạm OD ────────────────────────────────────────
    if ds.get("gold_station_od_pairs"):
        cid = create_chart(headers,
            slice_name="Top cặp trạm xuất phát – đích",
            viz_type="table",
            datasource_id=ds["gold_station_od_pairs"],
            params={
                "groupby": ["start_station_name", "end_station_name"],
                "metrics": [
                    {"expressionType": "SIMPLE", "column": {"column_name": "total_rides"}, "aggregate": "SUM", "label": "Tổng chuyến"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "avg_duration_minutes"}, "aggregate": "AVG", "label": "Thời gian TB (phút)"},
                ],
                "row_limit": 30,
                "order_desc": True,
            }
        )
        if cid: chart_ids.append(cid)

    # ── Chart 10: MoM Trend Line Chart (Xu hướng chuyến đi theo tháng) ───
    if ds.get("gold_monthly_summary"):
        cid = create_chart(headers,
            slice_name="Xu hướng chuyến đi theo tháng (MoM)",
            viz_type="dist_bar",
            datasource_id=ds["gold_monthly_summary"],
            params={
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "total_rides"}, "aggregate": "SUM", "label": "Tổng chuyến đi"}],
                "columns": [],
                "groupby": ["month"],
                "row_limit": 12,
                "order_desc": False,
                "x_axis_label": "Tháng",
                "y_axis_label": "Số chuyến đi"
            }
        )
        if cid: chart_ids.append(cid)

    # ── Chart 11: MoM Summary Table (Báo cáo tổng hợp theo tháng) ────────
    if ds.get("gold_monthly_summary"):
        cid = create_chart(headers,
            slice_name="Báo cáo tổng hợp theo tháng (MoM)",
            viz_type="table",
            datasource_id=ds["gold_monthly_summary"],
            params={
                "groupby": ["month"],
                "metrics": [
                    {"expressionType": "SIMPLE", "column": {"column_name": "total_rides"}, "aggregate": "SUM", "label": "Tổng chuyến"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "member_rides"}, "aggregate": "SUM", "label": "Member"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "casual_rides"}, "aggregate": "SUM", "label": "Casual"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "avg_duration_minutes"}, "aggregate": "AVG", "label": "Thời gian TB (phút)"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "avg_distance_km"}, "aggregate": "AVG", "label": "Khoảng cách TB (km)"},
                ],
                "table_timestamp_format": "smart_date",
                "include_search": False,
                "order_desc": False,
            }
        )
        if cid: chart_ids.append(cid)

    # ── Tạo Dashboard ─────────────────────────────────────────────────────
    print(f"\n📋 Đã tạo {len(chart_ids)} charts. Đang tạo dashboard...")
    if chart_ids:
        create_dashboard(headers, "NYC Citi Bike Lakehouse Analytics", chart_ids)

if __name__ == "__main__":
    main()
