import json

import requests


def main() -> None:
    url = "http://localhost:8000/api/generate"
    payload = {
        "content": {
            "specs": [
                {
                    "cpu": "CPU i5-12400",
                    "ram": "RAM 16GB DDR4",
                    "mainboard": "Mainboard B660M DDR4",
                    "storage": {"ssd": "NVMe 256GB", "hdd": "1TB 5400rpm"},
                    "power_supply": "Power Supply 650W",
                    "case": "ATX Mid Tower"
                }
            ],
            "target": "Build a PC for office work with low budget.",
        }
    }

    response = requests.post(url, json=payload, timeout=120)
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print(response.text)


if __name__ == "__main__":
    main()
