"""LLMCall: row -> single LLM call, exercised against MockChatClient."""
import unittest

from cargodash import LLMCall, MockChatClient


class TestLLMCall(unittest.TestCase):
    def test_basic_call_writes_output_field(self):
        call = LLMCall(prompt="echo: {text}",
                       client=MockChatClient(fixed_response="ok"))
        out = call({"text": "hello"})
        self.assertEqual(out["llm_output"], "ok")
        self.assertEqual(out["text"], "hello")  # original field preserved

    def test_custom_output_field(self):
        call = LLMCall(prompt="{text}", output_field="reply",
                       client=MockChatClient(fixed_response="hi"))
        self.assertIn("reply", call({"text": "x"}))

    def test_prompt_template_filled_from_row(self):
        seen = {}

        def capture(messages):
            seen["content"] = messages[-1]["content"]
            return "r"

        call = LLMCall(prompt="Rewrite: {text}",
                       client=MockChatClient(response_fn=capture))
        call({"text": "abc"})
        self.assertEqual(seen["content"], "Rewrite: abc")

    def test_system_prompt_is_prepended(self):
        seen = {}

        def capture(messages):
            seen["roles"] = [m["role"] for m in messages]
            return "r"

        call = LLMCall(prompt="{text}", system_prompt="be brief",
                       client=MockChatClient(response_fn=capture))
        call({"text": "x"})
        self.assertEqual(seen["roles"], ["system", "user"])

    def test_missing_template_field_raises_keyerror(self):
        call = LLMCall(prompt="{missing}", client=MockChatClient())
        with self.assertRaises(KeyError):
            call({"text": "x"})

    def test_requires_client_or_model(self):
        with self.assertRaises(ValueError):
            LLMCall(prompt="{text}")

    def test_client_and_model_together_rejected(self):
        with self.assertRaises(ValueError):
            LLMCall(prompt="{text}", client=MockChatClient(), model="gpt-4")


if __name__ == "__main__":
    unittest.main()
