from vertexai.preview.generative_models import (
    GenerativeModel,
    SafetySetting,
    Tool,
)
from vertexai.preview.generative_models import grounding
from google.auth.credentials import AnonymousCredentials
import vertexai

class VertexModel:
    """Handles generating content using the Vertex AI model."""
    
    def __init__(self, project_id: str, location: str):
        """Initialize Vertex AI model and set up generation configurations."""
        
        # Shared generation config
        self.generation_config = {
            "max_output_tokens": 8192,
            "temperature": 1,
            "top_p": 0.95,
        }
        
        # Shared safety settings
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
        vertexai.init(project=project_id, location=location)
        
        # Initialize the model
        self.model = GenerativeModel(
            "gemini-1.5-pro-002",
            tools=self.tools,
        )

    def generate_response_from_transcript(self, transcript: str) -> None:
        """Generates content using Vertex AI model based on the transcript."""
        # Use the pre-defined generation config and safety settings
        responses = self.model.generate_content(
            [transcript],
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            stream=True,
        )

        for response in responses:
            if response.candidates and response.candidates[0].content.parts:
                print(response.text, end="")
