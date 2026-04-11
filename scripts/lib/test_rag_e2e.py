"""End-to-end integration test for the RAG pipeline via HTTP API."""

import base64
import os
import sys
import time
from pathlib import Path

import httpx

BASE_URL = os.environ.get("API_URL", "http://localhost:8000")
TMP_DIR = Path(__file__).resolve().parent.parent.parent / "tmp"
POLL_INTERVAL_S = 2
POLL_TIMEOUT_S = 30

PROJECT_FILES = {
    "ted-pim-artist.md": (
        "# Ted Pim\n\nTed Pim is a contemporary artist known for layering"
        " digital distortion over classical portraiture. His work blends"
        " Renaissance-era figures with modern decay aesthetics, cracked"
        " surfaces, ink runs, and chromatic bleeding. Featured at Urban"
        " Nation Berlin.\n\nKey themes: memory, erosion, beauty under pressure."
    ),
    "color-palette.txt": (
        "Primary palette — Ted Pim style:\n"
        "- Deep umber (#3B1F0A)\n"
        "- Venetian red (#C0392B)\n"
        "- Cobalt blue (#1A3B6E)\n"
        "- Ivory white (#F5F0E8)\n"
        "- Carbon black (#0D0D0D)\n\n"
        "Notes: high contrast, desaturated midtones, accent red only on wounds/lips"
    ),
    "exhibition-notes.yml": (
        "exhibition: Urban Nation Open Walls 2024\n"
        "artist: Ted Pim\nlocation: Berlin, Germany\nthemes:\n"
        "  - classical portraiture\n  - digital corruption\n"
        "  - feminine suffering\nnotes: >\n"
        "  Works are printed large-format then hand-treated with resin and\n"
        "  black ink runs. The distortion is intentional, referencing both\n"
        "  vandalism and the passage of time."
    ),
    "artwork-catalog.json": (
        '{"artist": "Ted Pim", "style": "neo-classical distortion", "works":'
        ' [{"title": "Untitled Triptych I", "medium": "oil + digital",'
        ' "year": 2023}, {"title": "Saint Bleeding", "medium": "oil + digital",'
        ' "year": 2022}, {"title": "The Weeping Three", "medium": "mixed media",'
        ' "year": 2024}], "gallery": "Urban Nation, Berlin"}'
    ),
}

results: list[bool] = []


def check(label: str, passed: bool, detail: str = "") -> bool:
    tag = "[PASS]" if passed else "[FAIL]"
    suffix = f" -- {detail}" if detail else ""
    print(f"  {tag} {label}{suffix}")
    results.append(passed)
    return passed


def poll_enriched(client: httpx.Client, file_id: str, label: str) -> bool:
    deadline = time.monotonic() + POLL_TIMEOUT_S
    while time.monotonic() < deadline:
        resp = client.get(f"{BASE_URL}/api/knowledge/{file_id}")
        if resp.status_code == 200 and resp.json().get("enriched"):
            return check(f"{label} enriched", True)
        time.sleep(POLL_INTERVAL_S)
    return check(f"{label} enriched", False, "timeout")


def step_upload_project_files(client: httpx.Client) -> list[dict]:
    print("\n[1/7] Uploading project knowledge files...")
    uploaded = []
    for filename, content in PROJECT_FILES.items():
        resp = client.post(
            f"{BASE_URL}/api/knowledge",
            json={"filename": filename, "content": content, "scope": "project"},
        )
        ok = resp.status_code == 200 and "id" in resp.json()
        check(f"upload {filename}", ok, f"status={resp.status_code}")
        if ok:
            uploaded.append(resp.json())
    return uploaded


def step_wait_enrichment(client: httpx.Client, files: list[dict]) -> None:
    print("\n[2/7] Waiting for LLM enrichment...")
    time.sleep(3)
    for f in files:
        poll_enriched(client, f["id"], f.get("filename", f["id"]))


def step_first_chat(client: httpx.Client) -> str:
    print("\n[3/7] Sending first chat message...")
    resp = client.post(
        f"{BASE_URL}/api/chat",
        json={"message": "Who is Ted Pim and what kind of art does he make?"},
    )
    ok = resp.status_code == 200
    data = resp.json() if ok else {}
    conv_id = data.get("conversationId", data.get("conversation_id", ""))
    msg = data.get("message", "").lower()
    mentions_ted = "ted pim" in msg or "contemporary" in msg or "artist" in msg
    check("chat response received", ok, f"status={resp.status_code}")
    check("response mentions Ted Pim / art", mentions_ted, msg[:120])
    return conv_id


def step_upload_image(client: httpx.Client, conversation_id: str) -> dict:
    print("\n[4/7] Uploading conversation image...")
    img_path = TMP_DIR / "TedPim_CoverImage_web.jpg"
    img_b64 = base64.b64encode(img_path.read_bytes()).decode()
    resp = client.post(
        f"{BASE_URL}/api/knowledge",
        json={
            "filename": "TedPim_CoverImage_web.jpg",
            "content": img_b64,
            "scope": "conversation",
            "conversationId": conversation_id,
        },
    )
    ok = resp.status_code == 200
    check("image upload", ok, f"status={resp.status_code}")
    return resp.json() if ok else {}


def step_wait_image_enrichment(client: httpx.Client, img: dict) -> None:
    print("\n[5/7] Waiting for image enrichment...")
    if not img.get("id"):
        check("image enrichment", False, "no image id")
        return
    time.sleep(3)
    poll_enriched(client, img["id"], "image")


def step_color_chat(client: httpx.Client, conversation_id: str) -> None:
    print("\n[6/7] Asking about colors...")
    resp = client.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "What colors does Ted Pim typically use?",
            "conversationId": conversation_id,
        },
    )
    ok = resp.status_code == 200
    msg = resp.json().get("message", "").lower() if ok else ""
    mentions_color = any(
        w in msg for w in ["color", "colour", "palette", "red", "umber", "cobalt"]
    )
    check("response received", ok, f"status={resp.status_code}")
    check("response references colors/palette", mentions_color, msg[:120])


def step_image_chat(client: httpx.Client, conversation_id: str) -> None:
    print("\n[7/7] Asking about uploaded image...")
    resp = client.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "Tell me about the image I uploaded",
            "conversationId": conversation_id,
        },
    )
    ok = resp.status_code == 200
    msg = resp.json().get("message", "").lower() if ok else ""
    mentions_image = any(
        w in msg for w in ["image", "artwork", "portrait", "painting", "ted pim", "photo"]
    )
    check("response received", ok, f"status={resp.status_code}")
    check("response references image/artwork", mentions_image, msg[:120])


def main() -> None:
    print(f"RAG E2E Integration Test -- {BASE_URL}")
    client = httpx.Client(timeout=120.0)

    uploaded = step_upload_project_files(client)
    step_wait_enrichment(client, uploaded)
    conversation_id = step_first_chat(client)

    if not conversation_id:
        print("\nNo conversation_id returned, cannot continue.")
        sys.exit(1)

    img = step_upload_image(client, conversation_id)
    step_wait_image_enrichment(client, img)
    step_color_chat(client, conversation_id)
    step_image_chat(client, conversation_id)

    passed = sum(results)
    total = len(results)
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
