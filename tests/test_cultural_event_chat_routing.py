from unittest.mock import patch

import main


def test_cultural_event_chat_uses_hybrid_recommender():
    question = "I am interested in cultural events. What events do you recommend for me?"

    sample_events = [
        {
            "event_name": "Test Cultural Event",
            "ml_predicted_categories": ["Cultural Event"],
        }
    ]

    with patch.object(main, "get_recommender") as mock_get_recommender:
        mock_get_recommender.return_value.recommend.return_value = sample_events

        response = main.chat(main.ChatRequest(message=question), user={"student_id": 1})

        mock_get_recommender.return_value.recommend.assert_called_once_with(
            question.lower(),
            top_k=5,
        )

    assert response["intent"] == "recommendations"
    assert response["data"] == sample_events
    assert response["data"][0]["ml_predicted_categories"] == ["Cultural Event"]
