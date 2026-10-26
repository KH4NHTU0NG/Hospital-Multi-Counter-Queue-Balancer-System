from collections import deque
from models import Patient, Counter, KIND_PRIORITY, KIND_NORMAL

QUEUE_EMERGENCY = "emergency"
QUEUE_PRIORITY = "priority"
QUEUE_NORMAL = "normal"


class TriageRouter:
    def __init__(self):
        self.emergencyQueue = deque()
        self.priorityQueue = deque()
        self.normalQueue = deque()
        self.history_stack = []

    def determine_queue_type(self, patient):
        if not isinstance(patient, Patient):
            raise TypeError("Dữ liệu đầu vào phải là đối tượng Patient")

        if patient.is_emergency or patient.severity == 5:
            return QUEUE_EMERGENCY
        elif patient.severity == 4 or patient.age >= 65 or patient.age <= 6:
            return QUEUE_PRIORITY
        else:
            return QUEUE_NORMAL

    def triage_patient(self, patient):
        if not isinstance(patient, Patient):
            raise TypeError("Chỉ nhận đối tượng Patient")

        if self._is_patient_in_queues(patient.patient_id):
            raise ValueError(f"Bệnh nhân {patient.patient_id} đã có trong hàng đợi phân loại")

        queue_type = self.determine_queue_type(patient)

        if queue_type == QUEUE_EMERGENCY:
            self.emergencyQueue.append(patient)
        elif queue_type == QUEUE_PRIORITY:
            self.priorityQueue.append(patient)
        else:
            self.normalQueue.append(patient)

        self.history_stack.append((queue_type, patient))
        return queue_type

    def get_next_patient(self):
        if self.emergencyQueue:
            return self.emergencyQueue.popleft()
        if self.priorityQueue:
            return self.priorityQueue.popleft()
        if self.normalQueue:
            return self.normalQueue.popleft()
        return None

    def get_next_for_counter_kind(self, counter_kind):
        if counter_kind == KIND_PRIORITY:
            return self.get_next_patient()
        elif counter_kind == KIND_NORMAL:
            if self.normalQueue:
                return self.normalQueue.popleft()
            if self.priorityQueue:
                return self.priorityQueue.popleft()
            if self.emergencyQueue:
                return self.emergencyQueue.popleft()
            return None
        else:
            raise ValueError("Loại quầy không hợp lệ")

    def route_next_to_counter(self, counter):
        if not isinstance(counter, Counter):
            raise TypeError("Phải truyền vào đối tượng Counter")
        if not counter.is_open:
            raise ValueError(f"Quầy {counter.counter_id} đang đóng, không thể chuyển bệnh nhân")

        if self.emergencyQueue:
            patient = self.emergencyQueue.popleft()
            counter.enqueue_front(patient)
            return patient

        patient = self.get_next_patient()
        if patient is not None:
            counter.enqueue(patient)
        return patient

    def undo_last_triage(self):
        while self.history_stack:
            queue_type, patient = self.history_stack.pop()
            target_queue = self._get_queue_by_name(queue_type)
            if patient in target_queue:
                target_queue.remove(patient)
                return patient

        raise IndexError("Không có thao tác phân loại nào có thể hoàn tác (Stack trống)")

    def total_waiting(self):
        return len(self.emergencyQueue) + len(self.priorityQueue) + len(self.normalQueue)

    def get_summary(self):
        return {
            "emergency": len(self.emergencyQueue),
            "priority": len(self.priorityQueue),
            "normal": len(self.normalQueue),
            "total": len(self.emergencyQueue) + len(self.priorityQueue) + len(self.normalQueue),
        }

    def _get_queue_by_name(self, queue_type):
        if queue_type == QUEUE_EMERGENCY:
            return self.emergencyQueue
        elif queue_type == QUEUE_PRIORITY:
            return self.priorityQueue
        return self.normalQueue

    def _is_patient_in_queues(self, patient_id):
        for q in (self.emergencyQueue, self.priorityQueue, self.normalQueue):
            for p in q:
                if p.patient_id == patient_id:
                    return True
                
        return False