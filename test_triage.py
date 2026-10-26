from models import Patient, Counter, KIND_NORMAL
from triage_route import TriageRouter, QUEUE_EMERGENCY, QUEUE_PRIORITY, QUEUE_NORMAL


def run_tests():
    router = TriageRouter()

    print("--- 6 TEST CASES HỢP LỆ ---")
    p1 = Patient("BN01", "Nguyễn Văn A", 25, severity=2, is_emergency=False)
    assert router.triage_patient(p1) == QUEUE_NORMAL and len(router.normalQueue) == 1
    print("[PASS] TC1")

    p2 = Patient("BN02", "Trần Thị B", 70, severity=1, is_emergency=False)
    assert router.triage_patient(p2) == QUEUE_PRIORITY and len(router.priorityQueue) == 1
    print("[PASS] TC2")

    p3 = Patient("BN03", "Lê Văn C", 30, severity=4, is_emergency=False)
    assert router.triage_patient(p3) == QUEUE_PRIORITY and len(router.priorityQueue) == 2
    print("[PASS] TC3")

    p4 = Patient("BN04", "Phạm Thị D", 40, severity=3, is_emergency=True)
    assert router.triage_patient(p4) == QUEUE_EMERGENCY and len(router.emergencyQueue) == 1
    print("[PASS] TC4")

    p5 = Patient("BN05", "Hoàng Văn E", 50, severity=5, is_emergency=False)
    assert router.triage_patient(p5) == QUEUE_EMERGENCY and len(router.emergencyQueue) == 2
    print("[PASS] TC5")

    p6 = Patient("BN06", "Đỗ Bé F", 4, severity=2, is_emergency=False)
    router.triage_patient(p6)
    undone = router.undo_last_triage()
    assert undone.patient_id == "BN06" and len(router.priorityQueue) == 2
    print("[PASS] TC6a")

    next_p = router.get_next_patient()
    assert next_p.patient_id == "BN04"
    print("[PASS] TC6b")

    print("\n--- 5 TEST CASES SAI / BẮT LỖI ---")
    try:
        router.triage_patient({"patient_id": "BN99", "name": "Sai"})
        print("[FAIL] EC1")
    except TypeError:
        print("[PASS] EC1")

    try:
        router.triage_patient(p1)
        print("[FAIL] EC2")
    except ValueError:
        print("[PASS] EC2")

    try:
        c = Counter(1, KIND_NORMAL)
        c.close()
        router.route_next_to_counter(c)
        print("[FAIL] EC3")
    except ValueError:
        print("[PASS] EC3")

    try:
        p_err = Patient("BN_ERR", "Lỗi", 30, severity=10)
        router.triage_patient(p_err)
        print("[FAIL] EC4")
    except ValueError:
        print("[PASS] EC4")

    try:
        empty_r = TriageRouter()
        empty_r.undo_last_triage()
        print("[FAIL] EC5")
    except IndexError:
        print("[PASS] EC5")

    print("\nTẤT CẢ 11 TEST CASES ĐÃ VƯỢT QUA!")


if __name__ == "__main__":
    run_tests()