E2E_TEST_CASES = [

    # =====================================================
    # General
    # =====================================================

    {
        "id": "e2e_general_01",
        "category": "general",
        "question": (
            "Is Queenstown in the South Island?"
        ),
        "expected_services": [
            "general"
        ],
        "expected_sources": []
    },


    # =====================================================
    # Weather
    # =====================================================

    {
        "id": "e2e_weather_01",
        "category": "weather",
        "question": (
            "What will the weather be "
            "tomorrow in Auckland?"
        ),
        "expected_services": [
            "weather"
        ],
        "expected_sources": [
            "Open-Meteo"
        ]
    },


    # =====================================================
    # Places
    # =====================================================

    {
        "id": "e2e_places_01",
        "category": "places",
        "question": (
            "Recommend some restaurants "
            "in Auckland."
        ),
        "expected_services": [
            "places"
        ],
        "expected_sources": []
    },


    # =====================================================
    # RAG
    # =====================================================

    {
        "id": "e2e_rag_01",
        "category": "rag",
        "question": (
            "According to the travel knowledge base, "
            "what is the difference between "
            "Waiheke Island and Rangitoto Island?"
        ),
        "expected_services": [
            "rag"
        ],
        "expected_sources": [
            "auckland.md"
        ]
    },

    {
        "id": "e2e_rag_02",
        "category": "rag",
        "question": (
            "According to the travel knowledge base, "
            "what is the difference between "
            "Queenstown and Wanaka?"
        ),
        "expected_services": [
            "rag"
        ],
        "expected_sources": [
            "queenstown.md"
        ]
    },


    # =====================================================
    # Analytics
    # =====================================================

    {
        "id": "e2e_analytics_01",
        "category": "analytics",
        "question": (
            "How much did international visitors "
            "spend in Auckland in July 2026?"
        ),
        "expected_services": [
            "analytics"
        ],
        "expected_sources": []
    },

    {
        "id": "e2e_analytics_02",
        "category": "analytics",
        "question": (
            "Compare tourism spending between "
            "Auckland and Otago in July 2026."
        ),
        "expected_services": [
            "analytics"
        ],
        "expected_sources": []
    },


    # =====================================================
    # Multi-tool
    # =====================================================

    {
        "id": "e2e_multi_01",
        "category": "multi_tool",
        "question": (
            "Check the weather tomorrow in Auckland "
            "and tell me whether Waiheke Island "
            "would be suitable."
        ),
        "expected_services": [
            "weather",
            "rag"
        ],
        "expected_sources": [
            "Open-Meteo",
            "auckland.md"
        ]
    },

    {
        "id": "e2e_multi_02",
        "category": "multi_tool",
        "question": (
            "What is the weather in Queenstown tomorrow "
            "and recommend some restaurants there?"
        ),
        "expected_services": [
            "weather",
            "places"
        ],
        "expected_sources": [
            "Open-Meteo"
        ]
    },


    # =====================================================
    # Hypothetical weather + RAG
    # =====================================================

    {
        "id": "e2e_rag_03",
        "category": "rag",
        "question": (
            "What should a family with young children "
            "do in Auckland on a rainy day?"
        ),
        "expected_services": [
            "rag"
        ],
        "expected_sources": [
            "auckland.md"
        ]
    },
]