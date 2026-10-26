import json
import os

class Node:
    """
    Nút trong cây nhị phân tìm kiếm (BST), lưu trữ đối tượng bệnh nhân.
    """
    def __init__(self, patient):
        self.patient = patient               # Đối tượng Patient
        self.patient_id = patient.patient_id # Khóa tìm kiếm (ID bệnh nhân - khớp với models.py)
        self.left = None
        self.right = None
        self.height = 1                      # Dùng cho cây AVL (nếu muốn tối ưu cân bằng sau)


class PatientDatabase:
    """
    Lớp quản lý cơ sở dữ liệu bệnh nhân sử dụng Binary Search Tree (BST).
    Cho phép thêm, tìm kiếm, cập nhật, xóa, lưu/đọc file với tốc độ O(log n).
    """
    def __init__(self):
        self.root = None

    # -------------------------------------------------------------------------
    # 1. THÊM BỆNH NHÂN (INSERT)
    # -------------------------------------------------------------------------
    def insert(self, patient):
        """Thêm một bệnh nhân mới vào cây."""
        self.root = self._insert_recursive(self.root, patient)

    def _insert_recursive(self, node, patient):
        if node is None:
            return Node(patient)
        
        if patient.patient_id < node.patient_id:
            node.left = self._insert_recursive(node.left, patient)
        elif patient.patient_id > node.patient_id:
            node.right = self._insert_recursive(node.right, patient)
        else:
            # Nếu ID đã tồn tại, cập nhật thông tin mới vào node hiện tại
            node.patient = patient

        return node

    # -------------------------------------------------------------------------
    # 2. TÌM KIẾM BỆNH NHÂN (SEARCH)
    # -------------------------------------------------------------------------
    def search(self, patient_id):
        """Tìm kiếm bệnh nhân theo ID với độ phức tạp O(log n)."""
        return self._search_recursive(self.root, patient_id)

    def _search_recursive(self, node, patient_id):
        if node is None or node.patient_id == patient_id:
            return node.patient if node else None

        if patient_id < node.patient_id:
            return self._search_recursive(node.left, patient_id)
        return self._search_recursive(node.right, patient_id)

    # -------------------------------------------------------------------------
    # 3. CẬP NHẬT THÔNG TIN BỆNH NHÂN (UPDATE)
    # -------------------------------------------------------------------------
    def update(self, patient_id, **kwargs):
        """Cập nhật các thuộc tính của bệnh nhân theo ID."""
        patient = self.search(patient_id)
        if patient:
            for key, value in kwargs.items():
                if hasattr(patient, key):
                    setattr(patient, key, value)
            return True
        return False

    # -------------------------------------------------------------------------
    # 4. XÓA BỆNH NHÂN KHỎI CÂY (DELETE)
    # -------------------------------------------------------------------------
    def delete(self, patient_id):
        """Xóa bệnh nhân khỏi cơ sở dữ liệu dựa vào ID."""
        self.root, deleted = self._delete_recursive(self.root, patient_id)
        return deleted

    def _delete_recursive(self, node, patient_id):
        if node is None:
            return None, False

        deleted = False
        if patient_id < node.patient_id:
            node.left, deleted = self._delete_recursive(node.left, patient_id)
        elif patient_id > node.patient_id:
            node.right, deleted = self._delete_recursive(node.right, patient_id)
        else:
            deleted = True
            # Trường hợp 1: Node lá hoặc chỉ có 1 con
            if node.left is None:
                return node.right, True
            elif node.right is None:
                return node.left, True

            # Trường hợp 2: Node có 2 con -> Lấy giá trị nhỏ nhất ở cây con phải (In-order successor)
            min_larger_node = self._find_min(node.right)
            node.patient = min_larger_node.patient
            node.patient_id = min_larger_node.patient_id
            node.right, _ = self._delete_recursive(node.right, min_larger_node.patient_id)

        return node, deleted

    def _find_min(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current

    # -------------------------------------------------------------------------
    # 5. DUYỆT TẤT CẢ BỆNH NHÂN (IN-ORDER TRAVERSAL)
    # -------------------------------------------------------------------------
    def get_all_patients(self):
        """Lấy danh sách tất cả bệnh nhân sắp xếp theo ID tăng dần."""
        patients = []
        self._inorder_traversal(self.root, patients)
        return patients

    def _inorder_traversal(self, node, patients_list):
        if node:
            self._inorder_traversal(node.left, patients_list)
            patients_list.append(node.patient)
            self._inorder_traversal(node.right, patients_list)

    # -------------------------------------------------------------------------
    # 6. GHI VÀ LƯU DỮ LIỆU RA FILE (JSON PERSISTENCE)
    # -------------------------------------------------------------------------
    def save_to_file(self, filename="database.json"):
        """Lưu toàn bộ danh sách bệnh nhân xuống file JSON."""
        patients = self.get_all_patients()
        data = []
        for p in patients:
            if hasattr(p, "to_dict"):
                data.append(p.to_dict())
            else:
                data.append(vars(p))
                
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_from_file(self, patient_class, filename="database.json"):
        """Đọc dữ liệu từ file JSON và tái tạo lại cây BST."""
        if not os.path.exists(filename):
            return
        
        with open(filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for item in data:
                    patient = patient_class(**item)
                    self.insert(patient)
            except json.JSONDecodeError:
                pass
