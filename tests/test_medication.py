from services.medication import extract_medications


def test_medication_extraction():

    text = """
    Paracetamol 500 mg
    """

    medications = extract_medications(text)

    assert isinstance(medications, list)