# Lời Nói Đầu

Trong kỷ nguyên số hóa hiện nay, sự bùng nổ dữ liệu từ các thiết bị thông minh, hệ thống Internet vạn vật (IoT) và các hệ thống giao thông công cộng đã đặt ra những thách thức lớn về mặt lưu trữ, xử lý và phân tích dữ liệu lớn (Big Data). Việc khai thác hiệu quả nguồn tài nguyên này không chỉ giúp các doanh nghiệp tối ưu hóa hoạt động vận hành mà còn hỗ trợ chính quyền các đô thị thông minh (Smart Cities) đưa ra những quyết định quy hoạch chính xác.

Môn học **Phân tích dữ liệu lớn (Big Data Analytics)** đã trang bị cho chúng em những kiến thức nền tảng quan trọng về các hệ thống xử lý phân tán như Apache Spark, các công nghệ lưu trữ dữ liệu dạng bảng thế hệ mới như Delta Lake, cùng các công cụ truy vấn phân tán và trực quan hóa dữ liệu như Trino và Apache Superset. Nhằm cụ thể hóa những kiến thức lý thuyết đã học vào một bài toán thực tế, nhóm chúng em đã lựa chọn đề tài: **"Thiết kế và triển khai Data Lakehouse chạy local bằng Docker để phân tích dữ liệu chuyến đi NYC Citi Bike sử dụng Apache Spark, Delta Lake, MinIO, Trino và Superset"**.

Chúng em xin bày tỏ lòng biết ơn sâu sắc đến Giảng viên bộ môn đã tận tình truyền đạt kiến thức, định hướng nghiên cứu và tạo điều kiện thuận lợi nhất để nhóm có thể hoàn thành đồ án này. Mặc dù đã có nhiều cố gắng trong quá trình thiết kế hệ thống và hoàn thiện báo cáo, song do giới hạn về mặt tài nguyên phần cứng và thời gian thực hiện, đồ án chắc chắn không tránh khỏi những thiếu sót. Chúng em rất mong nhận được những ý kiến đóng góp, nhận xét từ thầy/cô để đề tài được hoàn thiện hơn.

*Xin chân thành cảm ơn!*

---

# CHƯƠNG 1: GIỚI THIỆU ĐỀ TÀI

## 1.1. Giới thiệu đề tài

Hệ thống giao thông công cộng tại các siêu đô thị lớn như New York (Mỹ) liên tục sinh ra lượng dữ liệu khổng lồ theo thời gian thực. Trong số đó, dịch vụ chia sẻ xe đạp công cộng **NYC Citi Bike** là một trong những hệ thống có quy mô lớn nhất thế giới, ghi nhận hàng chục triệu chuyến đi mỗi năm. Việc thu thập, làm sạch và tổng hợp nguồn dữ liệu hành trình này đòi hỏi một hạ tầng xử lý dữ liệu lớn mạnh mẽ, linh hoạt và tối ưu chi phí.

Đồ án tập trung nghiên cứu và xây dựng một kiến trúc **Data Lakehouse** thu nhỏ chạy hoàn toàn trên môi trường container hóa **Docker** tại máy cục bộ (local). Hệ thống sử dụng mô hình kiến trúc ba tầng dữ liệu (Medallion Architecture: Bronze - Silver - Gold) để xử lý toàn bộ dữ liệu hành trình của NYC Citi Bike trong năm 2024. Quy trình xử lý dữ liệu (ETL/ELT) được thực hiện song song bằng **Apache Spark** và lưu trữ dưới định dạng bảng **Delta Lake** trên nền tảng **MinIO Object Storage** (chuẩn tương thích S3). Lớp Serving (phục vụ truy vấn) sử dụng query engine phân tán **Trino** giúp tăng tốc độ truy xuất SQL, kết nối trực tiếp đến dashboard công cụ **Apache Superset** để cung cấp các báo cáo trực quan về xu hướng vận hành và hành vi khách hàng.

## 1.2. Lý do chọn đề tài

### 1.2.1. Tầm quan trọng của dữ liệu NYC Citi Bike
Dữ liệu chuyến đi của NYC Citi Bike là một tập dữ liệu Big Data thực tế điển hình, sở hữu đầy đủ đặc trưng của dữ liệu lớn (Volume - kích thước hàng chục triệu dòng mỗi năm; Variety - đa dạng về kiểu thông tin từ thời gian, không gian địa lý, phân loại xe đến nhóm khách hàng; Velocity - tần suất phát sinh hành trình liên tục). Khai thác tập dữ liệu này giúp giải quyết các bài toán thực tiễn quan trọng:
*   Đo lường và dự báo nhu cầu sử dụng xe theo thời gian (giờ cao điểm, ngày thường vs cuối tuần) và theo mùa.
*   Xếp hạng các trạm xe nóng (hotspot) về lượng đi/đến, hỗ trợ bài toán tái cân bằng (rebalancing) đội xe đạp của đơn vị vận hành.
*   Phân tích sự khác biệt về hành vi giữa nhóm khách hàng đăng ký thành viên (Member) và khách vãng lai (Casual) để tối ưu chiến lược marketing.

### 1.2.2. Sự chuyển dịch sang kiến trúc Data Lakehouse
Trước đây, các hệ thống Big Data thường bị chia rẽ thành hai hệ thống độc lập: **Data Lake** (mạnh về lưu trữ dữ liệu thô giá rẻ nhưng thiếu tính toàn vẹn) và **Data Warehouse** (truy vấn nhanh, hỗ trợ ACID nhưng chi phí lưu trữ cao và không linh hoạt). Kiến trúc **Data Lakehouse** ra đời nhằm kết hợp những ưu điểm vượt trội của cả hai thế giới:
*   Cho phép lưu trữ dữ liệu trên Object Storage giá rẻ (như MinIO/S3).
*   Bổ sung tầng định dạng bảng thế hệ mới (Delta Lake) để hỗ trợ các giao dịch ACID (ACID Transactions), quản lý Schema (Schema Enforcement) và khôi phục phiên bản lịch sử (Time Travel).
*   Tách biệt hoàn toàn tầng Tính toán (Compute - Spark/Trino) và tầng Lưu trữ (Storage - MinIO) giúp hệ thống dễ dàng mở rộng độc lập khi quy mô dữ liệu tăng lên.

### 1.2.3. Khả năng đóng gói local bằng Docker Compose
Việc triển khai các hệ thống Big Data trên Cloud (AWS/GCP) thường tốn kém chi phí lớn đối với sinh viên học tập. Đề tài lựa chọn xây dựng môi trường chạy local qua Docker giúp giả lập chính xác một hệ thống Big Data thực tế mà không phát sinh chi phí, đồng thời dễ dàng chuyển đổi cấu hình lên các dịch vụ Cloud thương mại khi cần thiết.

## 1.3. Mục Tiêu Đề Tài

Đề tài đặt ra các mục tiêu cốt lõi sau:
1.  **Thiết kế và cấu hình hạ tầng Lakehouse cục bộ:** Đóng gói thành công các dịch vụ MinIO (4 nodes cluster), Apache Spark (1 master, 2 workers), Trino query engine và Apache Superset trong cùng một mạng Docker Compose.
2.  **Xây dựng Pipeline Medallion 3 tầng hoàn chỉnh:**
    *   **Bronze Layer:** Nạp nguyên bản dữ liệu CSV từ nguồn vào định dạng Delta Lake, lưu trữ lịch sử audit.
    *   **Silver Layer:** Thực hiện loại lọc dữ liệu lỗi, tính toán khoảng cách địa lý bằng công thức toán học Haversine và trích xuất các đặc trưng thời gian.
    *   **Gold Layer:** Tạo ra 8 bảng dữ liệu aggregated tối ưu hóa cho các câu hỏi phân tích cụ thể, đặc biệt bổ sung bảng `gold_monthly_summary` để tăng tốc truy vấn báo cáo xu hướng tháng.
3.  **Tối ưu hiệu năng serving:** Tích hợp Trino để làm cầu nối trung gian, cho phép Superset thực hiện các truy vấn SQL song song trực tiếp lên Delta Lake trên MinIO với độ trễ thấp nhất.
4.  **Tự động hóa trực quan hóa:** Viết script Python tự động hóa REST API của Superset để cấu hình và dựng dashboard 11 biểu đồ trực quan, sạch sẽ và chuyên nghiệp phục vụ kịch bản điều phối vận hành thực tế.

---

# TÀI LIỆU THAM KHẢO (IEEE STANDARD)

[1] M. Armbrust *et al.*, "Lakehouse: A new generation of open platforms on top of data lakes," in *Proceedings of the 11th Conference on Innovative Data Systems Research (CIDR)*, Jan. 2021, Art. no. 28.

[2] M. Armbrust *et al.*, "Delta Lake: High-performance ACID table storage over cloud object stores," *Proceedings of the VLDB Endowment*, vol. 13, no. 12, pp. 3411-3424, Aug. 2020, doi: 10.14778/3415478.3415560.

[3] M. Zaharia *et al.*, "Apache Spark: A unified engine for big data processing," *Communications of the ACM*, vol. 59, no. 11, pp. 56-65, Nov. 2016, doi: 10.1145/2934664.

[4] W. Sethasakkoon and T. Senivongse, "Performance evaluation of SQL query engines on Delta Lakehouse," in *Proceedings of the 20th International Joint Conference on Computer Science and Software Engineering (JCSSE)*, Phitsanulok, Thailand, 2023, pp. 154-159, doi: 10.1109/JCSSE58229.2023.10202111.

[5] T. White, *Hadoop: The Definitive Guide*, 4th ed. Sebastopol, CA, USA: O'Reilly Media, 2015.

[6] Citi Bike NYC, "Citi Bike System Data," Lyft, Inc., 2024. [Online]. Available: https://citibikenyc.com/system-data. [Accessed: Jul. 2, 2026].

[7] Apache Software Foundation, "Apache Superset Documentation," 2024. [Online]. Available: https://superset.apache.org/docs/. [Accessed: Jul. 2, 2026].

[8] Trino Software Foundation, "Trino Distributed SQL Query Engine Documentation," 2024. [Online]. Available: https://trino.io/docs/current/. [Accessed: Jul. 2, 2026].
