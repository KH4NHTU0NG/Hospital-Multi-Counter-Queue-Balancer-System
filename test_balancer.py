# ==============================================================================
# FILE: test_balancer.py
# TÁC GIẢ: Member 4 (Balancer Module)
# MỤC ĐÍCH: Kiểm thử đơn vị cho bộ cân bằng tải Min-Heap (balancer.py)
# ==============================================================================

from models import Patient, Counter, KIND_NORMAL, KIND_PRIORITY
from balancer import Balancer


def run_tests():
    print("--- 1. KIỂM THỬ KHỞI TẠO & THÊM QUẦY ---")
    b = Balancer()
    c1 = Counter(1, KIND_PRIORITY)
    c2 = Counter(2, KIND_NORMAL)
    c3 = Counter(3, KIND_NORMAL)
    b.add_counter(c1)
    b.add_counter(c2)
    b.add_counter(c3)
    assert b.active_counters == 3

    # Không cho phép trùng ID
    try:
        b.add_counter(Counter(2, KIND_NORMAL))
        assert False, "Lẽ ra phải báo lỗi trùng mã quầy"
    except ValueError:
        pass

    # Không cho phép thêm quầy ưu tiên thứ 2
    try:
        b.add_counter(Counter(4, KIND_PRIORITY))
        assert False, "Lẽ ra phải báo lỗi chỉ cho phép 1 quầy ưu tiên"
    except ValueError:
        pass
    print("[PASS] TC1: Khởi tạo và ràng buộc thêm quầy")

    print("--- 2. KIỂM THỬ CÂN BẰNG TẢI MIN-HEAP (ASSIGN PATIENT) ---")
    p1 = Patient("BN01", "Nguyễn Văn A", 20, 2)
    p2 = Patient("BN02", "Trần Văn B", 30, 2)
    p3 = Patient("BN03", "Lê Văn C", 25, 2)

    # Phân bổ bệnh nhân thường vào quầy thường ít người nhất
    assigned_c = b.assign_patient(p1, to_priority=False)
    assert assigned_c.counter_id == 2 and c2.load == 1

    assigned_c2 = b.assign_patient(p2, to_priority=False)
    assert assigned_c2.counter_id == 3 and c3.load == 1

    assigned_c3 = b.assign_patient(p3, to_priority=False)
    assert assigned_c3.counter_id == 2 and c2.load == 2
    print("[PASS] TC2: Min-Heap chọn quầy thường có tải nhỏ nhất")

    print("--- 3. KIỂM THỬ PHÂN BỔ BỆNH NHÂN ƯU TIÊN ---")
    p_prio = Patient("BN_P1", "Cụ Bà", 75, 2)
    p_assigned = b.assign_patient(p_prio, to_priority=True)
    assert p_assigned.counter_id == 1 and c1.load == 1
    print("[PASS] TC3: Bệnh nhân ưu tiên vào đúng quầy ưu tiên")

    print("--- 4. KIỂM THỬ PHỤC VỤ (SERVE NEXT) ---")
    served = b.serve_next(2)
    assert served.patient_id == "BN01"
    assert c2.load == 1
    print("[PASS] TC4: Gọi khám cập nhật đúng tải của quầy")

    print("--- 5. KIỂM THỬ ĐÓNG QUẦY SỰ CỐ & ĐIỀU CHUYỂN BỆNH NHÂN ---")
    # Đóng quầy 2 (đang có BN03 chờ) -> tự chuyển sang quầy 3
    moved = b.close_counter(2)
    assert len(moved) == 1 and moved[0].patient_id == "BN03"
    assert c3.load == 2  # BN02 và BN03
    assert not c2.is_open

    # Mở lại quầy 2
    b.open_counter(2)
    assert c2.is_open
    print("[PASS] TC5: Đóng sự cố và mở lại quầy chuẩn xác")

    print("\nTẤT CẢ TEST CASES CỦA BALANCER ĐÃ VƯỢT QUA!")


if __name__ == "__main__":
    run_tests()
