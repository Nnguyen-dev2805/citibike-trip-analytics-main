# Thiết Kế Dashboard Cho Citi Bike Lakehouse Analytics

Tài liệu này mô tả cách thiết kế dashboard cho đồ án **Docker-Based Data Lakehouse Cho Phân Tích NYC Citi Bike**. Mục tiêu là tạo một dashboard vừa thể hiện được kết quả phân tích, vừa chứng minh được thiết kế Big Data từ Raw/Bronze/Silver/Gold đến Serving layer.

## 1. Ý Tưởng Chính Của Dashboard

Dashboard nên được thiết kế theo 3 cấp phân tích:

```text
Toàn bộ dữ liệu
  -> Chi tiết theo tháng
  -> So sánh giữa các tháng
```

Cách thiết kế này phù hợp vì:

1. Dữ liệu Citi Bike được công bố theo từng tháng.
2. Pipeline cũng ingest dữ liệu theo tháng.
3. Silver table được partition theo `month`.
4. Gold table có thể tổng hợp dữ liệu theo ngày, giờ, trạm, loại người dùng và loại xe.
5. Dashboard theo tháng có ý nghĩa thực tế cho vận hành, ví dụ đánh giá nhu cầu, điều phối xe và so sánh xu hướng giữa các tháng.

Câu chốt khi báo cáo:

> Dashboard được thiết kế theo 3 cấp: overview toàn bộ dữ liệu, drill-down theo tháng và so sánh giữa các tháng. Cách thiết kế này thống nhất với nguồn dữ liệu, pipeline xử lý và nhu cầu phân tích thực tế.

## 2. Bố Cục Tổng Thể

Tên dashboard đề xuất:

```text
Citi Bike Monthly Lakehouse Analytics
```

Hoặc tiếng Việt:

```text
Phân Tích Nhu Cầu Sử Dụng Citi Bike Theo Tháng
```

Bố cục nên làm như sau:

```text
[Title: Citi Bike Monthly Lakehouse Analytics]

[Global Filters]
Month | User Type | Bike Type | Station

[Section 1: Overall KPIs]
Total rides | Total months | Avg rides/month | Avg duration | Avg distance

[Section 2: Month-over-Month Trend]
Total rides by month
Member vs Casual by month
Avg duration/distance by month

[Section 3: Selected Month Detail]
Daily rides in selected month
Hourly demand by day/hour

[Section 4: Station & Route Analysis]
Top start stations
Top end stations
Top OD pairs table

[Section 5: User & Bike Behavior]
Member vs Casual behavior
Bike type usage
```

## 3. Global Filters

Nên đặt filter ở đầu dashboard:


| Filter               | Ý nghĩa                                           |
| -------------------- | ------------------------------------------------- |
| `month`              | Chọn tháng cần phân tích chi tiết                 |
| `member_casual`      | Lọc theo nhóm người dùng member/casual            |
| `rideable_type`      | Lọc theo loại xe                                  |
| `start_station_name` | Lọc theo trạm bắt đầu, nếu muốn phân tích sâu hơn |


Lưu ý:

- `month` là filter quan trọng nhất.
- Không nên thêm quá nhiều filter để tránh dashboard khó demo.
- Nếu làm trong Superset, có thể dùng native filter và map filter đến các chart liên quan.

## 4. Section 1: Overall KPIs

Phần đầu dashboard cho cái nhìn tổng quan về toàn bộ dữ liệu đã ingest vào Lakehouse.

### KPI nên có


| KPI                 | Ý nghĩa                                               | Nguồn dữ liệu gợi ý                                   |
| ------------------- | ----------------------------------------------------- | ----------------------------------------------------- |
| Total rides         | Tổng số chuyến trong toàn bộ dữ liệu hoặc theo filter | `gold_daily_rides` hoặc `gold_monthly_summary`        |
| Total months        | Số tháng đã có dữ liệu                                | `gold_monthly_summary`                                |
| Avg rides/month     | Trung bình số chuyến mỗi tháng                        | `gold_monthly_summary`                                |
| Avg duration        | Thời lượng chuyến đi trung bình                       | `gold_monthly_summary`                                |
| Avg distance        | Quãng đường trung bình                                | `gold_monthly_summary`                                |
| Member/Casual ratio | Tỷ lệ người dùng member và casual                     | `gold_monthly_summary` hoặc `gold_user_type_behavior` |


### Cách báo cáo

> Phần KPI đầu tiên cho biết quy mô dữ liệu sau khi pipeline chạy xong. Các chỉ số này không đọc trực tiếp từ raw data, mà lấy từ lớp Gold đã được Spark tổng hợp sẵn.

## 5. Section 2: Month-over-Month Trend

Phần này dùng để so sánh giữa các tháng.

### Chart đề xuất


| Chart                     | Loại biểu đồ      | Nguồn dữ liệu          | Ý nghĩa                                 |
| ------------------------- | ----------------- | ---------------------- | --------------------------------------- |
| Total rides by month      | Line chart        | `gold_monthly_summary` | Xu hướng số chuyến theo tháng           |
| Member vs Casual by month | Grouped bar chart | `gold_monthly_summary` | So sánh nhóm người dùng qua các tháng   |
| Avg duration by month     | Line chart        | `gold_monthly_summary` | Thời lượng trung bình thay đổi thế nào  |
| Avg distance by month     | Line chart        | `gold_monthly_summary` | Quãng đường trung bình thay đổi thế nào |


### Cách báo cáo

> Phần month-over-month giúp đánh giá xu hướng tăng giảm nhu cầu sử dụng xe, thay đổi hành vi người dùng và sự thay đổi về thời lượng/quãng đường trung bình giữa các tháng. Đây là dạng báo cáo có ý nghĩa thực tế vì đơn vị vận hành thường đánh giá hệ thống theo chu kỳ tháng.

## 6. Section 3: Selected Month Detail

Phần này phân tích chi tiết một tháng được chọn.

### Chart đề xuất


| Chart                         | Loại biểu đồ           | Nguồn dữ liệu        | Ý nghĩa                                      |
| ----------------------------- | ---------------------- | -------------------- | -------------------------------------------- |
| Daily rides in selected month | Line chart             | `gold_daily_rides`   | Xem ngày nào trong tháng có nhu cầu cao/thấp |
| Hourly demand                 | Heatmap hoặc bar chart | `gold_hourly_demand` | Xem giờ cao điểm và ngày trong tuần          |


Nếu Superset khó làm heatmap, có thể dùng bar chart theo `start_hour`.

### Cách báo cáo

> Sau phần tổng quan, dashboard cho phép chọn từng tháng để phân tích chi tiết. Daily rides cho biết biến động theo ngày, còn hourly demand giúp nhận diện khung giờ cao điểm. Các cột như `start_hour`, `day_of_week` và `month` được tạo ở tầng Silver, sau đó tổng hợp ở tầng Gold.

## 7. Section 4: Station & Route Analysis

Phần này phân tích địa điểm và tuyến di chuyển.

### Chart đề xuất


| Chart              | Loại biểu đồ         | Nguồn dữ liệu             | Ý nghĩa                             |
| ------------------ | -------------------- | ------------------------- | ----------------------------------- |
| Top start stations | Horizontal bar chart | `gold_top_start_stations` | Trạm bắt đầu phổ biến nhất          |
| Top end stations   | Horizontal bar chart | `gold_top_end_stations`   | Trạm kết thúc phổ biến nhất         |
| Top OD pairs       | Table                | `gold_station_od_pairs`   | Tuyến đi phổ biến giữa các cặp trạm |


### Cách báo cáo

> Top station cho biết khu vực nào phát sinh nhu cầu cao. OD pairs cho biết các cặp trạm có nhiều chuyến đi nhất. Trong thực tế, các thông tin này có thể hỗ trợ điều phối xe, bổ sung xe vào trạm thiếu xe hoặc kiểm tra các trạm có lưu lượng lớn.

## 8. Section 5: User & Bike Behavior

Phần này phân tích hành vi người dùng và loại xe.

### Chart đề xuất


| Chart                     | Loại biểu đồ             | Nguồn dữ liệu             | Ý nghĩa                                                       |
| ------------------------- | ------------------------ | ------------------------- | ------------------------------------------------------------- |
| Member vs Casual behavior | Bar chart                | `gold_user_type_behavior` | So sánh số chuyến, thời lượng, quãng đường giữa member/casual |
| Bike type usage           | Bar chart hoặc pie chart | `gold_bike_type_usage`    | Loại xe nào được sử dụng nhiều hơn                            |


### Cách báo cáo

> Phần này giúp hiểu hành vi người dùng. Member thường thể hiện nhu cầu đi lại thường xuyên, còn casual có thể phản ánh nhu cầu sử dụng không định kỳ hoặc du lịch. Bike type usage giúp biết loại xe nào được sử dụng nhiều nhất.

## 9. Bảng Gold Nên Bổ Sung

Để dashboard handle tốt cả tổng quan, chi tiết theo tháng và so sánh giữa các tháng, nên bổ sung thêm một bảng Gold:

```text
gold_monthly_summary
```

### Cột đề xuất

```text
month
total_rides
member_rides
casual_rides
avg_duration_minutes
avg_distance_km
unique_start_stations
unique_end_stations
```

### Lý do nên thêm

1. Dashboard overview chạy nhanh hơn vì không cần group lại từ bảng daily.
2. So sánh giữa các tháng rõ ràng hơn.
3. Phù hợp với nguồn dữ liệu vì Citi Bike publish theo tháng.
4. Phù hợp với thiết kế Silver vì Silver partition theo `month`.
5. Đây là một data mart rõ ràng ở lớp Gold cho báo cáo month-over-month.

Câu báo cáo:

> Em bổ sung bảng `gold_monthly_summary` để phục vụ báo cáo month-over-month. Đây là một bảng Gold được thiết kế riêng cho dashboard tổng quan theo tháng, giúp query nhanh hơn và tránh phải aggregate lại dữ liệu chi tiết khi người dùng mở dashboard.

## 10. Ý Nghĩa Với Thiết Kế Big Data

Dashboard không chỉ là phần hiển thị, mà còn chứng minh thiết kế pipeline:

```text
Raw
  -> Bronze
  -> Silver partition by month
  -> Gold data marts
  -> Trino/Superset dashboard
```

Các điểm cần nhấn mạnh:

1. Dashboard đọc dữ liệu từ Gold, không đọc trực tiếp Raw/Bronze.
2. Silver partition theo `month`, nên filter theo tháng có ý nghĩa hiệu năng.
3. Gold tables được thiết kế theo câu hỏi phân tích cụ thể.
4. Trino/Superset là serving layer, tách khỏi Spark ETL layer.
5. Thiết kế dashboard phản ánh đúng cách dữ liệu được ingest và xử lý.

Câu báo cáo:

> Dashboard là lớp cuối của pipeline. Nó chứng minh dữ liệu đã đi từ Raw, qua Bronze, Silver, Gold và cuối cùng trở thành insight có thể quan sát được. Điểm quan trọng là dashboard không xử lý dữ liệu nặng, mà khai thác các bảng Gold đã được thiết kế sẵn cho phân tích.

## 11. Kịch Bản Báo Cáo Dashboard

Có thể báo cáo dashboard theo thứ tự sau:

### Bước 1. Giới thiệu mục tiêu dashboard

> Dashboard này được thiết kế để phân tích nhu cầu sử dụng Citi Bike theo tháng. Vì dữ liệu gốc được publish theo tháng và pipeline cũng ingest theo tháng, nên dashboard tập trung vào overview toàn bộ dữ liệu, drill-down từng tháng và so sánh giữa các tháng.

### Bước 2. Nói về nguồn dữ liệu dashboard

> Dashboard không đọc trực tiếp dữ liệu raw. Dữ liệu được Spark xử lý qua Bronze, Silver và Gold. Superset kết nối đến Trino để query các bảng Gold trên MinIO.

### Bước 3. Trình bày KPI tổng quan

> Hàng KPI đầu tiên cho biết tổng số chuyến, số tháng có dữ liệu, trung bình số chuyến mỗi tháng, thời lượng trung bình và quãng đường trung bình. Đây là các chỉ số tổng quan để đánh giá quy mô dữ liệu.

### Bước 4. Trình bày so sánh giữa các tháng

> Biểu đồ theo tháng giúp xem nhu cầu tăng giảm như thế nào. Ngoài tổng số chuyến, dashboard cũng so sánh member và casual, cũng như thời lượng/quãng đường trung bình giữa các tháng.

### Bước 5. Trình bày chi tiết một tháng

> Khi chọn một tháng, dashboard đi sâu vào daily rides và hourly demand. Phần này giúp nhận diện ngày cao điểm và khung giờ cao điểm trong tháng.

### Bước 6. Trình bày trạm và tuyến phổ biến

> Top start/end stations cho biết trạm nào có nhu cầu cao nhất. OD pairs cho biết các tuyến di chuyển phổ biến giữa các cặp trạm. Đây là thông tin có ý nghĩa trong vận hành và điều phối xe.

### Bước 7. Trình bày hành vi người dùng và loại xe

> Cuối cùng, dashboard so sánh member/casual và loại xe được sử dụng. Phần này giúp hiểu nhóm người dùng nào chiếm tỷ trọng lớn và loại xe nào được sử dụng nhiều hơn.

### Bước 8. Chốt ý Big Data

> Điểm quan trọng là dashboard không đứng riêng lẻ. Nó phản ánh toàn bộ thiết kế dữ liệu: ingest theo tháng, partition theo tháng, Gold aggregate theo câu hỏi phân tích và serving qua Trino/Superset.

## 12. Checklist Khi Làm Dashboard

Trước khi demo dashboard, nên kiểm tra:

1. Pipeline đã chạy xong Bronze, Silver và Gold.
2. Có đủ 7 bảng Gold hiện tại.
3. Nếu có so sánh giữa các tháng, nên có thêm `gold_monthly_summary`.
4. Trino đã đọc được bảng Delta trên MinIO.
5. Superset đã kết nối được đến Trino.
6. Dashboard có filter `month`.
7. Các chart dùng dữ liệu Gold, không dùng Raw/Bronze.
8. Mỗi chart trả lời được một câu hỏi phân tích cụ thể.
9. Không nhồi quá nhiều chart; khoảng 6-8 chart là hợp lý.
10. Chuẩn bị câu giải thích chart lấy từ bảng nào và có ý nghĩa gì.

## 13. Dashboard Tối Thiểu Nếu Không Đủ Thời Gian

Nếu thời gian làm dashboard ít, chỉ cần 6 chart chính:

1. KPI: Total rides, Avg duration, Avg distance.
2. Line chart: Total rides by month.
3. Line chart: Daily rides in selected month.
4. Bar chart: Hourly demand.
5. Bar chart: Top start stations.
6. Bar chart: Member vs Casual.

Câu báo cáo:

> Do thời gian demo có hạn, dashboard tập trung vào các chart quan trọng nhất: tổng quan, xu hướng theo tháng, chi tiết trong tháng, giờ cao điểm, trạm phổ biến và hành vi người dùng. Các chart này đủ để chứng minh dữ liệu Gold có thể phục vụ phân tích thực tế.

