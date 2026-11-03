"""Authoritative Midterm 2 membership, shared by delivery and study tools."""
COURSE_VERSION = "midterm2-brian-v1"
CHAPTERS = {
 "6": "Lecture 6: LANs and switching", "7": "Lecture 7: IP packets",
 "8": "Lecture 8: Subnets and forwarding", "9": "Lecture 9: Discovery",
 "10": "Lecture 10: Routing", "11": "Lecture 11: Convergence",
 "12": "Lecture 12: BGP", "13": "Lecture 13: Anycast and multicast",
 "14": "Lecture 14: Wireless", "15": "Lecture 15: Cellular and mobility",
 "16": "Synthesis", "17": "Practice midterm walkthrough", "18": "Exam-day warm-up",
}
MAIN = tuple(str(n) for n in range(6, 17))
SUPPLEMENTS = ("17", "18")
def is_main(dish):
    return str(dish).split(".")[0] in MAIN
def expected_media_count(dishes):
    return len(dishes) + len({d.split(".")[0] for d in dishes}) + 2
