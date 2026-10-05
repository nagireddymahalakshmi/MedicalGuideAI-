from services.rag import retrieve, build_context


def test_rag_retrieval():

    document = """
    Hemoglobin is 12 g/dL.
    Blood glucose is 95 mg/dL.
    The patient should discuss the report with a doctor.
    """

    results = retrieve(
        query="What is the hemoglobin?",
        document_text=document
    )

    assert len(results) > 0


def test_context():

    document = """
    Hemoglobin is 12 g/dL.
    """

    context = build_context(
        query="hemoglobin",
        document_text=document
    )

    assert isinstance(context, str)