import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from brevo import send_completion_email  # noqa: E402


async def main(email, name, score, max_score):
    res = await send_completion_email(email, name, score, max_score)
    print("Brevo response:", res)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python send_test_completion_email.py <email> <name> [score] [max]")
        sys.exit(1)
    score = int(sys.argv[3]) if len(sys.argv) > 3 else 105
    max_score = int(sys.argv[4]) if len(sys.argv) > 4 else 125
    asyncio.run(main(sys.argv[1], sys.argv[2], score, max_score))
