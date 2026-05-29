# seeds/seed_reviews.py

from db.database import SessionLocal
from models.review import Review

db = SessionLocal()

reviews = [
    Review(
        overall_workload=4,
        content_difficulty=4,
        exam_difficulty=4,
        project_assignment_difficulty=4,
        instructor=5,
        practical_usefulness=4,
        interest_enjoyment=5,
        user_like="Very good introduction course to philosophy. The material was interesting and easy to follow.",
        user_dislike="Some topics felt a little surface-level.",
        course_number="100",
        subject="PHIL",
    ),
    Review(
        overall_workload=4,
        content_difficulty=4,
        exam_difficulty=4,
        project_assignment_difficulty=4,
        instructor=5,
        practical_usefulness=4,
        interest_enjoyment=5,
        user_like="Great class. Covered interesting material, and the discussion sections were engaging and helpful.",
        user_dislike="Lecture style may not work for everyone.",
        course_number="100",
        subject="PHIL",
    ),
    Review(
        overall_workload=3,
        content_difficulty=3,
        exam_difficulty=4,
        project_assignment_difficulty=3,
        instructor=4,
        practical_usefulness=4,
        interest_enjoyment=5,
        user_like="The content was super engaging. Great if you enjoy debating or thinking deeply.",
        user_dislike="Some discussions could feel intimidating at first.",
        course_number="100",
        subject="PHIL",
    ),
    Review(
        overall_workload=4,
        content_difficulty=4,
        exam_difficulty=5,
        project_assignment_difficulty=4,
        instructor=5,
        practical_usefulness=5,
        interest_enjoyment=5,
        user_like="Very fun introduction to philosophy. The ending tied everything together well, and the course showed real implications of philosophy.",
        user_dislike="Sometimes I wanted more depth on certain topics.",
        course_number="100",
        subject="PHIL",
    ),
    Review(
        overall_workload=4,
        content_difficulty=4,
        exam_difficulty=5,
        project_assignment_difficulty=4,
        instructor=5,
        practical_usefulness=4,
        interest_enjoyment=5,
        user_like="Minimal assignments, organized lectures, and interesting material. The class was fun overall.",
        user_dislike="The course can feel broad rather than deeply focused.",
        course_number="100",
        subject="PHIL",
    ),
    Review(
        overall_workload=4,
        content_difficulty=3,
        exam_difficulty=4,
        project_assignment_difficulty=4,
        instructor=4,
        practical_usefulness=4,
        interest_enjoyment=4,
        user_like="The lectures were engaging, and the professor explained the material clearly. Workload was not too heavy.",
        user_dislike="Some ideas could have been explained in more detail.",
        course_number="100",
        subject="PHIL",
    ),
    Review(
        overall_workload=4,
        content_difficulty=4,
        exam_difficulty=4,
        project_assignment_difficulty=4,
        instructor=4,
        practical_usefulness=4,
        interest_enjoyment=4,
        user_like="The Friday discussion groups helped me understand the topics much better.",
        user_dislike="Discussions depended a lot on how active the group was.",
        course_number="100",
        subject="PHIL",
    ),
    Review(
        overall_workload=2,
        content_difficulty=2,
        exam_difficulty=3,
        project_assignment_difficulty=2,
        instructor=3,
        practical_usefulness=2,
        interest_enjoyment=2,
        user_like="Some topics were interesting.",
        user_dislike="I would not recommend it as an easy distribution course because the workload and discussions felt more demanding than expected.",
        course_number="100",
        subject="PHIL",
    ),
    Review(
        overall_workload=3,
        content_difficulty=3,
        exam_difficulty=4,
        project_assignment_difficulty=3,
        instructor=3,
        practical_usefulness=3,
        interest_enjoyment=3,
        user_like="The professor clearly knew the material, and some topics were interesting.",
        user_dislike="Lectures could be rambling and hard to follow because there were no slides.",
        course_number="100",
        subject="PHIL",
    ),
    Review(
        overall_workload=4,
        content_difficulty=3,
        exam_difficulty=4,
        project_assignment_difficulty=4,
        instructor=4,
        practical_usefulness=4,
        interest_enjoyment=5,
        user_like="You learn about many philosophical perspectives and questions. The course is fascinating if you like lecture-style teaching.",
        user_dislike="It requires paying close attention during lecture.",
        course_number="100",
        subject="PHIL",
    ),
    Review(
        overall_workload=3,
        content_difficulty=3,
        exam_difficulty=4,
        project_assignment_difficulty=3,
        instructor=4,
        practical_usefulness=4,
        interest_enjoyment=5,
        user_like="This course challenged me to expand my thinking. I liked the variety of topics and the assessments were not too difficult.",
        user_dislike="Some units felt stronger than others.",
        course_number="100",
        subject="PHIL",
    ),
        Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=4,

        project_assignment_difficulty=4,

        instructor=4,

        practical_usefulness=4,

        interest_enjoyment=4,

        user_like="The course was straightforward, grounded, and easy to follow.",

        user_dislike="Some concepts felt repetitive at times.",

        course_number="130",

        subject="PHIL",

    ),

    Review(

        overall_workload=4,

        content_difficulty=3,

        exam_difficulty=3,

        project_assignment_difficulty=3,

        instructor=4,

        practical_usefulness=4,

        interest_enjoyment=4,

        user_like="Interesting course connecting neuroscience with philosophical perspectives.",

        user_dislike="It is less traditional than most philosophy classes, so it works best if you also like neuroscience.",

        course_number="130",

        subject="PHIL",

    ),

    Review(

        overall_workload=4,

        content_difficulty=3,

        exam_difficulty=3,

        project_assignment_difficulty=3,

        instructor=4,

        practical_usefulness=3,

        interest_enjoyment=4,

        user_like="There were no regular assignments, only three essays across the semester, so the workload felt light.",

        user_dislike="Because the grade depends heavily on essays, each exam felt important and a little stressful.",

        course_number="130",

        subject="PHIL",

    ),

    Review(

        overall_workload=5,

        content_difficulty=4,

        exam_difficulty=4,

        project_assignment_difficulty=4,

        instructor=4,

        practical_usefulness=4,

        interest_enjoyment=4,

        user_like="The slides were clear and the lectures helped explain topics about mind, consciousness, and rationality.",

        user_dislike="It was easy to fall behind if you skipped class too often.",

        course_number="130",

        subject="PHIL",

    ),

    Review(

        overall_workload=4,

        content_difficulty=3,

        exam_difficulty=2,

        project_assignment_difficulty=3,

        instructor=3,

        practical_usefulness=3,

        interest_enjoyment=3,

        user_like="The course became easier to follow near the end once the terminology felt more familiar.",

        user_dislike="At first, many terms were easy to confuse.",

        course_number="130",

        subject="PHIL",

    ),

    Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=2,

        project_assignment_difficulty=3,

        instructor=4,

        practical_usefulness=3,

        interest_enjoyment=3,

        user_like="Lecture content was clear and there were no assignments besides the take-home exams.",

        user_dislike="The grading felt stressful because losing a small number of points could affect the final grade a lot.",

        course_number="130",

        subject="PHIL",

    ),

    Review(

        overall_workload=5,

        content_difficulty=4,

        exam_difficulty=3,

        project_assignment_difficulty=4,

        instructor=4,

        practical_usefulness=4,

        interest_enjoyment=4,

        user_like="Showing up to class and participating made the material much easier to understand.",

        user_dislike="The participation bonus depends on speaking up enough for the professor to recognize you.",

        course_number="130",

        subject="PHIL",

    ),

    Review(

        overall_workload=3,

        content_difficulty=3,

        exam_difficulty=2,

        project_assignment_difficulty=2,

        instructor=3,

        practical_usefulness=2,

        interest_enjoyment=2,

        user_like="Some topics about consciousness were interesting.",

        user_dislike="The written responses felt arbitrary, and I did not like that the assignments seemed to have one correct answer.",

        course_number="130",

        subject="PHIL",

    ),
        Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=4,

        project_assignment_difficulty=4,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=5,

        user_like="Course was very structured and allowed us to explore many aspects of European history.",

        user_dislike="Covers a broad time period so some topics are not explored deeply.",

        course_number="101",

        subject="HIST",

    ),

    Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=4,

        project_assignment_difficulty=3,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=4,

        user_like="Great class for non-history majors. The professor clearly cares about the material and student learning.",

        user_dislike="Cold calling during lecture was stressful sometimes.",

        course_number="101",

        subject="HIST",

    ),

    Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=4,

        project_assignment_difficulty=4,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=5,

        user_like="I learned a lot about European history and genuinely enjoyed the lectures.",

        user_dislike="Some readings felt less important compared to lectures.",

        course_number="101",

        subject="HIST",

    ),

    Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=4,

        project_assignment_difficulty=4,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=5,

        user_like="Amazing introductory history class with engaging lectures and excellent pacing.",

        user_dislike="The course moves quickly through some historical periods.",

        course_number="101",

        subject="HIST",

    ),

    Review(

        overall_workload=3,

        content_difficulty=4,

        exam_difficulty=3,

        project_assignment_difficulty=2,

        instructor=4,

        practical_usefulness=4,

        interest_enjoyment=4,

        user_like="The professor made the content interesting and engaging throughout the semester.",

        user_dislike="Most of the workload was concentrated in the first half of the semester.",

        course_number="101",

        subject="HIST",

    ),

    Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=4,

        project_assignment_difficulty=3,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=4,

        user_like="Very strong introduction to Modern Europe and helpful for improving primary source analysis.",

        user_dislike="Essay writing expectations could have been explained more clearly.",

        course_number="101",

        subject="HIST",

    ),

    Review(

        overall_workload=5,

        content_difficulty=4,

        exam_difficulty=4,

        project_assignment_difficulty=4,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=5,

        user_like="Fantastic lectures with very clear organization and engaging storytelling.",

        user_dislike="The second half of the semester felt much lighter than the beginning.",

        course_number="101",

        subject="HIST",

    ),

    Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=4,

        project_assignment_difficulty=4,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=5,

        user_like="Outstanding introductory history course and a very manageable workload overall.",

        user_dislike="Breadth comes at the expense of depth in some topics.",

        course_number="101",

        subject="HIST",

    ),

    Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=3,

        project_assignment_difficulty=2,

        instructor=4,

        practical_usefulness=3,

        interest_enjoyment=3,

        user_like="The class itself was chill and the lectures were easy to follow.",

        user_dislike="Some assignments were unexpectedly difficult compared to the workload.",

        course_number="101",

        subject="HIST",

    ),

    Review(

        overall_workload=3,

        content_difficulty=3,

        exam_difficulty=3,

        project_assignment_difficulty=2,

        instructor=3,

        practical_usefulness=3,

        interest_enjoyment=3,

        user_like="The material was fascinating and the lectures were interesting.",

        user_dislike="Three major essays early in the semester made the class stressful at first.",

        course_number="101",

        subject="HIST",

    ),

    Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=4,

        project_assignment_difficulty=4,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=5,

        user_like="The professor did a great job making lectures interactive and engaging.",

        user_dislike="Participation expectations could sometimes feel intimidating.",

        course_number="101",

        subject="HIST",

    ),
        Review(

        overall_workload=5,

        content_difficulty=4,

        exam_difficulty=5,

        project_assignment_difficulty=5,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=5,

        user_like="This course was good and felt like a more in-depth version of US history from high school.",

        user_dislike="Some topics may feel familiar if you already took US history before.",

        course_number="112",

        subject="HIST",

    ),

    Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=5,

        project_assignment_difficulty=4,

        instructor=5,

        practical_usefulness=5,

        interest_enjoyment=5,

        user_like="The course was well organized, informative, and clearly presented.",

        user_dislike="The class could have gone deeper into a few specific historical events.",

        course_number="112",

        subject="HIST",

    ),

    Review(

        overall_workload=5,

        content_difficulty=5,

        exam_difficulty=5,

        project_assignment_difficulty=5,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=5,

        user_like="Assignments helped reinforce the key concepts without feeling overwhelming.",

        user_dislike="Most of the workload was light, so students wanting a very intense history class may want something higher level.",

        course_number="112",

        subject="HIST",

    ),

    Review(

        overall_workload=5,

        content_difficulty=4,

        exam_difficulty=5,

        project_assignment_difficulty=5,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=4,

        user_like="The instructor communicated expectations clearly and was available for questions.",

        user_dislike="The course sometimes felt broad because it covered a lot of US history.",

        course_number="112",

        subject="HIST",

    ),

    Review(

        overall_workload=4,

        content_difficulty=4,

        exam_difficulty=5,

        project_assignment_difficulty=4,

        instructor=4,

        practical_usefulness=4,

        interest_enjoyment=4,

        user_like="Very positive learning experience with relevant material and manageable assignments.",

        user_dislike="Some lectures reviewed material I had already seen before.",

        course_number="112",

        subject="HIST",

    ),

    Review(

        overall_workload=5,

        content_difficulty=5,

        exam_difficulty=5,

        project_assignment_difficulty=5,

        instructor=5,

        practical_usefulness=4,

        interest_enjoyment=5,

        user_like="The class was organized very well and easy to follow from week to week.",

        user_dislike="I wish there were more opportunities for discussion.",

        course_number="112",

        subject="HIST",

    ),
]

db.add_all(reviews)
db.commit()
db.close()

print("Seeded realistic PHIL 100 reviews successfully.")