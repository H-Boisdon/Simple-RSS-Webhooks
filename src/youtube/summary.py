import nltk
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer
from youtube_transcript_api import YouTubeTranscriptApi


def ensure_nltk_resources():
    """Checks for necessary NLTK resources and downloads them if missing."""
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        print("Downloading missing NLTK 'punkt_tab' resource...")
        nltk.download("punkt_tab")


def get_free_summary(video_id, sentences_count=5):
    ensure_nltk_resources()
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=["fr", "en"])
        lang = transcript.language.lower()
        print(lang)

        full_text = " ".join([entry.text for entry in transcript])
        parser = PlaintextParser.from_string(full_text, Tokenizer(lang))

        summarizer = LsaSummarizer()
        summary_sentences = summarizer(parser.document, sentences_count)
        summary = " ".join([str(sentence) for sentence in summary_sentences])

        return summary

    except Exception as e:
        return f"Could not summarize: {str(e)}"
