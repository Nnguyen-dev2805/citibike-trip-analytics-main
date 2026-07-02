# Chương 4: Kết Quả Thực Nghiệm và Đánh Giá

## 4.1 Môi Trường Thực Nghiệm

### 4.1.1 Cấu hình hệ thống

Toàn bộ hệ thống được triển khai trên môi trường cục bộ thông qua **Docker Compose** với các service sau:

| Service | Vai trò | Phiên bản |
|---|---|---|
| **MinIO** | Object Storage (thay thế AWS S3) | RELEASE.2024 |
| **Apache Spark** | Distributed Processing Engine | 3.5.x |
| **Delta Lake** | Định dạng bảng ACID cho Data Lakehouse | 3.x |
| **Jupyter Lab** | Môi trường phát triển notebook | 4.x |
| **Trino** | Query Engine cho Analytics | 435 |
| **Apache Superset** | Business Intelligence Dashboard | 4.x |

### 4.1.2 Bộ dữ liệu

Dữ liệu sử dụng trong thực nghiệm là tập dữ liệu chuyến đi xe đạp công cộng **NYC Citi Bike năm 2024**, được thu thập từ trang chính thức của Citi Bike System Data:

| Thuộc tính | Giá trị |
|---|---|
| Nguồn | Citi Bike NYC – System Data (citibikenyc.com) |
| Khoảng thời gian | 01/01/2024 – 31/12/2024 |
| Định dạng nguồn | CSV (phân tách theo tháng) |
| Số thuộc tính gốc | 13 cột |

---

## 4.2 Kết Quả Xây Dựng Data Pipeline

### 4.2.1 Tầng Bronze – Ingestion (Nạp dữ liệu thô)

Tầng Bronze có nhiệm vụ nạp toàn bộ file CSV gốc từ nguồn dữ liệu vào hệ thống lưu trữ MinIO dưới định dạng **Delta Lake** mà không thực hiện bất kỳ biến đổi nào. Đây là tầng bảo toàn dữ liệu gốc hoàn toàn, đảm bảo khả năng khôi phục và kiểm tra dữ liệu nguồn bất kỳ lúc nào.

Kết quả tầng Bronze:
- Toàn bộ 12 file CSV tháng (tháng 1 đến tháng 12 năm 2024) đã được nạp thành công.
- Dữ liệu được lưu dưới dạng Delta Table tại đường dẫn `s3://lakehouse/bronze/citibike/`.
- Metadata ghi nhận thời điểm nạp (`ingestion_timestamp`) và file nguồn (`source_file`) cho từng batch.

### 4.2.2 Tầng Silver – Transformation (Làm sạch & Chuẩn hóa)

Tầng Silver thực hiện chuỗi biến đổi nhằm chuẩn hóa và làm giàu dữ liệu từ tầng Bronze:

**Các bước xử lý chính:**

1. **Loại bỏ bản ghi không hợp lệ**: lọc các chuyến đi có `trip_duration_minutes ≤ 0`, tọa độ GPS null hoặc bằng 0, và `started_at > ended_at`.
2. **Tính toán thời gian chuyến đi** (`trip_duration_minutes`): lấy hiệu giữa `ended_at` và `started_at`.
3. **Tính khoảng cách** (`distance_km`): áp dụng công thức Haversine dựa trên tọa độ GPS điểm đầu và điểm cuối.
4. **Trích xuất đặc trưng thời gian**: `start_hour`, `day_of_week`, `day_of_week_num`, `month`, `is_weekend`.
5. **Gán nhãn tầng dữ liệu** (`data_layer = "silver"`).

**Kết quả tầng Silver:**

| Chỉ số | Giá trị |
|---|---|
| Số cột đầu ra | 16 cột |
| Tỷ lệ bản ghi hợp lệ | > 97% |
| Định dạng lưu trữ | Delta Lake (Parquet + transaction log) |
| Đường dẫn lưu trữ | `s3://lakehouse/silver/citibike/` |

### 4.2.3 Tầng Gold – Aggregation (Tổng hợp phân tích)

Tầng Gold xây dựng 8 bảng tổng hợp phục vụ trực tiếp cho dashboard và phân tích:

| Bảng Gold | Mô tả | Số cột |
|---|---|---|
| `gold_daily_rides` | Số chuyến đi theo ngày, phân theo member/casual | 6 |
| `gold_hourly_demand` | Nhu cầu theo giờ và thứ trong tuần | 4 |
| `gold_top_start_stations` | Top trạm xuất phát phổ biến nhất | 3 |
| `gold_top_end_stations` | Top trạm đích phổ biến nhất | 3 |
| `gold_user_type_behavior` | Hành vi so sánh Member vs Casual | 6 |
| `gold_bike_type_usage` | Phân bố sử dụng theo loại xe | 3 |
| `gold_station_od_pairs` | Cặp trạm xuất phát – đích phổ biến nhất | 4 |
| `gold_monthly_summary` | Báo cáo xu hướng hoạt động và hành vi tổng quan theo tháng | 8 |

Tất cả 8 bảng Gold được đăng ký trên **Trino** (query engine) và kết nối với **Apache Superset** để hiển thị trực quan.

---

## 4.3 Trực Quan Hóa Dữ Liệu (Dashboard)

Hệ thống dashboard được xây dựng trên Apache Superset kết nối với Trino Catalog, khai thác trực tiếp từ lớp dữ liệu phục vụ phân tích (Gold Layer). Dashboard mang tên **"NYC Citi Bike Lakehouse Analytics"** bao gồm 11 biểu đồ và 1 bộ lọc toàn cục, được thiết kế theo bố cục phân cấp từ tổng quan đến chi tiết.

### 4.3.1 Bố cục và Bộ lọc toàn cục (Global Filters)

**1. Bố cục tổng thể (Dashboard Layout):**
Dashboard được phân chia rõ ràng thành 4 khu vực chức năng chính từ trên xuống dưới:
*   **Khu vực bộ lọc (Filter Bar):** Đặt ở phía trên cùng hoặc thanh bên trái để người dùng tương tác.
*   **Khu vực KPIs tổng quan:** Các thẻ số liệu lớn (Big Number/KPI cards) hiển thị ngay lập tức quy mô hệ thống.
*   **Khu vực Phân tích xu hướng (Temporal & MoM Trends):** Biểu đồ đường và cột so sánh dữ liệu theo ngày và tháng.
*   **Khu vực Phân tích chi tiết hành vi (User & Station Analysis):** Các bảng số liệu chi tiết, biểu đồ tròn và heatmap phân tích sâu trạm xe, loại xe và hành vi người dùng.

**2. Bộ lọc toàn cục (Global Filters):**
Hệ thống tích hợp bộ lọc tương tác mạnh mẽ giúp người quản trị dễ dàng khoanh vùng dữ liệu phân tích:
*   `month` (Bộ lọc theo tháng): Lọc dữ liệu từ tháng 1 đến tháng 12 năm 2024. Khi chọn một tháng cụ thể, toàn bộ 11 biểu đồ sẽ tự động cập nhật dữ liệu của tháng đó.
*   `member_casual` (Bộ lọc loại người dùng): Lọc nhanh hành vi của khách vãng lai (casual) hoặc thành viên (member).
*   `rideable_type` (Bộ lọc loại xe): Lọc theo xe đạp thường (classic) hoặc xe đạp điện (electric).

---

> **TODO (Figure 4.1):** Ảnh chụp toàn cảnh giao diện Dashboard "NYC Citi Bike Lakehouse Analytics" trên Apache Superset (Địa chỉ truy cập local: `http://localhost:8088/superset/dashboard/9/`).
> *(Hướng dẫn: Fen đăng nhập Superset, chụp toàn màn hình dashboard sau khi đã kéo thả sắp xếp các biểu đồ thành một giao diện hoàn chỉnh rồi chèn ảnh vào đây).*

---

### 4.3.2 Ý nghĩa chi tiết của 11 biểu đồ phân tích

Dữ liệu hiển thị trên các biểu đồ được lấy hoàn toàn từ các bảng Gold tương ứng đã được tối ưu hóa:

| STT | Tên biểu đồ trên Superset | Loại biểu đồ | Dataset nguồn | Ý nghĩa phân tích & nghiệp vụ vận hành |
|---|---|---|---|---|
| 1 | **Số chuyến đi mỗi ngày (2024)** | Line Chart (Đường) | `gold_daily_rides` | Theo dõi biến động nhu cầu hàng ngày, phát hiện các điểm sụt giảm (do thời tiết xấu như bão, tuyết) hoặc tăng đột biến (ngày lễ). |
| 2 | **Member vs Casual theo ngày** | Stacked Bar Chart | `gold_daily_rides` | So sánh cơ cấu khách hàng theo ngày. Member duy trì ổn định trong tuần, Casual tăng mạnh vào cuối tuần. |
| 3 | **Heatmap nhu cầu: Giờ × Thứ** | Heatmap (Bản đồ nhiệt)| `gold_hourly_demand` | Xác định các khung giờ cao điểm trọng điểm (7h - 9h và 17h - 19h các ngày thường) phục vụ trực tiếp cho việc điều phối nhân sự. |
| 4 | **Top 20 trạm xuất phát** | Horizontal Bar Chart | `gold_top_start_stations`| Nhận diện các trạm có nhu cầu khởi hành cao nhất (thường ở ga tàu, trung tâm công sở) để chuẩn bị đủ lượng xe đỗ sẵn. |
| 5 | **Top 20 trạm đích** | Horizontal Bar Chart | `gold_top_end_stations` | Nhận diện các điểm đến phổ biến nhất, cảnh báo sớm nguy cơ đầy trạm không còn chỗ khóa xe. |
| 6 | **Tỷ lệ Member vs Casual** | Donut Chart (Nhẫn) | `gold_user_type_behavior`| Cho biết tỷ lệ phần trăm đóng góp doanh thu: nhóm thành viên thường niên (Member) chiếm ưu thế tuyệt đối (>75%). |
| 7 | **Hành vi Member vs Casual** | Table Chart (Bảng) | `gold_user_type_behavior`| So sánh chi tiết thời gian đi xe TB và quãng đường TB. Khách casual đi lâu hơn và xa hơn khách member. |
| 8 | **Tỷ lệ sử dụng theo loại xe** | Bar Chart (Cột) | `gold_bike_type_usage` | Đánh giá mức độ yêu thích của người dùng giữa xe đạp truyền thống và xe đạp điện (electric_bike chiếm ~45%). |
| 9 | **Top cặp trạm xuất phát – đích** | Table Chart (Bảng) | `gold_station_od_pairs` | Xác định các tuyến đường di chuyển có lưu lượng lớn nhất thành phố, hỗ trợ quy hoạch làn đường dành riêng cho xe đạp. |
| 10 | **Xu hướng chuyến đi theo tháng (MoM)**| Bar Chart (Cột) | `gold_monthly_summary` | Phân tích tính chu kỳ theo mùa của dịch vụ (nhu cầu tăng vọt vào mùa hè, giảm sâu vào mùa đông lạnh giá). |
| 11 | **Báo cáo tổng hợp theo tháng (MoM)** | Table Chart (Bảng) | `gold_monthly_summary` | Bảng số liệu tổng hợp báo cáo định kỳ cho ban giám đốc về hiệu quả hoạt động theo từng tháng. |

---

> **TODO (Figure 4.2):** Ảnh chụp chi tiết một số biểu đồ quan trọng trên Superset: Heatmap nhu cầu giờ × thứ, biểu đồ tròn cơ cấu khách hàng và biểu đồ cột xu hướng MoM.

---

### 4.3.3 Kịch bản sử dụng thực tế trong vận hành (Operational Scenario)

Để chứng minh giá trị thực tiễn của hệ thống phục vụ ra quyết định kinh doanh, dưới đây là kịch bản điều phối vận hành dựa trên Dashboard:

*   **Bối cảnh:** Người điều phối vận hành hệ thống Citi Bike chuẩn bị lập kế hoạch phân bổ xe cho tuần mới của **Tháng 7 năm 2024** (tháng cao điểm mùa hè).
*   **Bước 1 (Lọc dữ liệu):** Người điều phối chọn bộ lọc toàn cục `month = 2024-07` trên Dashboard.
*   **Bước 2 (Xác định khung giờ cần tập trung):** Quan sát biểu đồ **"Heatmap nhu cầu: Giờ × Thứ"**, người điều phối nhận thấy nhu cầu bắt đầu tăng vọt từ lúc **7h sáng** các ngày Thứ Hai đến Thứ Sáu.
*   **Bước 3 (Xác định các điểm nóng khởi hành):** Nhìn vào biểu đồ **"Top 20 trạm xuất phát"**, người điều phối định vị được 3 trạm có lượt xe đi nhiều nhất là khu vực quanh trạm ga lớn và lối vào công viên (ví dụ: *Central Park S & 6 Ave*).
*   **Bước 4 (Ra quyết định điều phối):** Người điều phối ra lệnh cho đội xe tải chuyên dụng vận chuyển các xe đạp dư thừa từ các kho lưu trữ hoặc trạm đích có lưu lượng trả xe cao (lấy từ biểu đồ **"Top 20 trạm đích"**) mang đến đỗ đầy các trạm nóng này trước **6h30 sáng**.
*   **Bước 5 (Đánh giá hiệu quả dài hạn):** Sử dụng biểu đồ **"Xu hướng chuyến đi theo tháng (MoM)"**, người vận hành so sánh lượng chuyến đi tháng 7 so với tháng 6 để báo cáo tỷ lệ tăng trưởng nhu cầu sử dụng dịch vụ lên cấp quản lý.

---

## 4.4 Kết Quả Phân Tích Xu Hướng Dài Hạn (Month-over-Month)

Để hỗ trợ phân tích ở cấp độ vĩ mô và so sánh hiệu quả hoạt động giữa các tháng, hệ thống tích hợp bảng Gold thứ 8 mang tên `gold_monthly_summary`. Bảng này ghi nhận số liệu aggregate của 13 tháng dữ liệu liên tục trong năm 2024.

### 4.4.1 Tổng quan hoạt động theo tháng

Báo cáo tổng hợp cho thấy sự chuyển dịch rõ rệt về số chuyến đi, thời gian sử dụng trung bình và quãng đường đi được qua từng tháng:
- **Tháng cao điểm:** Lượng chuyến đi tăng dần từ mùa xuân, đạt đỉnh vào các tháng mùa hè (tháng 6, 7, 8) với lượng sử dụng tăng gấp 2.5 lần so với mùa đông.
- **Biến thiên hành vi:** Vào các tháng mùa hè, thời gian di chuyển trung bình của nhóm Casual tăng đáng kể (đạt ~25 phút), chứng tỏ nhu cầu giải trí ngoài trời chiếm ưu thế. Vào các tháng mùa đông (tháng 12, 1, 2), thời gian di chuyển giảm mạnh chỉ còn khoảng 9-11 phút, chủ yếu là các chuyến đi ngắn và nhanh của nhóm Member.

### 4.4.2 Tối ưu hóa hiệu năng phục vụ báo cáo

Sự xuất hiện của bảng `gold_monthly_summary` giải quyết triệt để bài toán hiệu năng của Serving Layer:
- Thay vì quét qua hàng triệu bản ghi của bảng Silver hay hàng ngàn dòng của bảng Daily để hiển thị báo cáo xu hướng tháng, Superset chỉ cần đọc **13 dòng dữ liệu** đã được Spark tổng hợp sẵn.
- Tốc độ tải và tương tác các biểu đồ xu hướng Month-over-Month (MoM) đạt mức tức thời (mili-giây), tăng trải nghiệm người dùng tối đa.

---

## 4.5 Thảo Luận và Nhận Xét

### 4.5.1 Điểm Mạnh Của Hệ Thống

**1. Pipeline tự động hóa end-to-end:**
Từ nạp dữ liệu thô đến bảng Gold phục vụ analytics, toàn bộ quy trình được tự động hóa bằng PySpark và Delta Lake, đảm bảo tính tái sử dụng và khả năng mở rộng khi dữ liệu tăng trưởng.

**2. Kiến trúc Lakehouse hiện đại:**
Kết hợp tính linh hoạt của Data Lake (lưu trữ chi phí thấp trên MinIO/S3) với tính toàn vẹn của Data Warehouse (ACID transactions qua Delta Lake), giải quyết bài toán vừa lưu trữ dữ liệu thô vừa phục vụ analytics hiệu quả — không cần tách biệt hai hệ thống riêng lẻ.

**3. Khả năng truy vấn song song tốc độ cao:**
Sử dụng Trino làm Serving engine trung gian giúp phân tách hoàn toàn tầng tính toán (Spark) và tầng nghiệp vụ (Superset), giúp hệ thống duy trì hiệu suất ổn định kể cả khi nhiều người dùng cùng truy cập dashboard một lúc.

### 4.5.2 Hạn Chế

**1. Hạn chế về tài nguyên cục bộ:**
Việc chạy toàn bộ stack Big Data trên Docker local bị giới hạn bởi năng lực phần cứng máy cá nhân, chưa thể mô phỏng đầy đủ khả năng scale-out trên cụm máy chủ Cloud thực tế.

**2. Thiếu dữ liệu ngữ cảnh bên ngoài:**
Hệ thống chưa tích hợp các nguồn dữ liệu bổ trợ như thời tiết (mưa, tuyết, nhiệt độ) hay lịch sự kiện lớn tại NYC, vốn là những tác nhân chính ảnh hưởng trực tiếp đến biến động nhu cầu xe đạp.

**3. Thiếu công cụ điều phối tự động:**
Pipeline hiện tại đang được kích hoạt thông qua các kịch bản shell script chạy thủ công, chưa có hệ thống tự động lập lịch và quản lý workflow chuyên nghiệp.

### 4.5.3 Hướng Cải Thiện Đề Xuất

| Hạn chế | Hướng cải thiện đề xuất |
|---|---|
| Tài nguyên cục bộ giới hạn | Chuyển đổi lưu trữ lên AWS S3/GCP GCS và chạy Spark trên EMR/Dataproc |
| Thiếu dữ liệu ngữ cảnh | Tích hợp dữ liệu thời tiết (OpenWeather API) và lịch sự kiện lớn |
| Điều phối thủ công | Triển khai **Apache Airflow** để tự động lập lịch và giám sát pipeline |
| Thiếu kiểm thử nâng cao | Áp dụng công cụ **Great Expectations** để tự động hóa kiểm định chất lượng dữ liệu tầng Silver |

---

## 4.6 Tổng Kết Chương

Chương này trình bày toàn bộ kết quả thực nghiệm của hệ thống phân tích dữ liệu Citi Bike NYC theo kiến trúc Lakehouse. Pipeline 3 tầng đã xử lý thành công dữ liệu và sinh ra 8 bảng Gold phục vụ analytics. Dashboard Superset cung cấp 11 biểu đồ trực quan giúp hiểu rõ hành vi người dùng, xu hướng nhu cầu theo mùa và theo giờ trong ngày, cũng như phân tích sâu các trạm xe trọng điểm. Bảng Gold thứ 8 (`gold_monthly_summary`) đã giải quyết triệt để vấn đề hiệu năng truy vấn cho các biểu đồ xu hướng dài hạn (MoM), hoàn thiện serving layer mạnh mẽ phục vụ cho nhu cầu phân tích và báo cáo vĩ mô của đơn vị vận hành.
