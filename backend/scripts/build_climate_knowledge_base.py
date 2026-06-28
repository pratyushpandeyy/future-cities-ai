import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


KNOWLEDGE_DIR = BACKEND_ROOT / "data" / "knowledge"
SEED_PATH = KNOWLEDGE_DIR / "climate_advisor_seed.json"
RAW_DIR = KNOWLEDGE_DIR / "raw"
INDEX_PATH = KNOWLEDGE_DIR / "climate_knowledge_index.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build local RAG knowledge chunks from seed and raw text files.",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DIR,
        help="Directory containing .txt or .md climate notes.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=INDEX_PATH,
        help="Output JSON index path.",
    )
    parser.add_argument(
        "--chunk-words",
        type=int,
        default=130,
        help="Approximate words per generated chunk.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed_chunks = load_seed_chunks()
    raw_chunks = build_raw_chunks(args.raw_dir, args.chunk_words)
    chunks = [*seed_chunks, *raw_chunks]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(chunks, indent=2), encoding="utf-8")

    print("Built climate RAG knowledge index.")
    print(f"output_path: {args.output}")
    print(f"seed_chunks: {len(seed_chunks)}")
    print(f"raw_chunks: {len(raw_chunks)}")
    print(f"total_chunks: {len(chunks)}")


def load_seed_chunks() -> list[dict[str, object]]:
    if not SEED_PATH.exists():
        return []

    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def build_raw_chunks(raw_dir: Path, chunk_words: int) -> list[dict[str, object]]:
    if not raw_dir.exists():
        return []

    chunks: list[dict[str, object]] = []

    for path in sorted(raw_dir.rglob("*")):
        if path.suffix.lower() not in {".txt", ".md"}:
            continue

        text = normalize_text(path.read_text(encoding="utf-8", errors="ignore"))
        title = title_for(path, text)

        for index, chunk_text in enumerate(split_text(text, chunk_words), start=1):
            chunks.append(
                {
                    "chunk_id": f"local-{path.stem}-{index:03d}",
                    "title": title,
                    "text": chunk_text,
                    "source": {
                        "title": title,
                        "publisher": "Local research note",
                        "year": datetime.now(UTC).year,
                        "url": None,
                    },
                    "tags": infer_tags(f"{title} {chunk_text}"),
                },
            )

    return chunks


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def title_for(path: Path, text: str) -> str:
    first_heading = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)

    if first_heading:
        return first_heading.group(1).strip()

    return path.stem.replace("_", " ").replace("-", " ").title()


def split_text(text: str, chunk_words: int) -> list[str]:
    words = text.split()

    if not words:
        return []

    chunks = []
    stride = max(40, chunk_words - 25)

    for start in range(0, len(words), stride):
        chunk = " ".join(words[start : start + chunk_words]).strip()

        if len(chunk.split()) >= 30:
            chunks.append(chunk)

    return chunks


def infer_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags = []
    keyword_tags = {
        "heat": ["heat", "temperature", "hot", "warming"],
        "flood": ["flood", "rainfall", "precipitation", "storm", "drainage"],
        "health": ["health", "asthma", "respiratory", "elderly", "children"],
        "water stress": ["water stress", "drought", "scarcity"],
        "green cover": ["vegetation", "green", "tree", "canopy"],
        "relocation": ["relocation", "migration", "habitability"],
        "urban": ["urban", "city", "district", "neighborhood"],
    }

    for tag, keywords in keyword_tags.items():
        if any(keyword in lowered for keyword in keywords):
            tags.append(tag)

    return tags or ["climate"]


if __name__ == "__main__":
    main()
