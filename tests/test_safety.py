from services.safety import check_safety


def test_normal_text():

    result = check_safety(
        "The patient has a routine blood test."
    )

    assert result["level"] == "normal"


def test_emergency_text():

    result = check_safety(
        "The patient has severe chest pain and difficulty breathing."
    )

    assert result["level"] == "emergency"
    assert result["safe"] is False