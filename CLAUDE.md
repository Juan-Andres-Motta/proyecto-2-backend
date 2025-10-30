For unit test, we focus on testing app logic, not testing Pydantic, FastAPI internals
All unit test must mock external layers (Example: Controller Layer should mock Service Layer)
For every task. First detail it with a plan, mentioning options about the implementation following best standard approaches
The plan should contain what changes, new things would be added, and the side effects it can have in other domains
Do not add code unless is explicitly asked for, or if plan is approved