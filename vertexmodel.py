from vertexai.preview.generative_models import (
    GenerativeModel,
    SafetySetting,
    Tool,
)
from vertexai.preview.generative_models import grounding
import vertexai


class VertexModel:
    """Handles generating content using the Vertex AI model."""

    def __init__(
        self, project_id: str = "propane-sphinx-448317-p4", location: str = "us-east1"
    ):
        """
        Initialize Vertex AI model and set up generation configurations.

        Args:
            project_id (str): The Google Cloud project ID for Vertex AI.
            location (str): The location of the Vertex AI resources.
        """
        self.generation_config = {
            "max_output_tokens": 8192,
            "temperature": 1,
            "top_p": 0.95,
        }

        # Define safety settings
        self.safety_settings = [
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=SafetySetting.HarmBlockThreshold.OFF,
            ),
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=SafetySetting.HarmBlockThreshold.OFF,
            ),
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=SafetySetting.HarmBlockThreshold.OFF,
            ),
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=SafetySetting.HarmBlockThreshold.OFF,
            ),
        ]

        # Initialize tools
        self.tools = [
            Tool.from_google_search_retrieval(
                google_search_retrieval=grounding.GoogleSearchRetrieval()
            ),
        ]

        # Initialize Vertex AI
        try:
            vertexai.init(project=project_id, location=location)
            print(
                f"Vertex AI initialized with project ID: {project_id} and location: {location}"
            )
        except Exception as e:
            print(f"Error initializing Vertex AI: {e}")
            raise

        # Initialize the model
        try:
            self.model = GenerativeModel(
                "gemini-1.5-pro-002",
                tools=self.tools,
            )
        except Exception as e:
            print(f"Error initializing GenerativeModel: {e}")
            raise

    def generate_response(self, transcript: str) -> str:
        """
        Generates content using Vertex AI model based on the transcript.

        Args:
            transcript (str): The input text for the model to process.

        Returns:
            str: The generated response text from the model.
        """
        try:
            responses = self.model.generate_content(
                [transcript],
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
                stream=True,
            )

            # Collect and return the response text
            complete_response = ""
            for response in responses:
                if response.candidates and response.candidates[0].content.parts:
                    complete_response += response.text
            return complete_response

        except Exception as e:
            print(f"Error generating response: {e}")
            return "An error occurred while generating the response."


if __name__ == "__main__":
    vertex_model = VertexModel()

    while True:
        user_transcript = input(
            "\nEnter your question (or type 'exit' to quit): "
        ).strip()
        if user_transcript.lower() == "exit":
            print("Exiting the program. Goodbye!")
            break

        if not user_transcript:
            print("No input detected. Please enter a valid question.")
            continue

        print("Processing your input...")

        # Generate a response from the Vertex model
        model_response = vertex_model.generate_response(user_transcript)

        print("\nModel Response:")
        print(model_response)
