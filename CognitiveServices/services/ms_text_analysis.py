"""
from azure.cognitiveservices.language.textanalytics import TextAnalyticsClient
from msrest.authentication import CognitiveServicesCredentials


def text_analysis(text):
    text_analytics_key = "5558c21d60eb470583d5f692047c46dd"
    credentials = CognitiveServicesCredentials(text_analytics_key)

    # Creates a text analytics with the given settings
    text_analytics_url = "https://westeurope.api.cognitive.microsoft.com/"
    text_analytics = TextAnalyticsClient(endpoint=text_analytics_url, credentials=credentials)
    docs = [
        {
            "id": "1",
            "language": "en",
            "text": text
        }
    ]
    response = text_analytics.sentiment(documents=docs)
    for document in response.documents:
        return "Sentiment Score: ", "{:.2f}".format(document.score)
"""