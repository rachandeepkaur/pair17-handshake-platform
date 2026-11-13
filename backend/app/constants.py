"""Enumerated values shared by schemas and services (formerly on the SQL models)."""

JOB_CATEGORIES = ("full_time", "part_time", "on_campus", "internship")
APPLICATION_STATUSES = ("Pending", "Reviewed", "Declined")
MEMBER_ROLES = ("owner", "admin", "recruiter", "hiring_manager", "viewer")
INVITABLE_ROLES = ("admin", "recruiter", "hiring_manager", "viewer")
