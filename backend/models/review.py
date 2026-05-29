from sqlalchemy import Column, Integer, String, Text
from db.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)

    overall_workload = Column(Integer)
    content_difficulty = Column(Integer)
    exam_difficulty = Column(Integer)
    project_assignment_difficulty = Column(Integer)

    instructor = Column(Integer)

    practical_usefulness = Column(Integer)
    interest_enjoyment = Column(Integer)

    user_like = Column(Text)
    user_dislike = Column(Text)

    course_number = Column(String)
    subject = Column(String)