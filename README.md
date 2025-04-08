hướng dẫn sử dụng:

1. Cài môi trường ảo virtualenv (lên ytb xem)
2. Kích hoạt môi trường ảo và vào bên trong file cần thiết: cd vào trong folder đã tạo môi trường ảo(có file chứa code), gõ scripts\activate
3. Cài tất cả các thư viện trong requirements.txt: pip istall -r requirements.txt
4. Nhập lệnh chạy file như thường (nên tạo 1 file src để chứa code, cd vào và chạy: python main.py)


cách hoạt động:
1.  đầu tiên tìm ra url chung của các trang chủ và số trang, VD https://vneconomy.vn/tai-chinh.htm?trang=2
2.  lặp qua các tiêu đề categories đã nhập và số trang, truy cập vào url 
3.  tìm các box chứa toàn nội dung và link trong trang, lưu nó vào 1 mảng list articles . VD:![image](https://github.com/user-attachments/assets/72d07407-32e1-4ee7-9598-74b6a0f10d8f)
4.  lặp qua các box, tìm ra chỉ số chứa link, lặp qua các chỉ số chứa link ,xử lý link nếu link dạng rút gọn không đầy đủ , lưu các link đã tìm được vào 1 list đã khai báo ở đầu cùng với các chỉ số url, source, category (source bị thừa, lười sửa)
5.  sau khi có các link, cho vào 1 set để kiểm tra và loại bỏ các link trùng nhau vì trong 1 bài báo, các chỉ số có khả năng tìm được 2 link giống nhau(ví dụ ấn vào ảnh để mở bài báo hoặc ấn vào chữ để mở bài báo)
6.  lặp qua tất cả các link, truy cập vào url sẽ cho ra bài báo cụ thể, tìm và lưu các biến dạng tittle, summary và list content_element, sau đó trả về giá trị từ điển
7.  lưu dữ liệu thô vào thư mục raw(không cần thiết lắm vì không dùng)
8.  tiền xử lý lần 1:
         +kiểm tra xem 1 từ điển có đủ các giá trị tittle, summary, content, category không, nếu k trả về none
         +áp dụng xóa thẻ html, các kí tự đặp biệt cho tất cả 4 chỉ số
         +hàm chạy để bắt đầu chạy và lưu vào 1 file csv
9.  tiền xử lý lần 2:
         +đọc file csv đã lưu, xóa tất cả các chỉ số hàng có giá trị trống
         +xóa bỏ tất cả các chỉ số hàng nếu nó không đạt đủ tiêu chuẩn(tránh bị ngắn quá hoặc sai nội dung)
