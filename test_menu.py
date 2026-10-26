# ==============================================================================
# FILE: test_menu.py
# TÁC GIẢ: Lê Trí Nhân - SE211777 (Member 1)
# MỤC ĐÍCH: Kiểm thử tích hợp toàn hệ thống (Integration & Unit Tests cho menu.py)
# ==============================================================================

import os
from menu import HospitalQueueSystem
from models import STATUS_WAITING, STATUS_IN_SERVICE, STATUS_DONE, KIND_NORMAL
from triage_route import QUEUE_EMERGENCY, QUEUE_PRIORITY, QUEUE_NORMAL


def run_integration_tests():
    system = HospitalQueueSystem()

    print("--- 1. KIỂM THỬ TIẾP NHẬN, PHÂN LOẠI & LƯU BST/HASHMAP ---")
    p1, q1 = system.register_patient("BN01", "Nguyễn Văn A", 25, 2, False)
    p2, q2 = system.register_patient("BN02", "Trần Thị B", 70, 2, False)
    p3, q3 = system.register_patient("BN03", "Lê Văn C", 30, 4, False)
    p4, q4 = system.register_patient("BN04", "Phạm Thị D", 40, 3, True)
    p5, q5 = system.register_patient("BN05", "Hoàng Văn E", 35, 1, False)

    assert q1 == QUEUE_NORMAL
    assert q2 == QUEUE_PRIORITY
    assert q3 == QUEUE_PRIORITY
    assert q4 == QUEUE_EMERGENCY
    assert q5 == QUEUE_NORMAL
    assert system.router.total_waiting() == 5
    print("[PASS] TC1: Phân loại Triage & Lưu Hashmap/BST chính xác")

    print("--- 2. KIỂM THỬ HOÀN TÁC (STACK UNDO) ---")
    p_temp, _ = system.register_patient("BN99", "Nhập Nhầm", 20, 1, False)
    undone_p, _ = system.undo_last_registration()
    assert undone_p.patient_id == "BN99"
    assert system.find_patient("BN99")[0] is None
    print("[PASS] TC2: Hoàn tác Stack LIFO & Xóa bản ghi nhầm khỏi BST/Cache")

    print("--- 3. KIỂM THỬ ĐIỀU PHỐI SANG QUẦY (MIN-HEAP BALANCER) ---")
    results = system.dispatch_all_waiting_to_counters()
    assert len(results) == 5
    c1 = system.balancer.get_counter(1)
    c2 = system.balancer.get_counter(2)
    c3 = system.balancer.get_counter(3)
    assert c2.load == 1 and c3.load == 1
    print("[PASS] TC3: Điều phối cân bằng tải qua Min-Heap chính xác")

    print("--- 4. KIỂM THỬ GỌI KHÁM & XUẤT VIỆN (SERVE & DISCHARGE) ---")
    served_p, prev_p = system.call_next_patient_at_counter(2)
    assert served_p.patient_id == "BN01" and served_p.status == STATUS_IN_SERVICE
    done_p = system.discharge_current_at_counter(2)
    assert done_p.patient_id == "BN01" and done_p.status == STATUS_DONE
    print("[PASS] TC4: Gọi khám và Xuất viện cập nhật trạng thái chuẩn xác")

    print("--- 5. KIỂM THỬ ĐÓNG QUẦY SỰ CỐ & TỰ ĐỘNG ĐIỀU CHUYỂN ---")
    moved_prio = system.close_counter(1)
    assert len(moved_prio) > 0
    assert c2.peek().patient_id == moved_prio[0].patient_id
    system.open_counter(1)
    print("[PASS] TC5: Xử lý sự cố đóng/mở quầy và bảo toàn thứ tự ưu tiên")

    print("--- 6. KIỂM THỬ MERGE SORT & TÌM KIẾM/CẬP NHẬT ---")
    all_patients = system.db.get_all_patients()
    sorted_by_age_desc = system.merge_sort_patients(all_patients, key_func=lambda p: p.age, reverse=True)
    assert sorted_by_age_desc[0].age == 70
    system.update_patient_record("BN05", name="Hoàng Văn E (Đã sửa)", severity=3)
    found_p, _ = system.find_patient("BN05")
    assert found_p.name == "Hoàng Văn E (Đã sửa)" and found_p.severity == 3
    print("[PASS] TC6: Sắp xếp Merge Sort O(n log n) & Cập nhật BST/Hashmap")

    print("--- 7. KIỂM THỬ LƯU/ĐỌC JSON & XUẤT CSV ---")
    saved_count = system.save_all_data("test_db.json", "test_report.csv")
    assert saved_count == 5 and os.path.exists("test_db.json") and os.path.exists("test_report.csv")

    # Kiểm tra nạp lại dữ liệu vào phiên làm việc mới
    fresh_system = HospitalQueueSystem()
    loaded_count = fresh_system.load_data_from_json("test_db.json")
    assert loaded_count == 5
    assert fresh_system.stats_cache["total_registered"] == 5

    os.remove("test_db.json")
    os.remove("test_report.csv")
    print("[PASS] TC7: Lưu/Đọc JSON và Xuất báo cáo CSV thành công (Đồng bộ Cache)")

    print("\n==> TẤT CẢ 7 KỊCH BẢN TÍCH HỢP HỆ THỐNG ĐỀU VƯỢT QUA (100% PASS)!")


if __name__ == "__main__":
    run_integration_tests()
