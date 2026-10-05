from services.ai import generate_answer


def test_ai_fallback():

    answer = generate_answer(
        question="What is hemoglobin?",
        context="Hemoglobin carries oxygen in the blood."
    )

    assert isinstance(answer, str)
    assert len(answer) > 0