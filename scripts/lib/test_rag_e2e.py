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
    print("\n[1/8] Uploading project knowledge files...")
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
    print("\n[2/8] Waiting for LLM enrichment...")
    time.sleep(3)
    for f in files:
        poll_enriched(client, f["id"], f.get("filename", f["id"]))


def step_first_chat(client: httpx.Client) -> str:
    print("\n[3/8] Sending first chat message...")
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


def step_chat_with_image(client: httpx.Client, conversation_id: str) -> None:
    """Send image through the chat endpoint, matching real user flow.

    The chat service indexes and enriches images synchronously before the
    agent responds, so RAG context is available from the first turn.
    """
    print("\n[4/8] Sending chat message with attached image...")
    img_path = TMP_DIR / "TedPim_CoverImage_web.jpg"
    img_b64 = base64.b64encode(img_path.read_bytes()).decode()
    resp = client.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "What do you see in this image?",
            "conversationId": conversation_id,
            "images": [img_b64],
            "imageFilenames": ["TedPim_CoverImage_web.jpg"],
        },
    )
    ok = resp.status_code == 200
    msg = resp.json().get("message", "").lower() if ok else ""
    sees_image = any(
        w in msg for w in ["image", "artwork", "portrait", "painting", "figure", "weep"]
    )
    check("chat+image response received", ok, f"status={resp.status_code}")
    check("first-turn response describes image", sees_image, msg[:120])


def step_verify_image_indexed(client: httpx.Client, conversation_id: str) -> None:
    """Verify the image landed in the knowledge base and was enriched.

    Because indexing now happens before the agent responds, the image
    should already be enriched by the time the chat call returns.
    """
    print("\n[5/8] Verifying image is indexed and enriched...")
    resp = client.get(
        f"{BASE_URL}/api/knowledge",
        params={"scope": "conversation", "conversationId": conversation_id},
    )
    ok = resp.status_code == 200
    files = resp.json() if ok else []
    image_files = [f for f in files if f.get("fileType", f.get("file_type", "")) in ("jpg", "jpeg")]
    has_image = len(image_files) >= 1
    check("image in knowledge base", has_image, f"found {len(image_files)} image(s)")
    if has_image:
        enriched = image_files[0].get("enriched", False)
        check("image already enriched", enriched)


def step_followup_about_image(client: httpx.Client, conversation_id: str) -> None:
    """Follow-up asking about the image without re-uploading.

    This is the exact scenario that was broken: the agent used RAG
    search_knowledge but scored below MIN_RELEVANCE_SCORE, returning
    'No relevant documents found.' The fix lowers the conversation
    threshold to 0.15 so image summaries survive filtering.
    """
    print("\n[6/8] Follow-up: asking about the uploaded image (RAG retrieval)...")
    resp = client.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "Tell me more about the image I uploaded",
            "conversationId": conversation_id,
        },
    )
    ok = resp.status_code == 200
    msg = resp.json().get("message", "").lower() if ok else ""
    recalls_image = any(
        w in msg
        for w in ["image", "artwork", "portrait", "painting", "figure", "weep", "three"]
    )
    check("response received", ok, f"status={resp.status_code}")
    check("follow-up recalls image content via RAG", recalls_image, msg[:120])


def step_color_chat(client: httpx.Client, conversation_id: str) -> None:
    print("\n[7/8] Asking about colors...")
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


def step_cross_reference(client: httpx.Client, conversation_id: str) -> None:
    """Ask a question that requires connecting the image to project knowledge.

    The agent needs both the conversation-scoped image and the
    project-scoped artist files to answer well.
    """
    print("\n[8/8] Cross-referencing image with project knowledge...")
    resp = client.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": (
                "Does the image I uploaded match Ted Pim's style "
                "based on what you know about his work?"
            ),
            "conversationId": conversation_id,
        },
    )
    ok = resp.status_code == 200
    msg = resp.json().get("message", "").lower() if ok else ""
    connects = any(
        w in msg for w in ["style", "pim", "portrait", "distortion", "classical", "decay"]
    )
    check("response received", ok, f"status={resp.status_code}")
    check("response connects image to artist style", connects, msg[:120])


def main() -> None:
    print(f"RAG E2E Integration Test -- {BASE_URL}")
    client = httpx.Client(timeout=120.0)

    uploaded = step_upload_project_files(client)
    step_wait_enrichment(client, uploaded)
    conversation_id = step_first_chat(client)

    if not conversation_id:
        print("\nNo conversation_id returned, cannot continue.")
        sys.exit(1)

    step_chat_with_image(client, conversation_id)
    step_verify_image_indexed(client, conversation_id)
    step_followup_about_image(client, conversation_id)
    step_color_chat(client, conversation_id)
    step_cross_reference(client, conversation_id)

    passed = sum(results)
    total = len(results)
    print(f"\n{'=' * 40}")
    print(f"Results: {passed}/{total} passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
