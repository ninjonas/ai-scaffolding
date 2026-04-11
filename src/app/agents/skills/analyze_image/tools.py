import structlog
from langchain_core.tools import tool

log = structlog.get_logger()


@tool
def describe_image(image_base64: str, question: str = "") -> str:
    """Analyze an image and describe its contents.

    Optionally answer a specific question about the image.
    """
    log.info("describe_image_called", has_question=bool(question), image_size=len(image_base64))
    prompt = "Describe this image in detail."
    if question:
        prompt = f"Regarding this image: {question}"
    log.info("describe_image_done", description_length=len(prompt))
    return prompt
