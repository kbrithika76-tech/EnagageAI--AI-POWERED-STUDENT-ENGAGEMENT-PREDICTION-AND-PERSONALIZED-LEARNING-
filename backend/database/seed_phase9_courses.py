import os
import sys
from sqlalchemy.orm import Session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.database.db import SessionLocal, engine, Base
from backend.models.course import Course, CourseModule, Concept
from backend.models.content import LearningContent

# Define courses, modules, and concepts hierarchy
courses_data = [
    {
        "title": "Deep Learning",
        "description": "Comprehensive deep learning curriculum covering fundamentals to advanced topics.",
        "difficulty": "intermediate",
        "duration_estimate": "12 Weeks",
        "modules": [
            {
                "title": "Prerequisites",
                "description": "Foundational knowledge required for deep learning.",
                "order_index": 1,
                "concepts": [
                    {"title": "Python Basics for Deep Learning", "order_index": 1},
                    {"title": "NumPy Basics", "order_index": 2},
                    {"title": "Linear Algebra Basics", "order_index": 3},
                    {"title": "Probability Basics", "order_index": 4},
                    {"title": "Machine Learning Basics", "order_index": 5}
                ]
            },
            {
                "title": "Neural Network Foundations",
                "description": "Core concepts of neural networks.",
                "order_index": 2,
                "concepts": [
                    {"title": "What is Deep Learning?", "order_index": 1},
                    {"title": "Neural Networks Basics", "order_index": 2},
                    {"title": "Perceptron", "order_index": 3},
                    {"title": "Activation Functions", "order_index": 4},
                    {"title": "Forward Propagation", "order_index": 5},
                    {"title": "Loss Functions", "order_index": 6}
                ]
            },
            {
                "title": "Neural Network Training",
                "description": "Training techniques and optimizers.",
                "order_index": 3,
                "concepts": [
                    {"title": "Gradient Descent", "order_index": 1},
                    {"title": "Backpropagation", "order_index": 2},
                    {"title": "Optimizers", "order_index": 3},
                    {"title": "Learning Rate", "order_index": 4},
                    {"title": "Batch Size and Epochs", "order_index": 5}
                ]
            },
            {
                "title": "Model Improvement",
                "description": "Techniques to improve model generalization.",
                "order_index": 4,
                "concepts": [
                    {"title": "Overfitting and Underfitting", "order_index": 1},
                    {"title": "Regularization", "order_index": 2},
                    {"title": "Dropout", "order_index": 3},
                    {"title": "Batch Normalization", "order_index": 4},
                    {"title": "Early Stopping", "order_index": 5}
                ]
            },
            {
                "title": "ANN",
                "description": "Artificial Neural Networks and MLPs.",
                "order_index": 5,
                "concepts": [
                    {"title": "ANN / MLP", "order_index": 1},
                    {"title": "Building ANN Models", "order_index": 2},
                    {"title": "ANN Classification", "order_index": 3},
                    {"title": "ANN Regression", "order_index": 4}
                ]
            },
            {
                "title": "CNN",
                "description": "Convolutional Neural Networks.",
                "order_index": 6,
                "concepts": [
                    {"title": "CNN Basics", "order_index": 1},
                    {"title": "Convolution", "order_index": 2},
                    {"title": "Filters and Kernels", "order_index": 3},
                    {"title": "Pooling", "order_index": 4},
                    {"title": "CNN Architecture", "order_index": 5},
                    {"title": "Image Classification", "order_index": 6},
                    {"title": "Transfer Learning", "order_index": 7}
                ]
            },
            {
                "title": "Sequential Models",
                "description": "RNN based architectures.",
                "order_index": 7,
                "concepts": [
                    {"title": "RNN", "order_index": 1},
                    {"title": "Vanishing Gradient Problem", "order_index": 2},
                    {"title": "LSTM", "order_index": 3},
                    {"title": "GRU", "order_index": 4},
                    {"title": "Bidirectional RNN", "order_index": 5},
                    {"title": "Sequence Classification", "order_index": 6}
                ]
            },
            {
                "title": "NLP",
                "description": "Natural Language Processing foundations.",
                "order_index": 8,
                "concepts": [
                    {"title": "NLP Basics", "order_index": 1},
                    {"title": "Tokenization", "order_index": 2},
                    {"title": "Word Embeddings", "order_index": 3},
                    {"title": "Sequence Models for NLP", "order_index": 4},
                    {"title": "Attention Mechanism", "order_index": 5}
                ]
            },
            {
                "title": "Transformers",
                "description": "Transformer architecture and applications.",
                "order_index": 9,
                "concepts": [
                    {"title": "Transformer Basics", "order_index": 1},
                    {"title": "Self-Attention", "order_index": 2},
                    {"title": "Encoder and Decoder", "order_index": 3},
                    {"title": "BERT Concept", "order_index": 4},
                    {"title": "Generative AI Basics", "order_index": 5}
                ]
            },
            {
                "title": "Advanced Deep Learning",
                "description": "State‑of‑the‑art deep learning techniques.",
                "order_index": 10,
                "concepts": [
                    {"title": "Autoencoders", "order_index": 1},
                    {"title": "GANs", "order_index": 2},
                    {"title": "Transfer Learning (Advanced)", "order_index": 3},
                    {"title": "Fine-Tuning", "order_index": 4},
                    {"title": "Model Evaluation", "order_index": 5}
                ]
            },
            {
                "title": "Practical Deep Learning",
                "description": "Hands‑on frameworks and deployment.",
                "order_index": 11,
                "concepts": [
                    {"title": "TensorFlow Basics", "order_index": 1},
                    {"title": "Keras Basics", "order_index": 2},
                    {"title": "PyTorch Basics", "order_index": 3},
                    {"title": "Model Saving and Loading", "order_index": 4},
                    {"title": "Model Deployment", "order_index": 5}
                ]
            },
            {
                "title": "Projects",
                "description": "Capstone projects applying deep learning.",
                "order_index": 12,
                "concepts": [
                    {"title": "Image Classification Project", "order_index": 1},
                    {"title": "Sentiment Analysis Project", "order_index": 2},
                    {"title": "Student Engagement Prediction Project", "order_index": 3},
                    {"title": "End‑to‑End Deep Learning Project", "order_index": 4}
                ]
            }
        ]
    },
    {
        "title": "Python",
        "description": "Beginner to intermediate Python programming curriculum.",
        "difficulty": "beginner",
        "duration_estimate": "8 Weeks",
        "modules": [
            {"title": "Python Fundamentals", "order_index": 1, "concepts": [
                {"title": "Introduction to Python", "order_index": 1},
                {"title": "Variables", "order_index": 2},
                {"title": "Data Types", "order_index": 3},
                {"title": "Input and Output", "order_index": 4},
                {"title": "Operators", "order_index": 5}
            ]},
            {"title": "Control Flow", "order_index": 2, "concepts": [
                {"title": "If/Else", "order_index": 1},
                {"title": "For Loop", "order_index": 2},
                {"title": "While Loop", "order_index": 3},
                {"title": "Break/Continue", "order_index": 4},
                {"title": "Nested Loops", "order_index": 5}
            ]},
            {"title": "Data Structures", "order_index": 3, "concepts": [
                {"title": "Lists", "order_index": 1},
                {"title": "Tuples", "order_index": 2},
                {"title": "Sets", "order_index": 3},
                {"title": "Dictionaries", "order_index": 4},
                {"title": "Strings", "order_index": 5}
            ]},
            {"title": "Functions", "order_index": 4, "concepts": [
                {"title": "Functions", "order_index": 1},
                {"title": "Parameters", "order_index": 2},
                {"title": "Return Values", "order_index": 3},
                {"title": "Lambda", "order_index": 4},
                {"title": "Scope", "order_index": 5}
            ]},
            {"title": "OOP", "order_index": 5, "concepts": [
                {"title": "Classes", "order_index": 1},
                {"title": "Objects", "order_index": 2},
                {"title": "Constructors", "order_index": 3},
                {"title": "Inheritance", "order_index": 4},
                {"title": "Polymorphism", "order_index": 5},
                {"title": "Encapsulation", "order_index": 6}
            ]},
            {"title": "File & Error Handling", "order_index": 6, "concepts": [
                {"title": "File Handling", "order_index": 1},
                {"title": "Exceptions", "order_index": 2},
                {"title": "Modules", "order_index": 3},
                {"title": "Packages", "order_index": 4}
            ]},
            {"title": "Data Science Python", "order_index": 7, "concepts": [
                {"title": "NumPy", "order_index": 1},
                {"title": "Pandas", "order_index": 2},
                {"title": "Matplotlib", "order_index": 3},
                {"title": "Data Preprocessing", "order_index": 4}
            ]},
            {"title": "Projects", "order_index": 8, "concepts": [
                {"title": "Beginner Python Project", "order_index": 1},
                {"title": "Data Analysis Project", "order_index": 2},
                {"title": "Mini Application", "order_index": 3}
            ]}
        ]
    }
    # Additional courses (Java, Data Structures & Algorithms, SQL, etc.) can be added similarly.
]

def seed_courses():
    db: Session = SessionLocal()
    try:
        # Insert Courses, Modules, Concepts if they do not exist
        for cdata in courses_data:
            existing_course = db.query(Course).filter(Course.title == cdata["title"]).first()
            if existing_course:
                course = existing_course
            else:
                course = Course(
                    title=cdata["title"],
                    description=cdata.get("description"),
                    difficulty=cdata.get("difficulty", "beginner"),
                    duration_estimate=cdata.get("duration_estimate"),
                    is_active=True,
                    order_index=cdata.get("order_index", 0)
                )
                db.add(course)
                db.flush()  # obtain course.id

            # Modules
            for mdata in cdata.get("modules", []):
                existing_module = (
                    db.query(CourseModule)
                    .filter(CourseModule.course_id == course.id, CourseModule.title == mdata["title"])
                    .first()
                )
                if existing_module:
                    module = existing_module
                else:
                    module = CourseModule(
                        course_id=course.id,
                        title=mdata["title"],
                        description=mdata.get("description"),
                        order_index=mdata.get("order_index", 0),
                        learning_objectives=mdata.get("learning_objectives")
                    )
                    db.add(module)
                    db.flush()

                # Concepts
                for condata in mdata.get("concepts", []):
                    existing_concept = (
                        db.query(Concept)
                        .filter(Concept.module_id == module.id, Concept.title == condata["title"])
                        .first()
                    )
                    if not existing_concept:
                        concept = Concept(
                            module_id=module.id,
                            title=condata["title"],
                            description=condata.get("description"),
                            order_index=condata.get("order_index", 0)
                        )
                        db.add(concept)
        db.commit()
        print("Courses, modules, and concepts seeded successfully.")

        # Map existing videos to concepts
        unmapped_videos = db.query(LearningContent).filter(LearningContent.concept_id.is_(None)).all()
        for video in unmapped_videos:
            # Try to find a concept with the same title (case‑insensitive)
            concept = db.query(Concept).filter(Concept.title.ilike(video.title)).first()
            if not concept:
                # Fallback: find first concept of the course that matches the video's module field
                related_module = db.query(CourseModule).join(Course).filter(CourseModule.title.ilike(video.module)).first()
                if related_module:
                    concept = db.query(Concept).filter(Concept.module_id == related_module.id).order_by(Concept.order_index).first()
            if concept:
                video.concept_id = concept.id
        db.commit()
        print(f"Mapped {len(unmapped_videos)} existing videos to concepts.")
    finally:
        db.close()

if __name__ == "__main__":
    # Ensure tables exist (Course tables already created by migration)
    Base.metadata.create_all(bind=engine)
    seed_courses()
