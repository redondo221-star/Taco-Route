def fetch_multi_routes():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": API_KEY,
               "X-Goog-Fieldmask": "routes.legs.steps,routes.polyline"}
    
    # ルートA: 高速フル活用
    payload_fast = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE",
        "routeModifiers": {"avoidHighways": False}, "languageCode": "ja-JP"
    }
    
    # ルートB: 一般道優先（新4号などを通る可能性が高い）
    payload_local = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE",
        "routeModifiers": {"avoidHighways": True}, "languageCode": "ja-JP"
    }

    # 両方のルートを取得して比較するロジックへ...
