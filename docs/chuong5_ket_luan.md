# Chương 5: Kết Luận và Hướng Phát Triển

## 5.1 Kết Luận

Đề tài **"Thiết kế và triển khai Data Lakehouse chạy local bằng Docker để phân tích dữ liệu chuyến đi NYC Citi Bike sử dụng Apache Spark, Delta Lake, MinIO, Trino và Superset"** đã được nghiên cứu, phát triển và hoàn thành đầy đủ các mục tiêu đề ra ban đầu. 

Dưới đây là các kết quả nổi bật đã đạt được:

### 5.1.1 Về mặt kiến trúc và hạ tầng hệ thống
1. **Thiết lập môi trường container hóa hoàn chỉnh:** Sử dụng Docker Compose để triển khai một hệ sinh thái Big Data thu nhỏ ngay trên môi trường máy cá nhân (Local). Các thành phần được tích hợp chặt chẽ, tối ưu hóa tài nguyên phần cứng cục bộ.
2. **Triển khai Object Storage độc lập:** Sử dụng MinIO làm hệ thống lưu trữ phân tán tương thích chuẩn S3 API, đóng vai trò là kho chứa dữ liệu tập trung (Centralized Storage) lưu trữ cả dữ liệu thô (raw) và dữ liệu có cấu trúc.
3. **Hiện thực hóa kiến trúc Data Lakehouse:** Áp dụng định dạng bảng Delta Lake giúp mang lại các tính năng ACID transaction, lưu vết phiên bản dữ liệu (Time Travel) và quản lý schema tự động trên nền tảng MinIO. Hệ thống đã xóa nhòa ranh giới giữa Data Lake và Data Warehouse truyền thống.

### 5.1.2 Về quy trình xử lý dữ liệu (Data Pipeline)
1. **Xây dựng Pipeline 3 tầng tiêu chuẩn (Medallion Architecture):**
    * **Tầng Bronze (Ingestion):** Tự động hóa quá trình nạp dữ liệu thô từ file CSV tháng vào Delta Lake, lưu trữ nguyên bản kèm siêu dữ liệu phục vụ audit.
    * **Tầng Silver (Transformation):** Làm sạch, chuẩn hóa kiểu dữ liệu, loại bỏ ngoại lai và tối ưu hóa tính toán không gian/thời gian thông qua công thức Haversine tính toán khoảng cách di chuyển thực tế.
    * **Tầng Gold (Serving):** Aggregate dữ liệu thành 8 bảng tối ưu hóa cho mục đích phân tích doanh nghiệp (bao gồm cả bảng báo cáo vĩ mô hàng tháng `gold_monthly_summary`).
2. **Tối ưu hóa hiệu năng truy vấn:** Kết hợp **Trino (Presto SQL)** làm động cơ truy vấn phân tán để kết nối trực tiếp đến các bảng Delta Lake trong MinIO, cung cấp tốc độ phản hồi truy vấn SQL tính bằng mili-giây.

### 5.1.3 Về phân tích nghiệp vụ và trực quan hóa (BI Dashboard)
1. **Dashboard Business Intelligence trực quan:** Tích hợp thành công hệ thống **Apache Superset** kết nối với Trino. Thiết lập tập lệnh tự động hóa REST API thiết lập 11 biểu đồ nghiệp vụ chất lượng cao, trả lời trọn vẹn các bài toán thực tế như: phân bổ nhu cầu theo thời gian, bản đồ nhiệt giờ cao điểm, đặc trưng hành vi nhóm người dùng, xu hướng dịch chuyển dòng xe đạp điện và xu hướng biến động doanh số theo từng tháng (MoM).
2. **Dọn dẹp và tự động hóa vận hành:** Xây dựng cơ chế dọn dẹp biểu đồ trùng lặp và tự động cập nhật datasets, giúp việc quản trị và trình diễn dashboard cực kỳ mượt mà.

---

## 5.2 Hạn Chế Của Đề Tài

Mặc dù hệ thống đã đáp ứng được toàn bộ yêu cầu nghiệp vụ cơ bản, đề tài vẫn còn tồn tại một số điểm hạn chế nhất định cần được xem xét:

1. **Hạn chế về hạ tầng triển khai cục bộ (Local Infrastructure):** Việc chạy toàn bộ stack Big Data trên Docker Compose nội bộ giúp tiết kiệm chi phí nhưng bị giới hạn bởi tài nguyên CPU, RAM và Disk của máy cá nhân. Chưa thử nghiệm khả năng chịu tải và phân tán trên môi trường Cloud (AWS/GCP/Azure) thực tế với khối lượng dữ liệu khổng lồ (Petabyte).
2. **Thiếu các nguồn dữ liệu bổ trợ:** Hệ thống chỉ phân tích dữ liệu chuyến đi thuần túy mà chưa tích hợp các yếu tố ngoại cảnh như: điều kiện thời tiết (mưa, tuyết, nhiệt độ cực đoan), lịch nghỉ lễ, sự kiện lớn hay tình trạng giao thông công cộng khác tại NYC. Đây là những nhân tố cực kỳ quan trọng ảnh hưởng trực tiếp đến nhu cầu di chuyển.
3. **Thiếu công cụ điều phối tự động:** Dự án hiện tại đang kích hoạt pipeline thủ công hoặc theo các shell script đơn giản, chưa tích hợp hệ thống quản lý luồng công việc (Workflow Orchestration) chuyên nghiệp như Apache Airflow hay Prefect.

---

## 5.3 Hướng Phát Triển Tiếp Theo

Từ những hạn chế nêu trên, các hướng nghiên cứu và phát triển tiếp theo của đề tài bao gồm:

### 5.3.1 Nâng cấp hạ tầng và mở rộng quy mô
* **Triển khai lên Cloud Data Lakehouse:** Chuyển đổi các dịch vụ local sang các dịch vụ tương đương trên Cloud, ví dụ: sử dụng **Amazon S3** hoặc **Google Cloud Storage** làm Storage Layer; chạy Spark trên **AWS EMR** hoặc **GCP Dataproc** để kiểm chứng hiệu năng tính toán phân tán thực tế.
* **Tích hợp Apache Airflow:** Xây dựng hệ thống lập lịch tự động, gửi cảnh báo khi pipeline gặp lỗi (alerting), và giám sát (monitoring) trạng thái dữ liệu định kỳ thông qua các luồng Directed Acyclic Graphs (DAGs).

### 5.3.2 Tối ưu hóa chất lượng dữ liệu và kỹ thuật lưu trữ
* **Tối ưu cấu trúc Delta Lake:** Áp dụng các kỹ thuật nâng cao của Delta Lake như **Compaction** (gộp các file Parquet nhỏ để tối ưu I/O) và **Z-Ordering** trên các cột hay truy vấn (`start_hour`, `start_station_name`) nhằm tăng tốc độ lọc dữ liệu khi phân tích.
* **Kiểm thử dữ liệu nâng cao:** Đưa công cụ **Great Expectations** vào tầng Silver để tự động kiểm thử chất lượng dữ liệu (Data Quality Checks) trước khi đẩy vào tầng Gold, hạn chế lỗi logic dữ liệu ảnh hưởng tới dashboard.

### 5.3.3 Xây dựng kiến trúc xử lý thời gian thực (Real-time Pipeline)
* Thiết lập luồng xử lý luồng (Streaming Pipeline) bằng cách tích hợp **Apache Kafka** để hứng dữ liệu sự kiện mở khóa xe (Real-time ride events) và sử dụng **Spark Structured Streaming** để cập nhật trực tiếp trạng thái các trạm xe lên bản đồ tương tác của người quản lý, hỗ trợ ra quyết định điều phối xe đạp tức thì.
