def generate_roadmap(data):
    strengths = []
    weaknesses = []
    roadmap = []

    if data["has_readme"]:
        strengths.append("Basic project documentation is present.")
    else:
        weaknesses.append("Missing or minimal README documentation.")
        roadmap.append("Add a detailed README with setup and usage instructions.")

    if data["has_tests"]:
        strengths.append("Test structure exists.")
    else:
        weaknesses.append("No test coverage found.")
        roadmap.append("Write unit and integration tests.")

    if len(data["commits"]) > 10:
        strengths.append("Consistent commit history.")
    else:
        weaknesses.append("Infrequent or inconsistent commits.")
        roadmap.append("Commit more frequently with meaningful messages.")

    if len(data["languages"]) > 0:
        strengths.append("Clear tech stack usage.")
    else:
        weaknesses.append("Tech stack not clearly defined.")
        roadmap.append("Define and structure the tech stack clearly.")

    roadmap.append("Refactor large files for better readability and modularity.")

    return strengths, weaknesses, roadmap
