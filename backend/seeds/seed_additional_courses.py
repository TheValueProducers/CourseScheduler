from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import Column, Integer as SA_Integer, MetaData, String as SA_String, Table, Text as SA_Text, inspect, select
from sqlalchemy import Boolean as SA_Boolean
from sqlalchemy import Float as SA_Float
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.types import JSON

# Allow running this script directly via: python seeds/seed_additional_courses.py
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from db.database import SessionLocal, engine
from parsers.parse_schedule import parse_prereq_expr


def _stage(message: str) -> None:
    print(f"[seed_additional_courses] {message}", flush=True)


def _load_courses_table(db_engine: Engine) -> Table:
    inspector = inspect(db_engine)
    metadata = MetaData()

    if not inspector.has_table("courses"):
        _stage("'courses' table not found; creating table")
        courses_table = Table(
            "courses",
            metadata,
            Column("code", SA_String(16), primary_key=True),
            Column("subject", SA_String(8), nullable=False),
            Column("course_number", SA_Integer, nullable=False),
            Column("long_title", SA_Text, nullable=True),
            Column("offered_terms", JSON, nullable=True),
            Column("credit_hours", SA_Float, nullable=True),
            Column("distribution", SA_String(64), nullable=True),
            Column("analyzing_diversity", SA_Boolean, nullable=False, default=False),
            Column("cross_list", JSON, nullable=True),
            Column("prereq_tree", JSON, nullable=True),
        )
        metadata.create_all(db_engine, tables=[courses_table])
        return courses_table

    return Table("courses", metadata, autoload_with=db_engine)


def _additional_courses() -> List[Dict[str, Any]]:
    comp_345_raw_text = """COMP 345 001 (CRN: 16250)\nFOUNDATIONS OF ML\nLong Title:\nFOUNDATIONS OF MACHINE LEARNING\nDepartment:\nComputer Science\nInstructor:\nSubramanian, Devika\nMeeting:\n9:25AM - 10:40AM TR (24-AUG-2026 - 4-DEC-2026)\nPart of Term:\nFull Term\nGrade Mode:\nStandard Letter\nCourse Type:\nLecture\nLanguage of Instruction:\nTaught in English\nMethod of Instruction:\nFace to Face\nCredit Hours:\n3\nRestrictions:\nMust be enrolled in one of the following Level(s):\nUndergraduate Professional\nVisiting Undergraduate\nUndergraduate\nPrerequisites:\nCOMP 282 AND STAT 315\nSection Max Enrollment:\n50\nSection Enrolled:\n19\nEnrollment data as of:\n28-JUN-2026 5:48AM\nAdditional Fees:\nNone\nFinal Exam:\nScheduled Final Exam-OTR Room\nDescription:\nThis course offers a comprehensive introduction to the foundational principles and practical techniques of machine learning. Students will explore key concepts such as learning from data, concept classes or models, learning objectives, loss functions, and the formulation of machine learning as an optimization problem. The course will also include ethical considerations in AI and discuss topics including bias and fairness. They will gain an understanding of core ideas in generalization, model evaluation, and trade-offs between performance and resource efficiency. The course emphasizes hands-on experience in implementing and understanding ML algorithms, with a strong focus on thorough evaluation and monitoring. Topics include supervised and unsupervised learning, linear models for regression and classification, non-linear models such as decision trees, ensemble methods, and neural networks. Additional topics include nearest neighbor search and probabilistic modeling techniques such as naive Bayes. Students will also learn basic unsupervised learning methods including clustering, PCA, and other dimensionality reduction techniques. The course covers machine learning evaluation strategies, including accuracy metrics, efficiency trade-offs, and best practices for model monitoring. Mutually Exclusive: Cannot register for COMP 345 if student has credit for COMP 447/COMP 546."""
    comp_346_raw_text = """Course Catalog - 2025-2026\nCOMP 346 - INTRO TO AI\nLong Title:\nINTRODUCTION TO ARTIFICAL INTELLIGENCE\nDepartment:\nComputer Science\nGrade Mode:\nStandard Letter\nLanguage of Instruction:\nTaught in English\nCourse Type:\nLecture\nCredit Hours:\n3\nRestrictions:\nMust be enrolled in one of the following Level(s):\nUndergraduate Professional\nVisiting Undergraduate\nUndergraduate\nPrerequisite(s):\nCOMP 215 AND STAT 315 AND COMP 282\nDescription:\nNo subject unleashes the spirit of innovation like artificial intelligence (AI). Think of companies like Deep Mind, OpenAI, Google, Hugging Face, and technologies like speech recognition, language translation, question answering systems, autonomous driving, household robots, chatbots, text-to-image generators, each of which embodies core algorithms in AI. COMP 346 offers an introduction to AI, which is the discipline of designing agents that make decisions and solve problems in the real world. The course covers the mathematical and computational concepts needed to design, engineer, and evaluate AI agents that do the right thing in the face of limited computational resources and limited information. The course draws on computer science, probability theory, statistics, optimization, game theory, logic, and decision theory. COMP 346 is a required course for the AI major. It can also be taken as part of a general education in computer science, as grounding for future research in AI, or to gain familiarity with AI algorithms for application in other fields."""
    comp_348_raw_text = """Course Catalog - 2025-2026\nCOMP 348 - INTRODUCTION TO DEEP LEARNING\nLong Title:\nINTRODUCTION TO DEEP LEARNING\nDepartment:\nComputer Science\nGrade Mode:\nStandard Letter\nLanguage of Instruction:\nTaught in English\nCourse Type:\nLecture\nCredit Hours:\n3\nRestrictions:\nMust be enrolled in one of the following Level(s):\nUndergraduate Professional\nVisiting Undergraduate\nUndergraduate\nPrerequisite(s):\nCOMP 345\nDescription:\nThis course explores the design landscape of deep neural network architectures and optimization strategies, with the primary goal of giving students skills and knowledge that will help them as practitioners. After completing the course, students should be able to evaluate the tradeoffs of using different neural network building blocks and training strategies and understand how to choose the types of models that are better suited for a task. Specific topics covered include multi-layer perceptrons, backpropagation, convolutional neural networks, recurrent neural networks, autoregressive networks, and deep generative models. The notion of inner representation and embeddings as a semantic representation of inputs. Understand self-supervised vs supervised representation learning, including generative pre-training and brief introduction to multimodal representation learning. Case studies from applications such as computer vision and natural language processing will be used to illustrate the utility of various deep neural network designs and training strategies."""
    comp_329_raw_text = """Course Catalog - 2025-2026\nCOMP 329 - SYSTEMS FOR AI\nLong Title:\nSYSTEMS FOR ARTIFICAL INTELLIGENCE\nDepartment:\nComputer Science\nGrade Mode:\nStandard Letter\nLanguage of Instruction:\nTaught in English\nCourse Type:\nLecture\nCredit Hours:\n3\nRestrictions:\nMust be enrolled in one of the following Level(s):\nUndergraduate Professional\nVisiting Undergraduate\nUndergraduate\nPrerequisite(s):\nCOMP 215 AND COMP 222 AND COMP 345\nDescription:\nThis course explores the systems and infrastructure that are used for modern artificial intelligence (AI) applications. As both data and computation are crucial to modern AI, the course will cover the theory and practice of systems for data processing and systems for AI computation. On the data side, the course will cover systems that facilitate data management, cleaning and preparation, with a focus on the relational model, relational database systems, as well as Big Data systems such as Apache Spark. On the computation side, the course will cover the use of modern AI accelerators such as GPUs, the theory and practice of parallelizing AI models across multiple computational units, with emphasis on understanding the hardware-software interface."""
    comp_456_raw_text = """COMP 456 - AI SENIOR DESIGN I\nLong Title:\nAI SENIOR DESIGN I\nDepartment:\nComputer Science\nGrade Mode:\nStandard Letter\nLanguage of Instruction:\nTaught in English\nCourse Type:\nLecture/Laboratory\nCredit Hours:\n4\nRestrictions:\nMust be enrolled in one of the following Level(s):\nUndergraduate Professional\nVisiting Undergraduate\nUndergraduate\nPrerequisite(s):\nCOMP 346\nDescription:\nIn this first of a two-course sequence, students will work as part of a team tasked with designing, building, and evaluating a complex, real-world system for which Artificial Intelligence (AI) provides a significant component. Students may work in conjunction with senior design teams from other engineering disciplines as part of a larger design effort for which AI provides an important functionality, or as part of an AI-major-only team concerned with designing and implementing an intelligent system of significant complexity. Teams will consider all stages of system design and implementation, from initial concept, through design and planning, prototyping, testing, and delivery and evaluation of a complete intelligent system. Technical communication, including written communication and oral communication, will be covered. In addition to the practical design and implementation component, classroom lectures will focus on the processes, techniques, and technologies necessary to engineer a real-world, intelligent system. Note that both COMP 456 and COMP 457 must be taken in sequence, in the same academic year."""
    comp_457_raw_text = """Course Catalog - 2026-2027\nCOMP 457 - AI SENIOR DESIGN II\nLong Title:\nAI SENIOR DESIGN II\nDepartment:\nComputer Science\nGrade Mode:\nStandard Letter\nLanguage of Instruction:\nTaught in English\nCourse Type:\nLecture/Laboratory\nCredit Hours:\n4\nRestrictions:\nMust be enrolled in one of the following Level(s):\nUndergraduate Professional\nVisiting Undergraduate\nUndergraduate\nPrerequisite(s):\nCOMP 456 AND COMP 329 AND COMP 348\nDescription:\nIn this second of a two-course sequence, students will work as part of a team tasked with designing, building, and evaluating a complex, real-world system for which Artificial Intelligence (AI) provides a significant component. Students may work in conjunction with senior design teams from other engineering disciplines as part of a larger design effort for which AI provides an important functionality, or as part of an AI-major-only team concerned with designing and implementing an intelligent system of significant complexity. Teams will consider all stages of system design and implementation, from initial concept, through design and planning, prototyping, testing, and delivery and evaluation of a complete intelligent system. Technical communication, including written communication and oral communication, will be covered. In addition to the practical design and implementation component, classroom lectures will focus on the processes, techniques, and technologies necessary to engineer a real-world, intelligent system. Note that both COMP 456 and COMP 457 must be taken in sequence, in the same academic year."""

    return [
        {
            "code": "COMP 345",
            "subject": "COMP",
            "course_number": 345,
            "long_title": "FOUNDATIONS OF MACHINE LEARNING",
            "offered_terms": ["Fall", "Spring"],
            "credit_hours": 3.0,
            "distribution": None,
            "analyzing_diversity": False,
            "cross_list": [],
            "prereq_tree": parse_prereq_expr("COMP 282 AND STAT 315"),
            "term_code": 202710,
            "raw_text": comp_345_raw_text,
        },
        {
            "code": "COMP 346",
            "subject": "COMP",
            "course_number": 346,
            "long_title": "INTRODUCTION TO ARTIFICAL INTELLIGENCE",
            "offered_terms": ["Spring"],
            "credit_hours": 3.0,
            "distribution": None,
            "analyzing_diversity": False,
            "cross_list": [],
            "prereq_tree": parse_prereq_expr("COMP 215 AND STAT 315 AND COMP 282"),
            "term_code": 202720,
            "raw_text": comp_346_raw_text,
        },
        {
            "code": "COMP 348",
            "subject": "COMP",
            "course_number": 348,
            "long_title": "INTRODUCTION TO DEEP LEARNING",
            "offered_terms": ["Fall"],
            "credit_hours": 3.0,
            "distribution": None,
            "analyzing_diversity": False,
            "cross_list": [],
            "prereq_tree": parse_prereq_expr("COMP 345"),
            "term_code": 202710,
            "raw_text": comp_348_raw_text,
        },
        {
            "code": "COMP 329",
            "subject": "COMP",
            "course_number": 329,
            "long_title": "SYSTEMS FOR ARTIFICAL INTELLIGENCE",
            "offered_terms": ["Fall"],
            "credit_hours": 3.0,
            "distribution": None,
            "analyzing_diversity": False,
            "cross_list": [],
            "prereq_tree": parse_prereq_expr("COMP 215 AND COMP 222 AND COMP 345"),
            "term_code": 202710,
            "raw_text": comp_329_raw_text,
        },
        {
            "code": "COMP 456",
            "subject": "COMP",
            "course_number": 456,
            "long_title": "AI SENIOR DESIGN I",
            "offered_terms": ["Fall"],
            "credit_hours": 4.0,
            "distribution": None,
            "analyzing_diversity": False,
            "cross_list": [],
            "prereq_tree": parse_prereq_expr("COMP 346"),
            "term_code": 202710,
            "raw_text": comp_456_raw_text,
        },
        {
            "code": "COMP 457",
            "subject": "COMP",
            "course_number": 457,
            "long_title": "AI SENIOR DESIGN II",
            "offered_terms": ["Spring"],
            "credit_hours": 4.0,
            "distribution": None,
            "analyzing_diversity": False,
            "cross_list": [],
            "prereq_tree": parse_prereq_expr("COMP 456 AND COMP 329 AND COMP 348"),
            "term_code": 202720,
            "raw_text": comp_457_raw_text,
        }
    ]


def seed_additional_courses() -> Dict[str, int]:
    courses = _additional_courses()
    courses_table = _load_courses_table(engine)

    insertable_columns = {col.name for col in courses_table.columns}
    inserted = 0
    updated = 0

    with SessionLocal() as db:
        assert isinstance(db, Session)

        existing_codes = {
            row[0]
            for row in db.execute(select(courses_table.c.code)).all()
            if row and row[0] is not None
        }

        for course in courses:
            code = course["code"]
            payload = {k: v for k, v in course.items() if k in insertable_columns}

            if code in existing_codes:
                db.execute(
                    courses_table.update()
                    .where(courses_table.c.code == code)
                    .values(**payload)
                )
                updated += 1
            else:
                db.execute(courses_table.insert().values(**payload))
                inserted += 1

        db.commit()

    _stage(f"finished: inserted={inserted}, updated={updated}")
    return {"inserted": inserted, "updated": updated}


if __name__ == "__main__":
    result = seed_additional_courses()
    print(f"Seed complete: inserted={result['inserted']}, updated={result['updated']}")
