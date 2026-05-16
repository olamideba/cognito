import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID

from routers.generate import (
    AnalogyRequest,
    ImageGenerationResult,
    generate_analogy,
)
from routers.session import QuizAnswerRequest, post_quiz_answer
from domains.agents import handlers


class _FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_json(self, envelope: dict) -> None:
        self.messages.append(envelope)


class AnalogyQuizFlowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.ws = _FakeWebSocket()
        handlers.set_live_context("session-123", self.ws)

    async def test_generate_analogy_visual_emits_timestamp_and_persists(self) -> None:
        mock_image = AsyncMock(
            return_value=ImageGenerationResult(
                base64_string="base64,abc",
                status="generated",
                message="Analogy image generated successfully.",
                model="gemini-2.5-flash-image",
                used_fallback=False,
            )
        )
        mock_append = AsyncMock(return_value="data:image/png;base64,abc")

        with (
            patch("domains.analogy.module.generate_image_result", mock_image),
            patch("domains.analogy.module.append_analogy", mock_append),
        ):
            result = await handlers.generate_analogy_visual(
                concept_label="Recursion Stack",
                image_prompt="Show call frames as stacked boxes.",
            )

        self.assertEqual(result["status"], "generated")
        self.assertEqual(result["session_id"], "session-123")
        self.assertEqual(result["concept_label"], "Recursion Stack")
        self.assertEqual(result["image_url"], "data:image/png;base64,abc")
        self.assertEqual(result["message"], "Analogy image generated successfully.")
        self.assertFalse(result["used_fallback"])
        datetime.fromisoformat(result["timestamp"])

        mock_append.assert_awaited_once_with(
            "session-123",
            "Recursion Stack",
            "base64,abc",
            result["timestamp"],
        )

        self.assertEqual(
            self.ws.messages,
            [{"type": "analogy_generated", "payload": result}],
        )

    async def test_generate_analogy_visual_marks_fallback_as_failed(self) -> None:
        mock_image = AsyncMock(
            return_value=ImageGenerationResult(
                base64_string="base64,fallback",
                status="failed",
                message="Image generation failed; fallback visual provided.",
                model="gemini-2.5-flash-image",
                used_fallback=True,
                error="model not available",
            )
        )
        mock_append = AsyncMock(return_value="data:image/png;base64,fallback")

        with (
            patch("domains.analogy.module.generate_image_result", mock_image),
            patch("domains.analogy.module.append_analogy", mock_append),
        ):
            result = await handlers.generate_analogy_visual(
                concept_label="Queue",
                image_prompt="Show items entering and leaving a line.",
            )

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["used_fallback"])
        self.assertEqual(result["error"], "model not available")
        mock_append.assert_awaited_once()

    async def test_render_quiz_component_hides_correct_answer_in_ui_payload(self) -> None:
        mock_get_session = AsyncMock(return_value={"state": {}})
        mock_update = AsyncMock()
        fixed_component_id = UUID("12345678-1234-5678-1234-567812345678")

        with (
            patch("domains.mentor.module.get_session", mock_get_session),
            patch("domains.mentor.module.update_session", mock_update),
            patch(
                "domains.mentor.module.uuid.uuid4",
                return_value=fixed_component_id,
            ),
        ):
            result = await handlers.render_quiz_component(
                component_type="multiple_choice",
                question="Which is LIFO?",
                options=["Queue", "Stack"],
                correct_answer="Stack",
                hint="Think push/pop.",
            )

        self.assertEqual(result["status"], "rendered")
        self.assertEqual(
            result["component_id"], "12345678-1234-5678-1234-567812345678"
        )
        mock_update.assert_awaited_once_with(
            "session-123",
            {
                "state": {
                    "correct_answer": "Stack",
                    "last_component_id": "12345678-1234-5678-1234-567812345678",
                }
            },
        )

        self.assertEqual(len(self.ws.messages), 1)
        sent = self.ws.messages[0]
        self.assertEqual(sent["type"], "quiz_component")
        self.assertEqual(
            sent["payload"]["component_id"],
            "12345678-1234-5678-1234-567812345678",
        )
        self.assertNotIn("correct_answer", sent["payload"])

    async def test_generate_analogy_route_returns_model_response(self) -> None:
        mock_generate = AsyncMock(return_value="data:image/svg+xml;base64,xyz")

        with patch("routers.generate.generate_image", mock_generate):
            response = await generate_analogy(
                AnalogyRequest(
                    concept_label="Binary Tree",
                    image_prompt="Show parent and child nodes.",
                )
            )

        self.assertEqual(response.concept_label, "Binary Tree")
        self.assertEqual(response.image_url, "data:image/svg+xml;base64,xyz")
        mock_generate.assert_awaited_once_with(
            "Binary Tree",
            "Show parent and child nodes.",
        )

    async def test_post_quiz_answer_uses_handler_result(self) -> None:
        mock_submit = AsyncMock(
            return_value={
                "component_id": "quiz-1",
                "answer": "stack",
                "is_correct": True,
            }
        )

        with patch("routers.session.submit_quiz_answer", mock_submit):
            result = await post_quiz_answer(
                "session-abc",
                QuizAnswerRequest(component_id="quiz-1", answer="stack"),
            )

        self.assertTrue(result["correct"])
        self.assertTrue(result["is_correct"])
        self.assertEqual(result["feedback"], "Correct!")
        self.assertEqual(result["component_id"], "quiz-1")
        mock_submit.assert_awaited_once_with(component_id="quiz-1", answer="stack")


if __name__ == "__main__":
    unittest.main()
