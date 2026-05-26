try:
    import spacy  # type: ignore[import]
except ImportError as e:
    raise SystemExit(
        "spaCy is required to run this script.\n"
        "Install it and the English model with:\n"
        "  pip install spacy\n"
        "  python -m spacy download en_core_web_sm\n"
        f"Original import error: {e}"
    )


def load_model():
    """Load the small English spaCy pipeline, with a clear error if missing."""
    try:
        return spacy.load("en_core_web_sm")
    except OSError as e:
        raise SystemExit(
            "spaCy model 'en_core_web_sm' is not installed.\n"
            "Install it with:\n"
            "  python -m spacy download en_core_web_sm\n"
            f"Original error: {e}"
        )


def analyze(text: str) -> None:
    nlp = load_model()
    doc = nlp(text)

    print("Tokens:")
    for token in doc:
        print(token.text, token.pos_, token.dep_)

    print("\nEntities:")
    for ent in doc.ents:
        print(ent.text, ent.label_)


if __name__ == "__main__":
    sample = "Apple is looking at buying a startup in the UK for $1 billion."
    analyze(sample)