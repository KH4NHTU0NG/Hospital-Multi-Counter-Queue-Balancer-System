import heapq
from models import Patient, Counter, KIND_NORMAL, KIND_PRIORITY


class Balancer:
    """Bộ cân bằng tải giữa các quầy khám sử dụng cấu trúc dữ liệu Min-Heap."""

    def __init__(self, counters=None):
        # Min-Heap lưu các quầy thường (KIND_NORMAL) đang mở (is_open == True)
        self.counter_heap = []
        # Quầy ưu tiên (hệ thống có 1 quầy ưu tiên và nhiều quầy thường)
        self.priority_counter = None
        # Từ điển quản lý toàn bộ các quầy theo counter_id để tra cứu nhanh
        self._counters = {}

        if counters:
            for counter in counters:
                self.add_counter(counter)

    @property
    def active_counters(self):
        """Tổng số quầy đang mở và hoạt động trong hệ thống."""
        return sum(1 for c in self._counters.values() if c.is_open)

    def add_counter(self, counter):
        """Thêm một quầy khám mới vào hệ thống cân bằng tải."""
        if not isinstance(counter, Counter):
            raise TypeError("Chỉ nhận đối tượng Counter")
        if counter.counter_id in self._counters:
            raise ValueError(f"Quầy {counter.counter_id} đã tồn tại trong hệ thống")

        if counter.kind == KIND_PRIORITY:
            if self.priority_counter is not None:
                raise ValueError("Hệ thống chỉ cho phép 1 quầy ưu tiên")
            self.priority_counter = counter
        else:
            if counter.is_open:
                heapq.heappush(self.counter_heap, counter)

        self._counters[counter.counter_id] = counter

    def get_counter(self, counter_id):
        """Lấy đối tượng Counter theo mã quầy."""
        if counter_id not in self._counters:
            raise ValueError(f"Không tìm thấy quầy có mã {counter_id}")
        return self._counters[counter_id]

    def least_busy_counter(self):
        """Tìm quầy thường đang mở có số người chờ ít nhất (ở đỉnh Min-Heap)."""
        # Loại bỏ các quầy đã đóng nếu còn sót ở đỉnh heap
        while self.counter_heap and not self.counter_heap[0].is_open:
            heapq.heappop(self.counter_heap)

        if not self.counter_heap:
            raise RuntimeError("Không có quầy thường nào đang mở để nhận bệnh nhân")

        return self.counter_heap[0]

    def select_least_loaded(self):
        """Alias của least_busy_counter() để tương thích với sơ đồ UML."""
        return self.least_busy_counter()

    def update_counter_load(self, counter=None):
        """Cập nhật lại Min-Heap sau khi tải hoặc trạng thái của quầy thay đổi."""
        if counter is not None and not isinstance(counter, Counter):
            raise TypeError("Chỉ nhận đối tượng Counter")

        # Giữ lại các quầy thường đang mở và tái cấu trúc Min-Heap
        self.counter_heap = [
            c for c in self._counters.values()
            if c.kind == KIND_NORMAL and c.is_open
        ]
        heapq.heapify(self.counter_heap)

    def rebalance(self):
        """Alias của update_counter_load() để tương thích với sơ đồ UML."""
        self.update_counter_load()

    def assign_patient(self, patient, to_priority=False):
        """Gán bệnh nhân vào quầy phù hợp và cập nhật lại Min-Heap.

        - Nếu to_priority=False (bệnh nhân thường): đưa vào cuối hàng của quầy
          thường đang mở có ít người chờ nhất.
        - Nếu to_priority=True (bệnh nhân ưu tiên): đưa vào quầy ưu tiên nếu
          quầy đang mở; nếu quầy ưu tiên đang đóng (gặp sự cố) thì đẩy lên đầu
          hàng của quầy thường ít người chờ nhất.
        """
        if not isinstance(patient, Patient):
            raise TypeError("Chỉ nhận đối tượng Patient")

        if to_priority:
            if self.priority_counter is not None and self.priority_counter.is_open:
                self.priority_counter.enqueue(patient)
                return self.priority_counter

            # Quầy ưu tiên chưa có hoặc đang đóng -> đưa lên đầu hàng quầy thường ít người nhất
            counter = self.least_busy_counter()
            counter.enqueue_front(patient)
            self.update_counter_load(counter)
            return counter

        # Bệnh nhân thường -> vào cuối hàng của quầy thường ít người nhất
        counter = self.least_busy_counter()
        counter.enqueue(patient)
        self.update_counter_load(counter)
        return counter

    def assign_priority_patient(self, patient):
        """Hàm hỗ trợ gán trực tiếp bệnh nhân thuộc diện ưu tiên."""
        return self.assign_patient(patient, to_priority=True)

    def serve_next(self, counter_id):
        """Gọi bệnh nhân đầu hàng của một quầy vào khám và cập nhật tải."""
        counter = self.get_counter(counter_id)
        patient = counter.serve_next()
        if patient is not None and counter.kind == KIND_NORMAL:
            self.update_counter_load(counter)
        return patient

    def close_counter(self, counter_id):
        """Đóng quầy (khi gặp sự cố) và tự động phân bổ lại bệnh nhân đang chờ.

        - Quầy thường đóng: chia từng bệnh nhân đang chờ sang các quầy thường
          còn mở theo nguyên tắc chọn quầy ít người nhất.
        - Quầy ưu tiên đóng: dồn toàn bộ bệnh nhân ưu tiên đang chờ lên đầu hàng
          của quầy thường ít người nhất (giữ nguyên thứ tự đến).
        """
        counter = self.get_counter(counter_id)
        if not counter.is_open:
            return []

        if counter.kind == KIND_NORMAL:
            # Kiểm tra còn ít nhất một quầy thường khác đang mở nếu quầy hiện tại có khách
            other_open_normals = [
                c for c in self._counters.values()
                if c.kind == KIND_NORMAL and c.is_open and c.counter_id != counter_id
            ]
            if len(counter) > 0 and not other_open_normals:
                raise RuntimeError("Không thể đóng quầy thường duy nhất đang còn bệnh nhân chờ")

            waiting_patients = counter.close()
            self.update_counter_load(counter)

            for patient in waiting_patients:
                self.assign_patient(patient, to_priority=False)
            return waiting_patients

        # Trường hợp quầy ưu tiên gặp sự cố
        waiting_priority = counter.close()
        if waiting_priority:
            target_counter = self.least_busy_counter()
            target_counter.enqueue_front_many(waiting_priority)
            self.update_counter_load(target_counter)
        return waiting_priority

    def open_counter(self, counter_id):
        """Mở lại quầy khám và đưa quầy thường trở lại vào Min-Heap."""
        counter = self.get_counter(counter_id)
        counter.open()
        if counter.kind == KIND_NORMAL:
            self.update_counter_load(counter)

    def get_all_counters(self):
        """Trả về danh sách tất cả các quầy theo thứ tự mã quầy tăng dần."""
        return [self._counters[cid] for cid in sorted(self._counters.keys())]

    def __str__(self):
        lines = [f"Balancer (Số quầy đang mở: {self.active_counters}):"]
        for counter in self.get_all_counters():
            lines.append(f"  - {counter}")
        return "\n".join(lines)
