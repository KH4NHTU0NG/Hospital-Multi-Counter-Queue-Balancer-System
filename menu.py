# ==============================================================================
# FILE: menu.py
# TÁC GIẢ: Lê Trí Nhân - SE211777 (Member 1)
# VAI TRÒ: Giao diện điều khiển chính (Main Controller / CLI Menu),
#          Quản lý Bộ đệm Bảng băm (Hashmap / Dictionary Cache),
#          Thuật toán Sắp xếp Merge Sort, Thống kê & Xuất/Nhập File.
# ==============================================================================

import csv
import os
from datetime import datetime

# Import từ 4 module của các thành viên trong nhóm
from models import (
    Patient,
    Counter,
    STATUS_WAITING,
    STATUS_IN_SERVICE,
    STATUS_DONE,
    KIND_NORMAL,
    KIND_PRIORITY,
)
from triage_route import (
    TriageRouter,
    QUEUE_EMERGENCY,
    QUEUE_PRIORITY,
    QUEUE_NORMAL,
)
from balancer import Balancer
from database import PatientDatabase

# Tương thích an toàn cho lớp Patient với database.py (nếu dùng patient.id)
if not hasattr(Patient, "id"):
    Patient.id = property(lambda self: self.patient_id)
if not hasattr(Patient, "patient"):
    Patient.patient = property(lambda self: self)


class HospitalQueueSystem:
    """
    Lớp điều khiển trung tâm tích hợp toàn bộ 4 module:
    - models.py (Kim - Member 2): Patient, Counter
    - triage_route.py (Tường - Member 3): TriageRouter (3 Deque + History Stack)
    - balancer.py (Dương - Member 4): Balancer (Min-Heap cân bằng tải quầy)
    - database.py (An - Member 5): PatientDatabase (Cây nhị phân tìm kiếm BST)
    """

    def __init__(self, init_default_counters=True):
        # 1. Khởi tạo các bộ xử lý từ Member 3, 4, 5
        self.router = TriageRouter()
        self.balancer = Balancer()
        self.db = PatientDatabase()

        # 2. Cấu trúc dữ liệu của Member 1 (Nhân): Hashmaps / Dictionaries O(1)
        # Lưu trữ toàn bộ bệnh nhân theo mã patient_id để truy xuất tức thời O(1)
        self.patient_cache = {}
        # Lưu bệnh nhân đang trong phòng khám của từng quầy: {counter_id: Patient}
        self.in_service_map = {}
        # Lưu nhãn phân loại ban đầu của từng bệnh nhân: {patient_id: queue_type}
        self.triage_tag_map = {}
        # Lưu thống kê hệ thống theo thời gian thực O(1)
        self.stats_cache = {
            "total_registered": 0,
            "emergency_count": 0,
            "priority_count": 0,
            "normal_count": 0,
            "dispatched_count": 0,
            "discharged_count": 0,
            "undo_count": 0,
        }

        if init_default_counters:
            self._seed_default_counters()

    def _seed_default_counters(self):
        """Khởi tạo mặc định 1 quầy ưu tiên (Quầy 1) và 2 quầy thường (Quầy 2, 3)."""
        default_setup = [
            Counter(1, KIND_PRIORITY),
            Counter(2, KIND_NORMAL),
            Counter(3, KIND_NORMAL),
        ]
        for counter in default_setup:
            self.balancer.add_counter(counter)
            self.in_service_map[counter.counter_id] = None

    # ==========================================================================
    # THUẬT TOÁN SẮP XẾP MERGE SORT O(N log N) (Phục vụ Báo cáo & Hiển thị)
    # ==========================================================================
    def merge_sort_patients(self, patients_list, key_func, reverse=False):
        """
        Sắp xếp danh sách đối tượng Patient bằng thuật toán Merge Sort O(n log n).
        Hỗ trợ sắp xếp tăng dần (reverse=False) hoặc giảm dần (reverse=True).
        """
        if len(patients_list) <= 1:
            return list(patients_list)

        mid = len(patients_list) // 2
        left_half = self.merge_sort_patients(patients_list[:mid], key_func, reverse)
        right_half = self.merge_sort_patients(patients_list[mid:], key_func, reverse)

        return self._merge(left_half, right_half, key_func, reverse)

    def _merge(self, left, right, key_func, reverse):
        merged = []
        i = j = 0
        while i < len(left) and j < len(right):
            left_key = key_func(left[i])
            right_key = key_func(right[j])
            if not reverse:
                condition = left_key <= right_key
            else:
                condition = left_key >= right_key

            if condition:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1

        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged

    # ==========================================================================
    # CHỨC NĂNG 1: TIẾP NHẬN & PHÂN LOẠI BỆNH NHÂN (Kết nối Member 2, 3, 5)
    # ==========================================================================
    def register_patient(self, patient_id, name, age, severity, is_emergency=False):
        """
        Tạo đối tượng Patient, kiểm tra trùng mã O(1) trên Hashmap & O(log n) trên BST,
        lưu vào Database và đẩy vào TriageRouter để phân loại hàng đợi.
        """
        clean_id = patient_id.strip().upper() if isinstance(patient_id, str) else ""
        if clean_id in self.patient_cache or self.db.search(clean_id) is not None:
            raise ValueError(f"Mã bệnh nhân '{clean_id}' đã tồn tại trong hệ thống")

        # Khởi tạo đối tượng Patient (models.py - Kim)
        patient = Patient(
            patient_id=clean_id,
            name=name,
            age=age,
            severity=severity,
            is_emergency=is_emergency,
        )

        # Đưa vào hàng đợi phân loại (triage_route.py - Tường)
        queue_type = self.router.triage_patient(patient)

        # Lưu trữ vào BST Database (database.py - An) và Hashmap Cache (Nhân)
        self.db.insert(patient)
        self.patient_cache[clean_id] = patient
        self.triage_tag_map[clean_id] = queue_type

        # Cập nhật bộ đếm thống kê O(1)
        self.stats_cache["total_registered"] += 1
        if queue_type == QUEUE_EMERGENCY:
            self.stats_cache["emergency_count"] += 1
        elif queue_type == QUEUE_PRIORITY:
            self.stats_cache["priority_count"] += 1
        else:
            self.stats_cache["normal_count"] += 1

        return patient, queue_type

    # ==========================================================================
    # CHỨC NĂNG 2: HOÀN TÁC PHÂN LOẠI GẦN NHẤT - STACK LIFO (Kết nối Member 3, 5)
    # ==========================================================================
    def undo_last_registration(self):
        """
        Hoàn tác thao tác tiếp nhận gần nhất bằng Stack LIFO của TriageRouter,
        đồng thời xóa bản ghi vừa nhập nhầm khỏi Cache và BST Database.
        """
        undone_patient = self.router.undo_last_triage()
        pid = undone_patient.patient_id
        q_type = self.triage_tag_map.pop(pid, None)

        self.patient_cache.pop(pid, None)
        self.db.delete(pid)

        self.stats_cache["total_registered"] = max(0, self.stats_cache["total_registered"] - 1)
        if q_type == QUEUE_EMERGENCY:
            self.stats_cache["emergency_count"] = max(0, self.stats_cache["emergency_count"] - 1)
        elif q_type == QUEUE_PRIORITY:
            self.stats_cache["priority_count"] = max(0, self.stats_cache["priority_count"] - 1)
        elif q_type == QUEUE_NORMAL:
            self.stats_cache["normal_count"] = max(0, self.stats_cache["normal_count"] - 1)
        self.stats_cache["undo_count"] += 1

        return undone_patient, q_type

    # ==========================================================================
    # CHỨC NĂNG 3: ĐIỀU PHỐI TỪ HÀNG ĐỢI PHÂN LOẠI SANG QUẦY KHÁM (Member 3 & 4)
    # ==========================================================================
    def dispatch_next_to_counter(self):
        """
        Lấy 1 bệnh nhân ưu tiên cao nhất từ TriageRouter (Emergency -> Priority -> Normal)
        và phân bổ vào quầy phù hợp thông qua bộ cân bằng tải Min-Heap (Balancer).
        Bảo toàn dữ liệu: Không làm mất bệnh nhân nếu tất cả quầy gặp sự cố đóng.
        """
        if self.router.total_waiting() == 0:
            return None, None, None

        has_open_normal = any(
            c.kind == KIND_NORMAL and c.is_open for c in self.balancer._counters.values()
        )
        priority_available = (
            self.balancer.priority_counter is not None
            and self.balancer.priority_counter.is_open
        )

        if not has_open_normal and not priority_available:
            raise RuntimeError("Tất cả các quầy khám đều đang đóng, không thể điều phối bệnh nhân")

        # Xác định hàng đợi của bệnh nhân chuẩn bị được lấy ra
        if self.router.emergencyQueue:
            source_queue = QUEUE_EMERGENCY
            if priority_available and self.balancer.priority_counter.load == 0:
                patient = self.router.emergencyQueue.popleft()
                counter = self.balancer.priority_counter
                counter.enqueue_front(patient)
            elif has_open_normal:
                patient = self.router.emergencyQueue.popleft()
                counter = self.balancer.least_busy_counter()
                counter.enqueue_front(patient)
                self.balancer.update_counter_load(counter)
            elif priority_available:
                patient = self.router.emergencyQueue.popleft()
                counter = self.balancer.priority_counter
                counter.enqueue_front(patient)
            else:
                raise RuntimeError("Không có quầy nào khả dụng để nhận bệnh nhân cấp cứu")

        elif self.router.priorityQueue:
            source_queue = QUEUE_PRIORITY
            if not priority_available and not has_open_normal:
                raise RuntimeError("Không có quầy nào khả dụng để nhận bệnh nhân ưu tiên")
            patient = self.router.priorityQueue.popleft()
            try:
                counter = self.balancer.assign_priority_patient(patient)
            except Exception:
                self.router.priorityQueue.appendleft(patient)
                raise

        else:
            source_queue = QUEUE_NORMAL
            if not has_open_normal:
                raise RuntimeError("Không có quầy thường nào đang mở để nhận bệnh nhân thường")
            patient = self.router.normalQueue.popleft()
            try:
                counter = self.balancer.assign_patient(patient, to_priority=False)
            except Exception:
                self.router.normalQueue.appendleft(patient)
                raise

        self.stats_cache["dispatched_count"] += 1
        return patient, counter, source_queue

    def dispatch_all_waiting_to_counters(self):
        """Điều phối toàn bộ bệnh nhân đang chờ ở khâu phân loại sang các quầy khám."""
        results = []
        while self.router.total_waiting() > 0:
            patient, counter, source_queue = self.dispatch_next_to_counter()
            if patient is None:
                break
            results.append((patient, counter, source_queue))
        return results

    # ==========================================================================
    # CHỨC NĂNG 4: GỌI KHÁM & XUẤT VIỆN TẠI QUẦY (Kết nối Member 2, 4, 5)
    # ==========================================================================
    def call_next_patient_at_counter(self, counter_id):
        """
        Gọi bệnh nhân đầu hàng tại quầy counter_id vào khám (STATUS_IN_SERVICE).
        Nếu tại quầy đang có bệnh nhân khám trước đó thì tự động hoàn tất xuất viện
        (STATUS_DONE) cho bệnh nhân cũ trước khi gọi người mới.
        """
        counter = self.balancer.get_counter(counter_id)
        if not counter.is_open:
            raise ValueError(f"Quầy {counter_id} đang đóng, không thể gọi khám")

        previous_finished = None
        current_in_service = self.in_service_map.get(counter_id)
        if current_in_service is not None:
            current_in_service.status = STATUS_DONE
            self.db.update(current_in_service.patient_id, status=STATUS_DONE)
            self.stats_cache["discharged_count"] += 1
            previous_finished = current_in_service
            self.in_service_map[counter_id] = None

        next_patient = self.balancer.serve_next(counter_id)
        if next_patient is not None:
            self.in_service_map[counter_id] = next_patient
            self.db.update(
                next_patient.patient_id,
                status=STATUS_IN_SERVICE,
                counter_id=counter_id,
            )

        return next_patient, previous_finished

    def discharge_current_at_counter(self, counter_id):
        """Hoàn tất khám và xuất viện (STATUS_DONE) cho bệnh nhân đang khám tại quầy."""
        self.balancer.get_counter(counter_id)  # Kiểm tra mã quầy hợp lệ
        patient = self.in_service_map.get(counter_id)
        if patient is None:
            return None

        patient.status = STATUS_DONE
        self.in_service_map[counter_id] = None
        self.db.update(patient.patient_id, status=STATUS_DONE)
        self.stats_cache["discharged_count"] += 1
        return patient

    # ==========================================================================
    # CHỨC NĂNG 5: QUẢN LÝ QUẦY KHÁM (THÊM / ĐÓNG SỰ CỐ / MỞ LẠI)
    # ==========================================================================
    def add_counter(self, counter_id, kind=KIND_NORMAL):
        new_counter = Counter(counter_id, kind=kind)
        self.balancer.add_counter(new_counter)
        self.in_service_map[counter_id] = None
        return new_counter

    def close_counter(self, counter_id):
        # Nếu quầy đang có bệnh nhân đang khám dở, hoàn tất cho bệnh nhân đó
        if self.in_service_map.get(counter_id) is not None:
            self.discharge_current_at_counter(counter_id)
        moved_patients = self.balancer.close_counter(counter_id)
        return moved_patients

    def open_counter(self, counter_id):
        self.balancer.open_counter(counter_id)
        return self.balancer.get_counter(counter_id)

    # ==========================================================================
    # CHỨC NĂNG 6: TÌM KIẾM, CẬP NHẬT & XÓA BỆNH NHÂN (Hashmap O(1) + BST O(log n))
    # ==========================================================================
    def find_patient(self, patient_id):
        """Tìm bệnh nhân qua bộ đệm Hashmap O(1) hoặc Cây tìm kiếm nhị phân BST O(log n)."""
        clean_id = patient_id.strip().upper()
        if clean_id in self.patient_cache:
            return self.patient_cache[clean_id], "Hashmap Cache O(1)"
        found = self.db.search(clean_id)
        if found is not None:
            self.patient_cache[clean_id] = found
            return found, "BST Database O(log n)"
        return None, None

    def update_patient_record(self, patient_id, name=None, age=None, severity=None, is_emergency=None):
        clean_id = patient_id.strip().upper()
        patient, _ = self.find_patient(clean_id)
        if patient is None:
            raise ValueError(f"Không tìm thấy bệnh nhân có mã '{clean_id}'")

        updates = {}
        if name is not None and name.strip():
            updates["name"] = name.strip()
        if age is not None:
            if not isinstance(age, int) or not (0 <= age <= 150):
                raise ValueError("Tuổi phải là số nguyên từ 0 đến 150")
            updates["age"] = age
        if severity is not None:
            if not isinstance(severity, int) or not (1 <= severity <= 5):
                raise ValueError("Mức độ bệnh phải là số nguyên từ 1 đến 5")
            updates["severity"] = severity
        if is_emergency is not None:
            updates["is_emergency"] = bool(is_emergency)

        self.db.update(clean_id, **updates)
        return patient

    def delete_patient_record(self, patient_id):
        """Xóa hồ sơ bệnh nhân (chỉ cho phép xóa khi không còn nằm trong hàng chờ)."""
        clean_id = patient_id.strip().upper()
        patient, _ = self.find_patient(clean_id)
        if patient is None:
            return False

        # Không xóa nếu bệnh nhân đang nằm trong hàng đợi phân loại hoặc hàng đợi quầy
        if self.router._is_patient_in_queues(clean_id):
            raise RuntimeError("Không thể xóa bệnh nhân đang nằm trong hàng đợi phân loại (hãy dùng Hoàn tác)")
        for c in self.balancer.get_all_counters():
            if any(p.patient_id == clean_id for p in c._queue):
                raise RuntimeError(f"Không thể xóa bệnh nhân đang xếp hàng tại Quầy {c.counter_id}")
        for cid, p in self.in_service_map.items():
            if p is not None and p.patient_id == clean_id:
                raise RuntimeError(f"Không thể xóa bệnh nhân đang khám tại Quầy {cid}")

        self.patient_cache.pop(clean_id, None)
        self.triage_tag_map.pop(clean_id, None)
        return self.db.delete(clean_id)

    # ==========================================================================
    # CHỨC NĂNG 7: LƯU / ĐỌC JSON & XUẤT BÁO CÁO CSV
    # ==========================================================================
    def save_all_data(self, json_filename="database.json", csv_filename="patients_report.csv"):
        """Lưu cây BST ra file JSON (database.py) và xuất bảng thống kê ra file CSV."""
        self.db.save_to_file(json_filename)
        patients = self.db.get_all_patients()

        with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "patient_id", "name", "age", "severity",
                "is_emergency", "triage_group", "status", "counter_id", "arrival_time"
            ])
            for p in patients:
                t_group = self.triage_tag_map.get(p.patient_id, "N/A")
                arr_str = datetime.fromtimestamp(p.arrival_time).strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([
                    p.patient_id, p.name, p.age, p.severity,
                    p.is_emergency, t_group, p.status, p.counter_id, arr_str
                ])
        return len(patients)

    def load_data_from_json(self, json_filename="database.json"):
        """Đọc dữ liệu bệnh nhân từ file JSON vào cây BST và đồng bộ bộ đệm Hashmap & Thống kê."""
        if not os.path.exists(json_filename):
            return 0
        self.db.load_from_file(Patient, json_filename)
        all_patients = self.db.get_all_patients()
        for p in all_patients:
            self.patient_cache[p.patient_id] = p
            q_type = self.router.determine_queue_type(p)
            self.triage_tag_map[p.patient_id] = q_type
            self.stats_cache["total_registered"] += 1
            if q_type == QUEUE_EMERGENCY:
                self.stats_cache["emergency_count"] += 1
            elif q_type == QUEUE_PRIORITY:
                self.stats_cache["priority_count"] += 1
            else:
                self.stats_cache["normal_count"] += 1
            if p.status == STATUS_DONE:
                self.stats_cache["discharged_count"] += 1
            elif p.status == STATUS_IN_SERVICE:
                self.stats_cache["dispatched_count"] += 1
        return len(all_patients)

    # ==========================================================================
    # CHỨC NĂNG 8: NẠP DỮ LIỆU MẪU TỰ ĐỘNG (DEMO / KIỂM THỬ NHANH)
    # ==========================================================================
    def seed_sample_patients(self):
        """Tạo 6 bệnh nhân mẫu thuộc đủ 3 nhóm (Thường, Ưu tiên, Cấp cứu) để demo."""
        sample_data = [
            ("BN01", "Nguyễn Văn An", 28, 2, False),   # Normal
            ("BN02", "Trần Thị Bình", 72, 2, False),   # Priority (Người cao tuổi >= 65)
            ("BN03", "Lê Hoàng Cường", 35, 4, False),  # Priority (Mức độ nặng == 4)
            ("BN04", "Phạm Gia Bảo", 5, 2, False),     # Priority (Trẻ nhỏ <= 6)
            ("BN05", "Hoàng Minh Đức", 42, 3, True),   # Emergency (Cờ cấp cứu True)
            ("BN06", "Võ Thị Hoa", 50, 5, False),      # Emergency (Mức độ nguy kịch == 5)
        ]
        added = []
        for pid, name, age, sev, emg in sample_data:
            if pid not in self.patient_cache and self.db.search(pid) is None:
                p, q_type = self.register_patient(pid, name, age, sev, emg)
                added.append((p, q_type))
        return added

    # ==========================================================================
    # GIAO DIỆN DÒNG LỆNH (CLI MENU INTERACTION)
    # ==========================================================================
    def print_dashboard(self):
        print("\n" + "=" * 78)
        print("          BẢNG ĐIỀU KHIỂN TRỰC TIẾP - HOSPITAL MULTI-COUNTER BALANCER")
        print("=" * 78)
        summary = self.router.get_summary()
        print("1. HÀNG ĐỢI PHÂN LOẠI (TriageRouter - Member 3):")
        print(f"   - Hàng Cấp Cứu (Emergency Queue) : {summary['emergency']} bệnh nhân "
              f"{[p.patient_id for p in self.router.emergencyQueue]}")
        print(f"   - Hàng Ưu Tiên (Priority Queue)  : {summary['priority']} bệnh nhân "
              f"{[p.patient_id for p in self.router.priorityQueue]}")
        print(f"   - Hàng Thường  (Normal Queue)    : {summary['normal']} bệnh nhân "
              f"{[p.patient_id for p in self.router.normalQueue]}")
        print(f"   => Tổng đang chờ phân bổ quầy    : {summary['total']} bệnh nhân")
        print("-" * 78)
        print("2. TRẠNG THÁI CÁC QUẦY KHÁM (Balancer Min-Heap - Member 2 & Member 4):")
        for c in self.balancer.get_all_counters():
            state_str = "ĐANG MỞ " if c.is_open else "ĐÃ ĐÓNG"
            kind_str = "ƯU TIÊN" if c.kind == KIND_PRIORITY else "THƯỜNG "
            in_srv = self.in_service_map.get(c.counter_id)
            srv_str = f"{in_srv.patient_id} ({in_srv.name})" if in_srv else "Trống"
            q_ids = [p.patient_id for p in c._queue]
            print(f"   * Quầy {c.counter_id:<2} [{kind_str} | {state_str}] "
                  f"| Đang khám: {srv_str:<22} | Chờ ({c.load}): {q_ids}")
        print("-" * 78)
        print("3. THỐNG KÊ BỘ ĐỆM (Hashmap Stats Cache - Member 1):")
        print(f"   - Tổng tiếp nhận : {self.stats_cache['total_registered']} "
              f"(Cấp cứu: {self.stats_cache['emergency_count']}, "
              f"Ưu tiên: {self.stats_cache['priority_count']}, "
              f"Thường: {self.stats_cache['normal_count']})")
        print(f"   - Đã chuyển quầy : {self.stats_cache['dispatched_count']} | "
              f"Đã khám xong (Done): {self.stats_cache['discharged_count']} | "
              f"Hoàn tác (Undo): {self.stats_cache['undo_count']}")
        print("=" * 78)

    def _cli_register_patient(self):
        print("\n--- 1. TIẾP NHẬN & PHÂN LOẠI BỆNH NHÂN MỚI ---")
        pid = input("Nhập Mã bệnh nhân (VD: BN01): ").strip().upper()
        name = input("Nhập Họ và Tên bệnh nhân: ").strip()
        try:
            age = int(input("Nhập Tuổi (0 - 150): ").strip())
            severity = int(input("Nhập Mức độ bệnh (1: Nhẹ -> 5: Nguy kịch): ").strip())
        except ValueError:
            print("[!] Lỗi: Tuổi và Mức độ bệnh phải là số nguyên!")
            return

        emg_ans = input("Có phải ca Cấp cứu khẩn cấp không? (y/n): ").strip().lower()
        is_emergency = emg_ans in ("y", "yes", "c", "co", "1")

        try:
            patient, q_type = self.register_patient(pid, name, age, severity, is_emergency)
            print(f"[+] Đã tiếp nhận: {patient}")
            print(f"[+] Đã đưa vào hàng đợi phân loại: '{q_type.upper()}' và lưu vào BST Database.")
        except (ValueError, TypeError) as e:
            print(f"[!] Lỗi dữ liệu: {e}")

    def _cli_undo_triage(self):
        print("\n--- 2. HOÀN TÁC THAO TÁC TIẾP NHẬN GẦN NHẤT (STACK UNDO) ---")
        try:
            patient, q_type = self.undo_last_registration()
            print(f"[+] Đã hoàn tác thành công bệnh nhân [{patient.patient_id}] {patient.name} "
                  f"khỏi hàng đợi '{q_type}' và xóa khỏi BST Database.")
        except IndexError as e:
            print(f"[!] {e}")

    def _cli_dispatch_to_counters(self):
        print("\n--- 3. ĐIỀU PHỐI BỆNH NHÂN TỪ TRIAGE SANG QUẦY KHÁM ---")
        print("1. Điều phối 1 bệnh nhân tiếp theo (theo thứ tự ưu tiên cao nhất)")
        print("2. Điều phối TẤT CẢ bệnh nhân đang chờ sang các quầy khám")
        sub = input("Chọn (1/2): ").strip()
        try:
            if sub == "1":
                patient, counter, src = self.dispatch_next_to_counter()
                if patient is None:
                    print("[i] Hàng đợi phân loại hiện đang trống.")
                else:
                    order = list(counter._queue).index(patient) + 1 if patient in counter._queue else counter.load
                    print(f"[+] Đã chuyển [{patient.patient_id}] {patient.name} (từ hàng {src}) "
                          f"--> Quầy {counter.counter_id} ({counter.kind}, thứ tự trong quầy: {order}).")
            elif sub == "2":
                results = self.dispatch_all_waiting_to_counters()
                if not results:
                    print("[i] Hàng đợi phân loại hiện đang trống.")
                else:
                    print(f"[+] Đã điều phối {len(results)} bệnh nhân sang các quầy:")
                    for p, c, src in results:
                        order = list(c._queue).index(p) + 1 if p in c._queue else "-"
                        print(f"    - [{p.patient_id}] {p.name} ({src}) --> Quầy {c.counter_id} (Thứ tự trong quầy: {order})")
            else:
                print("[!] Lựa chọn không hợp lệ.")
        except Exception as e:
            print(f"[!] Lỗi khi điều phối: {e}")

    def _cli_serve_and_discharge(self):
        print("\n--- 4. GỌI KHÁM TIẾP THEO / HOÀN TẤT KHÁM TẠI QUẦY ---")
        print("1. Gọi bệnh nhân tiếp theo vào khám tại một quầy (serve_next)")
        print("2. Hoàn tất khám & xuất viện cho bệnh nhân đang khám tại quầy")
        sub = input("Chọn (1/2): ").strip()
        if sub not in ("1", "2"):
            print("[!] Lựa chọn không hợp lệ.")
            return

        try:
            cid = int(input("Nhập Mã quầy (số nguyên, VD: 1, 2, 3): ").strip())
        except ValueError:
            print("[!] Lỗi: Mã quầy phải là số nguyên!")
            return

        try:
            if sub == "1":
                next_p, prev_p = self.call_next_patient_at_counter(cid)
                if prev_p is not None:
                    print(f"[✓] Bệnh nhân trước đó [{prev_p.patient_id}] {prev_p.name} đã khám xong (STATUS: done).")
                if next_p is not None:
                    print(f"[+] Quầy {cid} đang khám cho: [{next_p.patient_id}] {next_p.name} (STATUS: in_service).")
                else:
                    print(f"[i] Hàng chờ của Quầy {cid} hiện đang trống.")
            elif sub == "2":
                done_p = self.discharge_current_at_counter(cid)
                if done_p is not None:
                    print(f"[✓] Đã hoàn tất khám & xuất viện cho [{done_p.patient_id}] {done_p.name} tại Quầy {cid}.")
                else:
                    print(f"[i] Quầy {cid} hiện không có bệnh nhân nào đang khám.")
        except Exception as e:
            print(f"[!] Lỗi: {e}")

    def _cli_manage_counters(self):
        print("\n--- 5. QUẢN LÝ QUẦY KHÁM & XỬ LÝ SỰ CỐ (MIN-HEAP BALANCER) ---")
        print("1. Mở thêm quầy khám mới (add_counter)")
        print("2. Đóng quầy do sự cố & tự động chia lại bệnh nhân (close_counter)")
        print("3. Mở lại quầy sau sự cố (open_counter)")
        sub = input("Chọn (1/2/3): ").strip()
        if sub not in ("1", "2", "3"):
            print("[!] Lựa chọn không hợp lệ.")
            return

        try:
            cid = int(input("Nhập Mã quầy (số nguyên): ").strip())
        except ValueError:
            print("[!] Lỗi: Mã quầy phải là số nguyên!")
            return

        try:
            if sub == "1":
                k_ans = input("Loại quầy - (N)ormal hay (P)riority? [Mặc định N]: ").strip().lower()
                kind = KIND_PRIORITY if k_ans == "p" else KIND_NORMAL
                c = self.add_counter(cid, kind=kind)
                print(f"[+] Đã thêm thành công: {c}")
            elif sub == "2":
                moved = self.close_counter(cid)
                print(f"[+] Đã đóng Quầy {cid}. Đã tự động điều chuyển {len(moved)} bệnh nhân sang quầy khác:")
                for p in moved:
                    print(f"    -> [{p.patient_id}] {p.name} chuyển sang Quầy {p.counter_id}")
            elif sub == "3":
                c = self.open_counter(cid)
                print(f"[+] Đã mở lại thành công: {c}")
        except Exception as e:
            print(f"[!] Lỗi quản lý quầy: {e}")

    def _cli_search_update_delete(self):
        print("\n--- 6. TÌM KIẾM, CẬP NHẬT & XÓA HỒ SƠ BỆNH NHÂN (BST & HASHMAP) ---")
        print("1. Tìm kiếm bệnh nhân theo Mã ID")
        print("2. Cập nhật thông tin bệnh nhân")
        print("3. Xóa hồ sơ bệnh nhân")
        sub = input("Chọn (1/2/3): ").strip()
        pid = input("Nhập Mã bệnh nhân (VD: BN01): ").strip().upper()

        try:
            if sub == "1":
                patient, source = self.find_patient(pid)
                if patient:
                    print(f"[+] Tìm thấy từ {source}:")
                    print(f"    {patient} | Quầy: {patient.counter_id}")
                else:
                    print(f"[!] Không tìm thấy bệnh nhân có mã '{pid}'.")
            elif sub == "2":
                patient, _ = self.find_patient(pid)
                if not patient:
                    print(f"[!] Không tìm thấy bệnh nhân '{pid}'.")
                    return
                print("Thông tin hiện tại:", patient)
                new_name = input(f"Tên mới (Enter để giữ '{patient.name}'): ").strip()
                age_str = input(f"Tuổi mới (Enter để giữ {patient.age}): ").strip()
                sev_str = input(f"Mức độ bệnh mới 1-5 (Enter để giữ {patient.severity}): ").strip()

                try:
                    new_age = int(age_str) if age_str else None
                    new_sev = int(sev_str) if sev_str else None
                except ValueError:
                    print("[!] Lỗi: Tuổi và Mức độ bệnh phải là số nguyên!")
                    return

                updated = self.update_patient_record(
                    pid,
                    name=new_name if new_name else None,
                    age=new_age,
                    severity=new_sev,
                )
                print(f"[+] Đã cập nhật thành công: {updated}")
            elif sub == "3":
                if self.delete_patient_record(pid):
                    print(f"[+] Đã xóa hồ sơ bệnh nhân '{pid}' khỏi Hashmap Cache và BST Database.")
                else:
                    print(f"[!] Không tìm thấy bệnh nhân '{pid}'.")
            else:
                print("[!] Lựa chọn không hợp lệ.")
        except Exception as e:
            print(f"[!] Lỗi: {e}")

    def _cli_view_and_sort(self):
        print("\n--- 7. XEM DANH SÁCH & SẮP XẾP BỆNH NHÂN (MERGE SORT O(N log N)) ---")
        patients = self.db.get_all_patients()
        if not patients:
            print("[i] Cơ sở dữ liệu hiện chưa có bệnh nhân nào.")
            return

        print("Tiêu chí sắp xếp:")
        print("1. Theo Mã bệnh nhân (patient_id - Duyệt In-order BST / Merge Sort)")
        print("2. Theo Độ tuổi (age)")
        print("3. Theo Mức độ bệnh (severity)")
        print("4. Theo Thời gian đến (arrival_time)")
        s_key = input("Chọn tiêu chí (1-4) [Mặc định 1]: ").strip() or "1"
        ord_ans = input("Thứ tự: (T)ăng dần hay (G)iảm dần? [Mặc định T]: ").strip().upper()
        reverse = ord_ans == "G"

        if s_key == "2":
            sorted_list = self.merge_sort_patients(patients, key_func=lambda p: p.age, reverse=reverse)
        elif s_key == "3":
            sorted_list = self.merge_sort_patients(patients, key_func=lambda p: p.severity, reverse=reverse)
        elif s_key == "4":
            sorted_list = self.merge_sort_patients(patients, key_func=lambda p: p.arrival_time, reverse=reverse)
        else:
            sorted_list = self.merge_sort_patients(patients, key_func=lambda p: p.patient_id, reverse=reverse)

        print("\n" + "-" * 86)
        print(f"{'Mã BN':<8} {'Họ và Tên':<22} {'Tuổi':<6} {'Mức độ':<8} "
              f"{'Cấp cứu':<10} {'Phân loại':<12} {'Trạng thái':<12} {'Quầy'}")
        print("-" * 86)
        for p in sorted_list:
            emg_str = "Có" if p.is_emergency else "Không"
            t_tag = self.triage_tag_map.get(p.patient_id, "N/A")
            cid_str = str(p.counter_id) if p.counter_id is not None else "-"
            print(f"{p.patient_id:<8} {p.name:<22} {p.age:<6} {p.severity:<8} "
                  f"{emg_str:<10} {t_tag:<12} {p.status:<12} {cid_str}")
        print("-" * 86)

    def _cli_file_operations(self):
        print("\n--- 9. LƯU / ĐỌC DỮ LIỆU FILE (JSON & CSV) ---")
        print("1. Lưu dữ liệu xuống database.json và xuất báo cáo patients_report.csv")
        print("2. Đọc dữ liệu bệnh nhân từ file database.json vào BST")
        sub = input("Chọn (1/2): ").strip()
        try:
            if sub == "1":
                count = self.save_all_data()
                print(f"[+] Đã lưu {count} hồ sơ bệnh nhân vào 'database.json' và 'patients_report.csv'.")
            elif sub == "2":
                count = self.load_data_from_json()
                print(f"[+] Đã nạp {count} hồ sơ bệnh nhân từ 'database.json' vào BST và Hashmap Cache.")
            else:
                print("[!] Lựa chọn không hợp lệ.")
        except Exception as e:
            print(f"[!] Lỗi thao tác file: {e}")

    def run(self):
        """Vòng lặp giao diện điều khiển chính của chương trình."""
        while True:
            print("\n" + "=" * 68)
            print("      HỆ THỐNG CÂN BẰNG HÀNG ĐỢI ĐA QUẦY BỆNH VIỆN (GROUP 2)")
            print("=" * 68)
            print(" 1. Tiếp nhận & Phân loại bệnh nhân mới (TriageRouter + BST)")
            print(" 2. Hoàn tác thao tác tiếp nhận gần nhất (Stack LIFO Undo)")
            print(" 3. Điều phối bệnh nhân từ Triage sang Quầy khám (Min-Heap Balancer)")
            print(" 4. Gọi khám tiếp theo / Hoàn tất khám tại Quầy (Serve & Discharge)")
            print(" 5. Quản lý Quầy khám: Thêm quầy / Đóng sự cố / Mở lại quầy")
            print(" 6. Tìm kiếm, Cập nhật & Xóa hồ sơ bệnh nhân (Hashmap O(1) & BST)")
            print(" 7. Xem danh sách & Sắp xếp hồ sơ bệnh nhân (Merge Sort O(n log n))")
            print(" 8. Xem Bảng điều khiển trực tiếp & Thống kê (Live Dashboard)")
            print(" 9. Lưu / Đọc dữ liệu File (JSON Persistence & CSV Export)")
            print("10. Nạp nhanh 6 bệnh nhân mẫu (Demo / Testing)")
            print(" 0. Thoát chương trình")
            print("=" * 68)

            choice = input("Nhập lựa chọn của bạn (0 - 10): ").strip()
            if choice == "1":
                self._cli_register_patient()
            elif choice == "2":
                self._cli_undo_triage()
            elif choice == "3":
                self._cli_dispatch_to_counters()
            elif choice == "4":
                self._cli_serve_and_discharge()
            elif choice == "5":
                self._cli_manage_counters()
            elif choice == "6":
                self._cli_search_update_delete()
            elif choice == "7":
                self._cli_view_and_sort()
            elif choice == "8":
                self.print_dashboard()
            elif choice == "9":
                self._cli_file_operations()
            elif choice == "10":
                added = self.seed_sample_patients()
                print(f"[+] Đã nạp {len(added)} bệnh nhân mẫu vào hệ thống!")
                self.print_dashboard()
            elif choice == "0":
                print("Cảm ơn đã sử dụng Hệ thống Cân bằng Hàng đợi Bệnh viện. Tạm biệt!")
                break
            else:
                print("[!] Lựa chọn không hợp lệ, vui lòng chọn từ 0 đến 10.")


if __name__ == "__main__":
    app = HospitalQueueSystem()
    app.run()
