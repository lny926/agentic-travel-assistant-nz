TEST_CASES = [

    # =====================================================
    # General
    # =====================================================

    {
        "id": "general_01",
        "category": "general",
        "question": "Is Queenstown in the South Island?",
        "history": "",
        "expected_services": ["general"]
    },

    {
        "id": "general_02",
        "category": "general",
        "question": "Which part of Auckland is Botany in?",
        "history": "",
        "expected_services": ["general"]
    },

    {
        "id": "general_03",
        "category": "general",
        "question": "What is Auckland known for?",
        "history": "",
        "expected_services": ["general"]
    },


    # =====================================================
    # Weather
    # =====================================================

    {
        "id": "weather_01",
        "category": "weather",
        "question": "What will the weather be tomorrow in Auckland?",
        "history": "",
        "expected_services": ["weather"]
    },

    {
        "id": "weather_02",
        "category": "weather",
        "question": "Will it rain tomorrow in Queenstown?",
        "history": "",
        "expected_services": ["weather"]
    },

    {
        "id": "weather_03",
        "category": "weather",
        "question": "What is the temperature in Auckland today?",
        "history": "",
        "expected_services": ["weather"]
    },


    # =====================================================
    # Places
    # =====================================================

    {
        "id": "places_01",
        "category": "places",
        "question": "Recommend some restaurants in Auckland.",
        "history": "",
        "expected_services": ["places"]
    },

    {
        "id": "places_02",
        "category": "places",
        "question": "Find some attractions in Queenstown.",
        "history": "",
        "expected_services": ["places"]
    },

    {
        "id": "places_03",
        "category": "places",
        "question": "Where can I eat Chinese food in Auckland?",
        "history": "",
        "expected_services": ["places"]
    },


    # =====================================================
    # RAG
    # =====================================================

    {
        "id": "rag_01",
        "category": "rag",
        "question": (
            "According to the travel knowledge base, "
            "what is the difference between Waiheke Island "
            "and Rangitoto Island?"
        ),
        "history": "",
        "expected_services": ["rag"]
    },

    {
        "id": "rag_02",
        "category": "rag",
        "question": (
            "According to the travel knowledge base, "
            "what is the difference between Queenstown "
            "and Wanaka?"
        ),
        "history": "",
        "expected_services": ["rag"]
    },

    {
        "id": "rag_03",
        "category": "rag",
        "question": (
            "What should a family with young children "
            "do in Auckland on a rainy day?"
        ),
        "history": "",
        "expected_services": ["rag"]
    },


    # =====================================================
    # Analytics
    # =====================================================

    {
        "id": "analytics_01",
        "category": "analytics",
        "question": (
            "How much did international visitors spend "
            "in Auckland in July 2026?"
        ),
        "history": "",
        "expected_services": ["analytics"]
    },

    {
        "id": "analytics_02",
        "category": "analytics",
        "question": (
            "Compare tourism spending between Auckland "
            "and Otago in July 2026."
        ),
        "history": "",
        "expected_services": ["analytics"]
    },

    {
        "id": "analytics_03",
        "category": "analytics",
        "question": (
            "Show the tourism spending trend for "
            "Auckland in 2026."
        ),
        "history": "",
        "expected_services": ["analytics"]
    },


    # =====================================================
    # Multi-tool
    # =====================================================

    {
        "id": "multi_01",
        "category": "multi_tool",
        "question": (
            "Check the weather tomorrow in Auckland "
            "and tell me whether Waiheke Island "
            "would be suitable."
        ),
        "history": "",
        "expected_services": ["weather", "rag"]
    },

    {
        "id": "multi_02",
        "category": "multi_tool",
        "question": (
            "If it rains tomorrow in Auckland, "
            "what should a family with young children do?"
        ),
        "history": "",
        "expected_services": ["weather", "rag"]
    },

    {
        "id": "multi_03",
        "category": "multi_tool",
        "question": (
            "What is the weather in Queenstown tomorrow "
            "and recommend some restaurants there?"
        ),
        "history": "",
        "expected_services": ["weather", "places"]
    },


    # =====================================================
    # Follow-up / conversation context
    # =====================================================

    {
        "id": "memory_01",
        "category": "follow_up",
        "question": "What about the day after?",
        "history": (
            "User: What will the weather be tomorrow in Auckland?\n"
            "Assistant: Tomorrow's Auckland forecast is available."
        ),
        "expected_services": ["weather"]
    },

    {
        "id": "memory_02",
        "category": "follow_up",
        "question": "Can you recommend some restaurants there?",
        "history": (
            "User: What will the weather be tomorrow in Auckland?\n"
            "Assistant: Tomorrow's Auckland forecast is available."
        ),
        "expected_services": ["places"]
    },
]