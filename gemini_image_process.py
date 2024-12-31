import os
import re
from io import BytesIO

import google.generativeai as genai
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')


def get_output(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        if response.status_code == 200:
            image = response.content
            if not image:
                return 'error', 'Could not find the result. Please try again later'
            return find_mcq_answer_gemini_url(image)
        else:
            return 'error', 'Could not find the result. Please try again later'
    except Exception as e:
        print(f"Error in processing: {e}")
        return 'error', 'Could not process the result. Please try again later'


def resize_image(img, max_size=512):
    width, height = img.size
    if max(width, height) > max_size:
        ratio = min(max_size / width, max_size / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height))
    return img


def find_mcq_answer_gemini_url(image_in_bytes):
    """
    Extracts text from the image URL using the Gemini API and identifies the most likely answer.

    Args:
        image_in_bytes: URL of the image containing the MCQ.
        options: List of possible answer options (e.g., ["A", "B", "C", "D"]).

    Returns:
        A tuple containing:
            - The most likely answer option.
            - A short description of the answer (if available).
    """

    try:
        image = Image.open(BytesIO(image_in_bytes))

        # image resizing
        image = resize_image(image)

        # Define the prompt for the Gemini model
        prompt = [
            "**Task:** Analyze the image below, which contains a question (or a multiple-choice question). "
            "The text may be blurry, unclear, or ambiguous. "
            "Provide your best interpretation, explicitly stating any assumptions made due to poor image quality or "
            "ambiguity. "

            "**Output Format:**",
            "**Question:** [Your formulated question] (If unclear, provide your interpretation in brackets.)",
            "**Options:** [List all options, regardless of their format (e.g., 1, 2, 3... or A, B, C...). If options "
            "are unclear, interpret them and note this in brackets. For whitespace-separated options, clearly delimit "
            "each option using square brackets. "
            "[Option 1/A/a text] [Option 2/B/b text] [Option 3/C/c text] [Option 4/D/d text] (Add more options if "
            "needed.)]",
            "**Explanation:** (Optional) (under 50 words). Provide a concise explanation for your answer(s), "
            "including: "
            "Key assumptions made (e.g., due to blurry or ambiguous text). "
            "How ambiguities were resolved or why no resolution was possible. "
            "For multiple interpretations, explain each plausible answer.",
            "**Answer:** [List of your correct answers]",
            image,
        ]
        # Configure and use Gemini API (replace with your actual API key)
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")  # Use gemini-pro-vision for image input

        # Generate text using the Gemini model
        response = model.generate_content(prompt)

        print(response.text)

        # Extract answer and explanation from the response
        return extract_answer_and_explanation(response.text)

    except Exception as e:
        print(f"Error processing image with Gemini: {e}")
        return None, "Error processing image."


def extract_answer_and_explanation(input_string):
    try:
        # Extract the answer using regex (make it more robust to handle unexpected spaces or variations)
        answer_match = re.search(r"(?<=\*\*Answer:\*\*\s)(.*)", input_string, re.IGNORECASE)
        answer = answer_match.group(1).strip() \
            if answer_match else "Could not determine the answer. Please read the explanation "

        # Extract the explanation using regex
        try:
            explanation_match = re.search(r'\*\*Explanation:\*\*\s*(.*)', input_string, re.DOTALL)
            explanation = explanation_match.group(
                1).strip() if explanation_match else "No Explanation Found. Please try again later."
        except Exception:
            explanation = "No Explanation Found. Please try again later."

    except Exception:
        answer = "Error extracting answer."
        explanation = "Error extracting explanation."

    return answer, explanation

