import os

# 👉 CHANGE THIS to your project path
PROJECT_PATH = r"C:\Users\chand\Downloads\Rule_validator_new_requirment"

# 👉 Output file
OUTPUT_FILE = os.path.join(PROJECT_PATH, "project_dump.txt")


def should_include(file):
    return file.endswith((".py", ".txt", ".md", ".json"))


def export_project():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:

        for root, dirs, files in os.walk(PROJECT_PATH):
            for file in files:
                if should_include(file):

                    file_path = os.path.join(root, file)

                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        relative_path = os.path.relpath(file_path, PROJECT_PATH)

                        out.write("\n" + "="*80 + "\n")
                        out.write(f"FILE: {relative_path}\n")
                        out.write("="*80 + "\n\n")
                        out.write(content)
                        out.write("\n\n")

                    except Exception as e:
                        out.write(f"\nERROR reading {file_path}: {e}\n")

    print(f"\n✅ Project exported to: {OUTPUT_FILE}")


if __name__ == "__main__":
    export_project()