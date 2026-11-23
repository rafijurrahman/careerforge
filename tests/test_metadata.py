"""
Tests for document and binary metadata sanitization.
Verifies that generated documents do not leak tool signatures, OS usernames, or email addresses in metadata.
"""

import os
import re
import tempfile

import docx

from careerforge.core.cv_builder import build_universal_cv


def test_generated_docx_metadata():
    profile = {
        "personal": {
            "full_name": "Jane Developer",
            "email": "jane.dev@example.com",
            "phone": "+1-555-0100",
            "location": "Remote",
        },
        "professional_summary": "Experienced engineer with a focus on clean systems.",
        "skills": {
            "Languages": ["Python", "Go"],
        },
        "experience": [
            {
                "company": "Tech Corp",
                "role": "Software Engineer",
                "period": "2022 - Present",
                "location": "Remote",
                "bullets": ["Maintained backend microservices using Python."],
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        docx_path = os.path.join(tmp_dir, "test_output.docx")
        build_universal_cv(profile, docx_path)

        assert os.path.exists(docx_path)
        doc = docx.Document(docx_path)
        props = doc.core_properties

        # Author and last modified must match profile name exactly
        assert props.author == "Jane Developer"
        assert props.last_modified_by == "Jane Developer"
        assert props.comments == ""
        assert props.category == "Resume"

        # Check for email leaks in any metadata string field
        email_pattern = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
        metadata_fields = [
            props.author,
            props.last_modified_by,
            props.comments,
            props.title,
            props.category,
            props.subject,
            props.keywords,
        ]
        for field in metadata_fields:
            if field:
                assert not email_pattern.search(field), f"Email found in metadata field: {field}"


def test_sample_output_docx_metadata():
    sample_path = os.path.join("examples", "sample_output", "Alex_Rivera_Universal_CV.docx")
    assert os.path.exists(sample_path), "Sample DOCX must exist"

    doc = docx.Document(sample_path)
    props = doc.core_properties

    assert props.author == "Alex Rivera"
    assert props.last_modified_by == "Alex Rivera"
    assert props.comments == ""
    assert props.category == "Resume"

    email_pattern = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
    metadata_fields = [
        props.author,
        props.last_modified_by,
        props.comments,
        props.title,
        props.category,
        props.subject,
        props.keywords,
    ]
    for field in metadata_fields:
        if field:
            assert not email_pattern.search(field), f"Email found in metadata field: {field}"
