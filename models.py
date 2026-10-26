import time
from collections import deque


STATUS_WAITING = "waiting"
STATUS_IN_SERVICE = "in_service"
STATUS_DONE = "done"
VALID_STATUS = (STATUS_WAITING, STATUS_IN_SERVICE, STATUS_DONE)

KIND_NORMAL = "normal"
KIND_PRIORITY = "priority"
VALID_KINDS = (KIND_NORMAL, KIND_PRIORITY)


class Patient:
    """Bệnh nhân: chỉ lưu dữ liệu, không tự quyết định ưu tiên hay chọn quầy."""

    def __init__(self, patient_id, name, age, severity, is_emergency=False,
                 arrival_time=None, status=STATUS_WAITING, counter_id=None):
        # Kiểm tra dữ liệu đầu vào
        if not isinstance(patient_id, str) or not patient_id.strip():
            raise ValueError("Mã bệnh nhân không được để trống")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Tên bệnh nhân không được để trống")
        if not isinstance(age, int) or isinstance(age, bool) or not (0 <= age <= 150):
            raise ValueError("Tuổi phải là số nguyên từ 0 đến 150")
        if not isinstance(severity, int) or isinstance(severity, bool) or not (1 <= severity <= 5):
            raise ValueError("Mức độ bệnh phải là số nguyên từ 1 đến 5")
        if not isinstance(is_emergency, bool):
            raise ValueError("is_emergency phải là True hoặc False")
        if status not in VALID_STATUS:
            raise ValueError("Trạng thái không hợp lệ")

        self.patient_id = patient_id.strip()
        self.name = name.strip()
        self.age = age
        self.severity = severity
        self.is_emergency = is_emergency
        self.arrival_time = arrival_time if arrival_time is not None else time.time()
        self.status = status
        self.counter_id = counter_id

    def to_dict(self):
        """Chuyển thành dictionary để An lưu và Nhân xuất dữ liệu."""
        return {
            "patient_id": self.patient_id,
            "name": self.name,
            "age": self.age,
            "severity": self.severity,
            "is_emergency": self.is_emergency,
            "arrival_time": self.arrival_time,
            "status": self.status,
            "counter_id": self.counter_id,
        }

    @classmethod
    def from_dict(cls, data):
        """Tạo lại bệnh nhân từ dictionary."""
        return cls(
            patient_id=data["patient_id"],
            name=data["name"],
            age=data["age"],
            severity=data["severity"],
            is_emergency=data.get("is_emergency", False),
            arrival_time=data.get("arrival_time"),
            status=data.get("status", STATUS_WAITING),
            counter_id=data.get("counter_id"),
        )

    def __str__(self):
        emergency = "Cấp cứu" if self.is_emergency else "Thường"
        return (f"[{self.patient_id}] {self.name}, {self.age} tuổi, "
                f"mức độ {self.severity}, {emergency}, trạng thái: {self.status}")


class Counter:
    """Quầy khám: có hàng đợi riêng. Tải của quầy = số người đang chờ."""

    def __init__(self, counter_id, kind=KIND_NORMAL):
        if not isinstance(counter_id, int) or isinstance(counter_id, bool):
            raise ValueError("Mã quầy phải là số nguyên")
        if kind not in VALID_KINDS:
            raise ValueError("Loại quầy phải là 'normal' hoặc 'priority'")

        self.counter_id = counter_id
        self.kind = kind
        self.is_open = True
        self._queue = deque()

    @property
    def load(self):
        """Tải của quầy: số bệnh nhân đang chờ."""
        return len(self._queue)

    def enqueue(self, patient):
        """Thêm bệnh nhân vào CUỐI hàng."""
        self._check_can_accept(patient)
        self._queue.append(patient)
        self._assign(patient)

    def enqueue_front(self, patient):
        """Thêm bệnh nhân vào ĐẦU hàng."""
        self._check_can_accept(patient)
        self._queue.appendleft(patient)
        self._assign(patient)

    def enqueue_front_many(self, patients):
        """Thêm nhiều bệnh nhân vào đầu hàng mà vẫn giữ đúng thứ tự ban đầu.
        Phải thêm theo thứ tự ngược lại, vì mỗi lần appendleft sẽ đẩy người vừa thêm lên đầu."""
        for patient in reversed(list(patients)):
            self.enqueue_front(patient)

    def serve_next(self):
        """Lấy bệnh nhân đầu hàng ra khám. Hàng trống thì trả về None."""
        if not self._queue:
            return None
        patient = self._queue.popleft()
        patient.status = STATUS_IN_SERVICE
        return patient

    def peek(self):
        """Xem người đầu hàng mà không lấy ra. Hàng trống thì trả về None."""
        if not self._queue:
            return None
        return self._queue[0]

    def close(self):
        """Đóng quầy, trả về danh sách người đang chờ (giữ thứ tự) để phân lại."""
        self.is_open = False
        waiting = list(self._queue)
        self._queue.clear()
        for patient in waiting:
            patient.counter_id = None
            patient.status = STATUS_WAITING
        return waiting

    def open(self):
        """Mở lại quầy."""
        self.is_open = True

    def __len__(self):
        return len(self._queue)

    def __lt__(self, other):
        """So sánh theo (tải, mã quầy) để dùng được với heapq."""
        return (self.load, self.counter_id) < (other.load, other.counter_id)

    def __str__(self):
        state = "mở" if self.is_open else "đóng"
        return f"Quầy {self.counter_id} ({self.kind}, {state}): {self.load} người chờ"

    # --- Hàm nội bộ ---
    def _check_can_accept(self, patient):
        if not isinstance(patient, Patient):
            raise TypeError("Chỉ nhận đối tượng Patient")
        if not self.is_open:
            raise ValueError(f"Quầy {self.counter_id} đang đóng, không nhận bệnh nhân")

    def _assign(self, patient):
        patient.counter_id = self.counter_id
        patient.status = STATUS_WAITING