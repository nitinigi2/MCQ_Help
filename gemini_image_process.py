import google.generativeai as genai
from PIL import Image
from io import BytesIO
import requests
from dotenv import load_dotenv
import os
import re

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
            "**Task:** I have an image containing information and a multiple-choice question based on its content. "
            "Please analyze the image thoroughly, extract meaningful information, and identify the most appropriate "
            "answer from the given options. Use the extracted data, contextual clues, and logical reasoning to select "
            "the correct choice.",
            image,
            "**Output:**",
            "**Answer:** <letter of the correct answer>",
            "**Explanation:** (Optional) A brief explanation of why this is the correct answer in fewer words."
        ]

        # Configure and use Gemini API (replace with your actual API key)
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")  # Use gemini-pro-vision for image input

        # Generate text using the Gemini model
        response = model.generate_content(prompt)

        # Extract answer and explanation from the response
        return extract_answer_and_explanation(response.text)

    except Exception as e:
        print(f"Error processing image with Gemini: {e}")
        return None, "Error processing image."


def extract_answer_and_explanation(input_string):
    try:
        # Extract the answer using regex (make it more robust to handle unexpected spaces or variations)
        answer_match = re.search(r'\*\*Answer:\*\*\s*([a-zA-Z])', input_string)
        answer = answer_match.group(1) if answer_match else "Could not determine the answer. Please read the " \
                                                            "explanation "

        # Extract the explanation using regex
        try:
            explanation_match = re.search(r'\*\*Explanation:\*\*\s*(.*)', input_string, re.DOTALL)
            explanation = explanation_match.group(1).strip() if explanation_match else "No Explanation Found. Please try again later."
        except Exception:
            explanation = "No Explanation Found. Please try again later."

    except Exception:
        answer = "Error extracting answer."
        explanation = "Error extracting explanation."

    return answer, explanation

