import json
from pathlib import Path

src = Path("data/validation_set.jsonl")
dst = Path("data/validation_set.clean.jsonl")

with src.open("r", encoding="utf-8-sig") as fin, \
     dst.open("w", encoding="utf-8") as fout:
    for i, line in enumerate(fin, 1):
        try:
            obj = json.loads(line)
            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
        except Exception as e:
            raise RuntimeError(f"❌ Error at line {i}: {e}")

print("✅ Clean validation file generated:", dst)
