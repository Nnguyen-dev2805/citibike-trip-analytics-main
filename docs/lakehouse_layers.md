# 5 Lớp Trong Kiến Trúc Data Lakehouse

## 1. Lớp nguồn dữ liệu và nạp dữ liệu

Mục đích: thu thập dữ liệu từ hệ thống nguồn và đưa vào vùng lưu trữ ban đầu.

Công cụ trong dự án: Python downloader và Spark job `ingest_bronze.py`.

Input: file ZIP/CSV lịch sử chuyến đi từ NYC Citi Bike.

Output: file CSV raw trong MinIO và bảng Bronze Delta.

Ý nghĩa: lớp này giúp hệ thống giữ lại dữ liệu gốc để có thể kiểm tra, tái xử lý hoặc đối chiếu khi cần.

## 2. Lớp lưu trữ

Mục đích: lưu dữ liệu ở nhiều mức xử lý khác nhau, từ raw đến curated.

Công cụ trong dự án: MinIO, một object storage tương thích S3 chạy local bằng Docker.

Input: file raw, Delta table Bronze, Silver và Gold.

Output: cấu trúc bucket `lakehouse/raw`, `lakehouse/bronze`, `lakehouse/silver`, `lakehouse/gold`.

Ý nghĩa: object storage giúp lưu dữ liệu lớn với chi phí thấp và tách biệt lưu trữ khỏi xử lý.

## 3. Lớp định dạng bảng

Mục đích: biến file trên object storage thành bảng dữ liệu có transaction log, schema và khả năng quản lý phiên bản.

Công cụ trong dự án: Delta Lake.

Input: DataFrame từ Spark.

Output: các thư mục Delta có `_delta_log` và file Parquet.

Ý nghĩa: Delta Lake bổ sung ACID transaction, schema enforcement và khả năng đọc bảng nhất quán, khắc phục hạn chế của data lake chỉ lưu file rời rạc.

## 4. Lớp xử lý dữ liệu

Mục đích: làm sạch, chuẩn hóa, tạo cột dẫn xuất và tổng hợp dữ liệu.

Công cụ trong dự án: Apache Spark / PySpark.

Input: Bronze Delta hoặc Silver Delta.

Output: Silver Delta sạch và các bảng Gold phục vụ phân tích.

Ý nghĩa: Spark phù hợp với dữ liệu lớn, có thể mở rộng, và cho phép viết pipeline ETL rõ ràng bằng Python.

## 5. Lớp phục vụ và phân tích

Mục đích: cung cấp dữ liệu đã xử lý cho truy vấn SQL, báo cáo và dashboard.

Công cụ trong dự án: Spark SQL, Trino và Superset.

Input: các bảng Gold Delta.

Output: kết quả truy vấn, biểu đồ, dashboard và insight kinh doanh.

Ý nghĩa: người dùng cuối không cần đọc dữ liệu raw mà có thể khai thác trực tiếp các bảng Gold đã được chuẩn hóa theo câu hỏi phân tích.
