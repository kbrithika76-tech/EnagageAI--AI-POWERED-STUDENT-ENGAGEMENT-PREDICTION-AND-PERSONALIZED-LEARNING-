"""
EngageAI Backend — routes/quizzes.py
GET  /quizzes
GET  /quizzes/{id}
POST /quizzes/{id}/attempt
POST /quizzes
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict

from backend.database import get_db
from backend.models.user import User
from backend.models.quiz import Quiz, QuizQuestion, QuizAttempt
from backend.models.activity import ActivityEvent
from backend.auth.dependencies import get_current_user, require_teacher

router = APIRouter(prefix="/quizzes", tags=["Quizzes & Assessments"])


class AnswerSubmit(BaseModel):
    answers: Dict[int, str]  # {question_id: chosen_option 'a'/'b'/'c'/'d'}
    completion_time_seconds: Optional[int] = 60


class QuizQuestionCreate(BaseModel):
    question: str
    option_a: str
    option_b: str
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_option: str
    marks: int = 1


class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None
    module: str = "General"
    topic: Optional[str] = None
    difficulty: str = "beginner"
    questions: List[QuizQuestionCreate]


@router.get("")
def get_quizzes(
    module: Optional[str] = None,
    difficulty: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Quiz).filter(Quiz.is_active == True)
    if module:
        query = query.filter(Quiz.module == module)
    if difficulty:
        query = query.filter(Quiz.difficulty == difficulty)

    quizzes = query.all()
    
    # Get user attempts
    attempts = db.query(QuizAttempt).filter(QuizAttempt.student_id == current_user.id).all()
    attempts_map = {}
    for a in attempts:
        if a.quiz_id not in attempts_map or a.score_pct > attempts_map[a.quiz_id].score_pct:
            attempts_map[a.quiz_id] = a

    res = []
    for q in quizzes:
        att = attempts_map.get(q.id)
        res.append({
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "module": q.module,
            "topic": q.topic,
            "difficulty": q.difficulty,
            "question_count": len(q.questions),
            "user_attempt": {
                "attempted": att is not None,
                "best_score_pct": att.score_pct if att else 0.0,
                "last_attempted_at": att.completed_at.isoformat() if att and att.completed_at else None
            },
            "video_id": q.video_id
        })
    return res


@router.get("/{quiz_id}")
def get_quiz_detail(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.is_active == True).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    questions = []
    for q in quiz.questions:
        questions.append({
            "id": q.id,
            "question": q.question,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "marks": q.marks
        })

    return {
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "module": quiz.module,
        "topic": quiz.topic,
        "difficulty": quiz.difficulty,
        "video_id": quiz.video_id,
        "questions": questions
    }


@router.post("/{quiz_id}/attempt")
def submit_quiz_attempt(
    quiz_id: int,
    body: AnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    questions = {q.id: q for q in quiz.questions}
    total_marks = sum(q.marks for q in quiz.questions)
    earned_marks = 0.0

    for q_id, choice in body.answers.items():
        q_obj = questions.get(int(q_id))
        if q_obj and choice.lower() == q_obj.correct_option.lower():
            earned_marks += q_obj.marks

    score_pct = (earned_marks / total_marks * 100.0) if total_marks > 0 else 0.0

    # Determine attempt number
    prev_attempts = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == quiz_id,
        QuizAttempt.student_id == current_user.id
    ).count()

    # Save Attempt
    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=current_user.id,
        score=earned_marks,
        total_marks=total_marks,
        score_pct=score_pct,
        completion_time=body.completion_time_seconds,
        answers_json=str(body.answers),
        attempt_number=prev_attempts + 1,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    db.add(attempt)

    # Add Activity Event for ML Pipeline
    act_event = ActivityEvent(
        student_id=current_user.id,
        quiz_id=quiz_id,
        event_type="QUIZ_COMPLETED",
        duration=body.completion_time_seconds,
        timestamp=datetime.utcnow()
    )
    db.add(act_event)

    db.commit()
    db.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz_id,
        "score": earned_marks,
        "total_marks": total_marks,
        "score_pct": round(score_pct, 1),
        "passed": score_pct >= 50.0
    }


@router.get("/{quiz_id}/attempt/latest")
def get_latest_quiz_attempt(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import ast

    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == quiz_id,
        QuizAttempt.student_id == current_user.id
    ).order_by(QuizAttempt.completed_at.desc()).first()

    if not attempt:
        raise HTTPException(status_code=404, detail="No attempt found for this quiz.")

    # Parse submitted answers
    try:
        submitted_answers = ast.literal_eval(attempt.answers_json) if attempt.answers_json else {}
    except (ValueError, SyntaxError):
        submitted_answers = {}

    questions_info = []
    for q in quiz.questions:
        user_ans = submitted_answers.get(str(q.id)) or submitted_answers.get(q.id)
        questions_info.append({
            "id": q.id,
            "question": q.question,
            "user_answer": user_ans,
            "correct_option": q.correct_option,
            "is_correct": user_ans and user_ans.lower() == q.correct_option.lower(),
            "marks": q.marks,
            "explanation": q.explanation,
            "options": {
                "a": q.option_a,
                "b": q.option_b,
                "c": q.option_c,
                "d": q.option_d,
            }
        })

    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz_id,
        "quiz_title": quiz.title,
        "score": attempt.score,
        "total_marks": attempt.total_marks,
        "score_pct": round(attempt.score_pct, 1),
        "passed": attempt.score_pct >= 50.0,
        "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
        "questions_detail": questions_info
    }


@router.post("", status_code=201)
def create_quiz(
    body: QuizCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    quiz = Quiz(
        title=body.title,
        description=body.description,
        module=body.module,
        topic=body.topic,
        difficulty=body.difficulty,
        created_by=current_user.id,
        created_at=datetime.utcnow()
    )
    db.add(quiz)
    db.flush()

    for idx, q in enumerate(body.questions):
        qq = QuizQuestion(
            quiz_id=quiz.id,
            question=q.question,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            correct_option=q.correct_option,
            marks=q.marks,
            order_index=idx
        )
        db.add(qq)

    db.commit()
    db.refresh(quiz)
    return {"message": "Quiz created successfully", "quiz_id": quiz.id}
