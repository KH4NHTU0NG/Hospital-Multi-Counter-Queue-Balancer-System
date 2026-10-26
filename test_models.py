from models import Patient, Counter, KIND_PRIORITY


def make_patient(pid, name="An", age=30, severity=2, emergency=False):
    return Patient(pid, name, age, severity, emergency)


def test_patient_validation():

    p = make_patient("P1")
    assert p.name == "An"


    bad_cases = [
        dict(patient_id="", name="An", age=30, severity=2),
        dict(patient_id="P2", name="", age=30, severity=2),
        dict(patient_id="P3", name="An", age=-1, severity=2),
        dict(patient_id="P4", name="An", age=30, severity=9),
    ]
    for case in bad_cases:
        try:
            Patient(**case)
            assert False, f"Lẽ ra phải báo lỗi: {case}"
        except ValueError:
            pass
    print("OK: validate Patient")


def test_dict_roundtrip():
    p = make_patient("P1", "Binh", 70, 4, True)
    p2 = Patient.from_dict(p.to_dict())
    assert p2.to_dict() == p.to_dict()
    print("OK: to_dict / from_dict")


def test_fifo():
    c = Counter(1)
    a, b, d = make_patient("A"), make_patient("B"), make_patient("C")
    c.enqueue(a)
    c.enqueue(b)
    c.enqueue(d)
    assert c.load == 3
    assert c.serve_next() is a
    assert c.serve_next() is b
    assert c.serve_next() is d
    assert c.serve_next() is None  
    assert c.peek() is None
    print("OK: FIFO và hàng trống")


def test_closed_counter():
    c = Counter(1)
    c.close()
    try:
        c.enqueue(make_patient("A"))
        assert False, "Lẽ ra phải báo lỗi"
    except ValueError:
        pass
    c.open()
    c.enqueue(make_patient("B"))
    assert c.load == 1
    print("OK: quầy đóng / mở lại")


def test_close_returns_waiting():
    c = Counter(1)
    a, b = make_patient("A"), make_patient("B")
    c.enqueue(a)
    c.enqueue(b)
    waiting = c.close()
    assert waiting == [a, b]        
    assert c.load == 0
    assert a.counter_id is None

    # Đóng quầy khi hàng trống
    empty = Counter(2)
    assert empty.close() == []
    print("OK: close()")


def test_enqueue_front_order():
    target = Counter(1)
    x = make_patient("X")
    target.enqueue(x)

    priority = Counter(9, KIND_PRIORITY)
    a, b = make_patient("A"), make_patient("B")
    priority.enqueue(a)
    priority.enqueue(b)

    moved = priority.close()
    target.enqueue_front_many(moved)


    assert target.serve_next() is a
    assert target.serve_next() is b
    assert target.serve_next() is x
    print("OK: enqueue_front_many giữ thứ tự")


def test_compare_for_heap():
    import heapq
    c1, c2, c3 = Counter(1), Counter(2), Counter(3)
    c1.enqueue(make_patient("A"))
    c1.enqueue(make_patient("B"))
    c2.enqueue(make_patient("C"))

    heap = [c1, c2, c3]
    heapq.heapify(heap)
    assert heapq.heappop(heap) is c3
    assert heapq.heappop(heap) is c2


    d1, d2 = Counter(5), Counter(4)
    assert d2 < d1
    print("OK: so sánh quầy / heapq")


if __name__ == "__main__":
    test_patient_validation()
    test_dict_roundtrip()
    test_fifo()
    test_closed_counter()
    test_close_returns_waiting()
    test_enqueue_front_order()
    test_compare_for_heap()
    print("Tất cả test đều qua")