from data_masking_tool import data_masking_tool

def test_data_masking_tool():
    sample_text = "My phone number is 012-3456789."
    result = data_masking_tool(sample_text)
    assert isinstance(result, dict), "Expected output to be a dictionary"
    assert "masked_text" in result, "Expected key 'masked_text' in output"
    assert isinstance(result["masked_text"], str), "Expected 'masked_text' to be a string"
    print("Test passed")

test_data_masking_tool()
