RECOMMENDATIONS = {
    "python": {
        "reason": "Python is widely used for backend development, automation and AI/ML.",
        "topics": [
            "Python fundamentals",
            "OOP",
            "FastAPI",
            "NumPy and Pandas"
        ]
    },

    "react": {
        "reason": "React is commonly used to build modern frontend applications.",
        "topics": [
            "React components",
            "Hooks",
            "State management",
            "API integration"
        ]
    },

    "javascript": {
        "reason": "JavaScript is essential for modern web development.",
        "topics": [
            "ES6+",
            "Async/Await",
            "Promises",
            "DOM and APIs"
        ]
    },

    "mongodb": {
        "reason": "MongoDB is a popular NoSQL database used in MERN applications.",
        "topics": [
            "CRUD operations",
            "MongoDB queries",
            "Indexes",
            "Aggregation"
        ]
    },

    "sql": {
        "reason": "SQL is important for working with relational databases.",
        "topics": [
            "SELECT and WHERE",
            "JOINs",
            "GROUP BY",
            "Window functions"
        ]
    },

    "aws": {
        "reason": "AWS skills are frequently required for cloud deployment and infrastructure.",
        "topics": [
            "EC2",
            "S3",
            "IAM",
            "Cloud deployment"
        ]
    },

    "docker": {
        "reason": "Docker is used to package applications and their dependencies into containers.",
        "topics": [
            "Docker images",
            "Dockerfiles",
            "Containers",
            "Docker Compose"
        ]
    },

    "natural language processing": {
        "reason": "NLP is important for applications that understand and process human language.",
        "topics": [
            "Text preprocessing",
            "TF-IDF",
            "Word embeddings",
            "Transformers"
        ]
    },

    "machine learning": {
        "reason": "Machine learning enables applications to learn patterns from data.",
        "topics": [
            "Supervised learning",
            "Unsupervised learning",
            "Model evaluation",
            "Feature engineering"
        ]
    },

    "deep learning": {
        "reason": "Deep learning is useful for advanced AI applications.",
        "topics": [
            "Neural networks",
            "Backpropagation",
            "CNNs",
            "Transformers"
        ]
    }
}


def generate_recommendations(missing_skills):
    recommendations = []

    for skill in missing_skills:

        skill_lower = skill.lower()

        if skill_lower in RECOMMENDATIONS:

            information = RECOMMENDATIONS[skill_lower]

            recommendations.append({
                "skill": skill,
                "reason": information["reason"],
                "topics": information["topics"]
            })

        else:

            recommendations.append({
                "skill": skill,
                "reason": f"Learning {skill} can improve your match with this job.",
                "topics": [
                    f"{skill} fundamentals",
                    f"{skill} practical projects",
                    f"{skill} interview questions"
                ]
            })

    return recommendations