import requests

BASE_URL = 'http://127.0.0.1:5000/api'

def test_api():
    print("=== APIテスト開始 ===\n")

    # 1. スタッフの登録テスト
    print("1. スタッフを登録します...")
    res1 = requests.post(f"{BASE_URL}/staff", json={"name": "安藤瑠"})
    res2 = requests.post(f"{BASE_URL}/staff", json={"name": "永山翔太"})
    res2 = requests.post(f"{BASE_URL}/staff", json={"name": "佐藤大翔"})
    print(res1.json())
    print(res2.json(), "\n")

    # 2. スタッフ一覧の取得テスト
    print("2. スタッフ一覧を取得します...")
    res_staff = requests.get(f"{BASE_URL}/staff")
    staff_data = res_staff.json()
    print(staff_data, "\n")

    # 3. 希望休の提出テスト（山田さんが5月1日と5日に休む）
    print("3. 山田さん(ID: 1)の希望休を登録します...")
    res_shift = requests.post(f"{BASE_URL}/shifts", json={
        "staff_id": 1,
        "dates": ["2024-05-01", "2024-05-05"]
    })
    print(res_shift.json(), "\n")

    # 4. 指定した月（2024年5月）の希望休を取得するテスト
    print("4. 2024年5月の希望休一覧を取得します...")
    res_get_shifts = requests.get(f"{BASE_URL}/shifts/2024-05")
    print(res_get_shifts.json(), "\n")

    print("=== テスト完了 ===")

if __name__ == "__main__":
    test_api()