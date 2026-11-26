1. use pydantic-settings to import from .env file
SQLAlchemy + Pydantic vs SQLModel 
You'd still end up with separate models. Your User table has hashed_password, and that must never appear in an API response. So even with SQLModel you'd write a separate UserRead without it. Most of the duplication it's meant to remove comes back anyway.
It gets in the way for anything advanced. Constraints, relationships and enums often mean dropping down to raw SQLAlchemy inside SQLModel anyway.
It's less common in real codebases. Client projects and most interviewers expect SQLAlchemy plus Pydantic, so it's the more useful thing to know.
Your models are already done. Switching now costs you time and gets you nothing.

When would SQLModel be the better choice? Quick prototypes and small apps where the database model and the API shape are nearly identical.

That makes a nice design-decision entry for your learnings file: "Kept SQLAlchemy and Pydantic separate so the database model and the API contract can change independently, e.g. so hashed_password never leaks into a response.


2. Added a constraint, it silently didn't apply, because create_all doesn't migrate existing tables. That's why production uses Alembic.

3. Take user_id out of CartItemCreate. This is the important one. If the client sends user_id, anyone can add items to someone else's cart just by changing the number. The user always comes from the login token (get_current_user), never from the request body. This kind of bug has a name: IDOR, insecure direct object reference.

