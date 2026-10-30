# Hospital..

Hệ thống Cân bằng Hàng đợi Đa quầy Bệnh viện (Hospital Multi-Counter Queue Balancer System).

##  Cấu trúc Module & Giải thuật (DSA)
- `models.py`: Khai báo đối tượng `Patient` và `Counter` (Hàng đợi `collections.deque` FIFO).
- `triage_route.py`: Bộ định tuyến phân loại ca bệnh (3 Hàng đợi Deque: Cấp cứu, Ưu tiên, Thường) & Hoàn tác Stack LIFO.
- `balancer.py`: Bộ cân bằng tải tự động đa quầy sử dụng cấu trúc Min-Heap (`heapq`) $O(\log k)$.
- `database.py`: Cơ sở dữ liệu cây nhị phân tìm kiếm (Binary Search Tree - BST) $O(\log n)$ và hỗ trợ lưu JSON.
- `menu.py`: Bộ điều khiển trung tâm CLI Menu 10 chức năng, bộ đệm Hash Map Cache $O(1)$, thuật toán Merge Sort $O(n \log n)$ và xuất báo cáo CSV.

## Cách chạy chương trình
```bash
python3 menu.py
```

##  Kiểm thử tự động (Unit & Integration Tests)
```bash
python3 test_models.py && python3 test_triage.py && python3 test_balancer.py && python3 test_database.py && python3 test_menu.py
```
