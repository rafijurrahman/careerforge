"""
Quality and discrimination tests for CV tailoring engine.
Verifies that distinct job descriptions (Backend vs Frontend) select appropriate bullets
and exclude unrelated domain bullets.
"""

from careerforge.core.tailor_engine import tailor_profile


def test_tailor_discriminates_between_backend_and_frontend():
    profile = {
        "personal": {
            "full_name": "Fullstack Developer",
            "email": "dev@example.com",
            "phone": "+1 555-019-2834",
        },
        "skills": {
            "backend": ["Python", "Go", "PostgreSQL", "Redis", "Kafka", "Docker"],
            "frontend": ["React", "TypeScript", "Next.js", "Redux", "Tailwind CSS"],
        },
        "experience": [
            {
                "company": "OmniTech Solutions",
                "title": "Senior Software Engineer",
                "duration": "2021 – Present",
                "bullets": [
                    {
                        "text": "Optimized PostgreSQL queries and Redis caching, cutting p99 API latency from 450ms to 95ms.",
                        "skills": ["PostgreSQL", "Redis", "SQL"],
                        "weight": 8,
                    },
                    {
                        "text": "Architected asynchronous data ingestion pipeline with Go and Kafka handling 20,000 req/s.",
                        "skills": ["Go", "Kafka"],
                        "weight": 8,
                    },
                    {
                        "text": "Engineered responsive client interfaces using React, TypeScript, and Tailwind CSS for 50,000 users.",
                        "skills": ["React", "TypeScript"],
                        "weight": 8,
                    },
                    {
                        "text": "Built state management architecture using Redux Toolkit and Next.js, boosting page load speeds by 40%.",
                        "skills": ["Redux", "Next.js"],
                        "weight": 8,
                    },
                ],
            }
        ],
        "education": [
            {
                "institution": "University of Technology",
                "degree": "B.Sc. in Computer Science",
                "duration": "2017 – 2021",
            }
        ],
    }

    backend_jd = """
    Senior Backend Engineer.
    We are seeking a Backend Engineer with strong expertise in PostgreSQL database tuning,
    Redis caching, distributed API architectures, and Kafka event streaming.
    """

    frontend_jd = """
    Senior Frontend Engineer.
    Looking for a frontend specialist proficient in React, TypeScript, Redux, and Next.js
    to develop high-performance web applications and design systems.
    """

    # 1. Tailor for Backend JD (max 2 bullets)
    backend_tailored, backend_report = tailor_profile(
        profile,
        backend_jd,
        max_bullets_per_role=2,
    )

    selected_backend_bullets = [
        b["text"] if isinstance(b, dict) else b
        for b in backend_tailored["experience"][0]["bullets"]
    ]

    # Verify backend bullets were chosen
    assert any("PostgreSQL" in b or "Redis" in b for b in selected_backend_bullets), (
        f"Backend JD must select database/caching bullet. Got: {selected_backend_bullets}"
    )
    assert any("Kafka" in b or "Go" in b for b in selected_backend_bullets), (
        f"Backend JD must select Kafka/Go pipeline bullet. Got: {selected_backend_bullets}"
    )
    # Verify frontend bullets were excluded
    assert not any("React" in b for b in selected_backend_bullets), (
        f"Backend JD must exclude unrelated React bullet. Got: {selected_backend_bullets}"
    )
    assert not any("Redux" in b for b in selected_backend_bullets), (
        f"Backend JD must exclude unrelated Redux bullet. Got: {selected_backend_bullets}"
    )

    # 2. Tailor for Frontend JD (max 2 bullets)
    frontend_tailored, frontend_report = tailor_profile(
        profile,
        frontend_jd,
        max_bullets_per_role=2,
    )

    selected_frontend_bullets = [
        b["text"] if isinstance(b, dict) else b
        for b in frontend_tailored["experience"][0]["bullets"]
    ]

    # Verify frontend bullets were chosen
    assert any("React" in b for b in selected_frontend_bullets), (
        f"Frontend JD must select React bullet. Got: {selected_frontend_bullets}"
    )
    assert any("Redux" in b or "Next.js" in b for b in selected_frontend_bullets), (
        f"Frontend JD must select Redux/Next.js bullet. Got: {selected_frontend_bullets}"
    )
    # Verify backend bullets were excluded
    assert not any("PostgreSQL" in b for b in selected_frontend_bullets), (
        f"Frontend JD must exclude unrelated PostgreSQL bullet. Got: {selected_frontend_bullets}"
    )
    assert not any("Kafka" in b for b in selected_frontend_bullets), (
        f"Frontend JD must exclude unrelated Kafka bullet. Got: {selected_frontend_bullets}"
    )
