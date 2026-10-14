from functools import cached_property


class LayaUnavailableError(RuntimeError):
    """Raised when Laya is enabled but cannot be loaded or queried."""


class LayaDecisionProvider:
    """Local Laya adapter for binary RAG-quality decisions.

    Laya receives one short, labelled state at a time. The neutral choice keys
    avoid the `noul` label-bias limitation documented by the model authors.
    """

    _VALID_MODELS = {"english", "multilingual", "typed-decisions", "decisions", "default", "en", "laya", "laya-multilingual", "laya-typed-decisions", "ml", "multi", "typed", "typed_decisions"}

    def __init__(self, model: str | None, device: str | None, max_context_chars: int) -> None:
        self.model = self._normalize_model(model)
        self.device = device or None
        self.max_context_chars = max_context_chars

    @classmethod
    def _normalize_model(cls, model: str | None) -> str | None:
        if not model:
            return None
        if "/" in model:
            model = model.rsplit("/", 1)[-1]
        return model if model in cls._VALID_MODELS else None

    @cached_property
    def router(self):
        try:
            from laya import Router
        except ImportError as exc:
            raise LayaUnavailableError(
                "Laya is enabled but not installed. Install the 'laya' project dependency."
            ) from exc
        try:
            kwargs = {"max_loaded": 1}
            if self.device:
                kwargs["device"] = self.device
            return Router(**kwargs)
        except Exception as exc:
            raise LayaUnavailableError(f"Laya could not be initialized: {exc}") from exc

    def relevance(self, question: str, context: str) -> float:
        return self._yes_probability(
            f"Question:\n{question}\n\nCandidate context:\n{context}",
            "Does the candidate context contain information that directly helps answer the question?",
        )

    def faithfulness(self, answer: str, context: str) -> float:
        return self._yes_probability(
            f"Answer:\n{answer}\n\nRetrieved context:\n{context}",
            "Is every factual claim in the answer supported by the retrieved context?",
        )

    def citation_support(self, answer: str, source: str) -> float:
        return self._yes_probability(
            f"Answer:\n{answer}\n\nCitation source:\n{source}",
            "Does the citation source support at least one factual claim in the answer?",
        )

    def ocr_quality(self, text: str) -> float:
        return self._yes_probability(
            f"OCR text:\n{text}",
            "Is this text readable and mostly free of random characters or gibberish?",
        )

    def _yes_probability(self, state: str, instruction: str) -> float:
        state = state[: self.max_context_chars]
        questions = {
            "decision": {
                "type": "choice",
                "instructions": instruction,
                "criteria": {
                    "A": "yes, the statement is supported",
                    "B": "no, the statement is not supported",
                },
            }
        }
        try:
            kwargs = {"model": self.model} if self.model else {}
            result = self.router.predict({"text": state}, questions, **kwargs)
            probabilities = result["answers"]["decision"]["probabilities"]
            return float(probabilities["A"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LayaUnavailableError(f"Laya returned an invalid decision result: {exc}") from exc
        except LayaUnavailableError:
            raise
        except Exception as exc:
            raise LayaUnavailableError(f"Laya decision failed: {exc}") from exc