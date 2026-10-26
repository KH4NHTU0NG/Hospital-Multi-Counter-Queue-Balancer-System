# ==============================================================================
# FILE: test_database.py
# TÁC GIẢ: Member 5 (Database Module)
# MỤC ĐÍCH: Kiểm thử đơn vị cho cây nhị phân tìm kiếm BST (database.py)
# ==============================================================================

import os
from models import Patient
from database import PatientDatabase


def run_tests():
    print("--- 1. KIỂM THỬ THÊM & DUYỆT CÂY BST IN-ORDER ---")
    db = PatientDatabase()
    p_list = [
        Patient("BN05", "Bệnh nhân 5", 30, 2),
        Patient("BN02", "Bệnh nhân 2", 20, 1),
        Patient("BN07", "Bệnh nhân 7", 40, 3),
        Patient("BN01", "Bệnh nhân 1", 10, 1),
        Patient("BN03", "Bệnh nhân 3", 25, 2),
        Patient("BN06", "Bệnh nhân 6", 35, 3),
        Patient("BN08", "Bệnh nhân 8", 45, 4),
    ]
    for p in p_list:
        db.insert(p)

    all_p = db.get_all_patients()
    assert [p.patient_id for p in all_p] == ["BN01", "BN02", "BN03", "BN05", "BN06", "BN07", "BN08"]
    print("[PASS] TC1: BST Insert và In-order Traversal tăng dần theo ID")

    print("--- 2. KIỂM THỬ TÌM KIẾM (SEARCH) O(log n) ---")
    found = db.search("BN03")
    assert found is not None and found.name == "Bệnh nhân 3"
    assert db.search("BN99") is None
    print("[PASS] TC2: Tìm kiếm chính xác")

    print("--- 3. KIỂM THỬ CẬP NHẬT THÔNG TIN (UPDATE) ---")
    assert db.update("BN02", name="Bệnh nhân 2 (Đã sửa)", age=21) is True
    assert db.search("BN02").name == "Bệnh nhân 2 (Đã sửa)"
    assert db.search("BN02").age == 21
    assert db.update("BN99", name="Không tồn tại") is False
    print("[PASS] TC3: Cập nhật thông tin thành công")

    print("--- 4. KIỂM THỬ XÓA NÚT BST (DELETE) ---")
    # Xóa nút lá (BN01)
    assert db.delete("BN01") is True
    assert db.search("BN01") is None
    assert [p.patient_id for p in db.get_all_patients()] == ["BN02", "BN03", "BN05", "BN06", "BN07", "BN08"]

    # Xóa nút có 2 con (BN07 có 2 con là BN06 và BN08)
    assert db.delete("BN07") is True
    assert db.search("BN07") is None
    assert [p.patient_id for p in db.get_all_patients()] == ["BN02", "BN03", "BN05", "BN06", "BN08"]

    # Xóa nút gốc (BN05)
    assert db.delete("BN05") is True
    assert db.search("BN05") is None
    assert [p.patient_id for p in db.get_all_patients()] == ["BN02", "BN03", "BN06", "BN08"]

    # Xóa ID không tồn tại
    assert db.delete("BN99") is False
    print("[PASS] TC4: Xóa nút (nút lá, 2 con, nút gốc) bảo toàn cấu trúc BST")

    print("--- 5. KIỂM THỬ LƯU & ĐỌC FILE JSON ---")
    test_json = "temp_test_db.json"
    db.save_to_file(test_json)
    assert os.path.exists(test_json)

    db_new = PatientDatabase()
    db_new.load_from_file(Patient, test_json)
    assert len(db_new.get_all_patients()) == 4
    assert db_new.search("BN02").name == "Bệnh nhân 2 (Đã sửa)"

    os.remove(test_json)
    print("[PASS] TC5: Ghi & Đọc JSON tái tạo BST chính xác")

    print("\nTẤT CẢ TEST CASES CỦA DATABASE BST ĐÃ VƯỢT QUA!")


if __name__ == "__main__":
    run_tests()
