import csv
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, InternalServerError


# --------------------------------------------------
# Configuration
# --------------------------------------------------

NUM_RUNS = 5
MAX_TOKENS = 32768
MAX_RETRIES = 3

PROMPTS_DIR = Path("prompts")
SOLUTIONS_DIR = Path("solutions")
RESULTS_DIR = Path("results")


# --------------------------------------------------
# API setup
# --------------------------------------------------

load_dotenv()

client = OpenAI(
    base_url="https://api.tesseracted.com/v1",
    api_key=os.environ["KOLIBRI_API_KEY"],
    timeout=620.0,
)


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def natural_key(path):
    """
    Sort files naturally by prefix and number:
    e1, e2, ..., e10, h1, ..., m10.
    """
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", path.stem)

    if match:
        prefix = match.group(1).lower()
        number = int(match.group(2))
        return (prefix, number)

    return (path.stem.lower(), 0)


def get_difficulty(prompt_file):
    """
    Infer difficulty from the first letter of the prompt filename.
    """
    prefix = prompt_file.stem[0].lower()

    difficulty_map = {
        "e": "easy",
        "m": "medium",
        "h": "hard",
        "v": "very hard",
    }

    if prefix not in difficulty_map:
        raise ValueError(
            f"Cannot determine difficulty from filename: "
            f"{prompt_file.name}"
        )

    return difficulty_map[prefix]


def get_solution_file(prompt_file):
    """
    Map, for example:
        e1.txt  -> solutions/e1s.txt
        m7.txt  -> solutions/m7s.txt
        h10.txt -> solutions/h10s.txt
        v5.txt  -> solutions/v5s.txt
    """
    return SOLUTIONS_DIR / f"{prompt_file.stem}s.txt"


def get_correct_answer(prompt_file):
    """
    Read the exact integer from the first 'Answer: ...' line
    in the corresponding solution file.
    """
    solution_file = get_solution_file(prompt_file)

    if not solution_file.exists():
        raise FileNotFoundError(
            f"Missing solution file for {prompt_file.name}: "
            f"{solution_file}"
        )

    solution_text = solution_file.read_text(encoding="utf-8")

    match = re.search(
        r"^\s*Answer:\s*([+-]?\d+)\s*$",
        solution_text,
        flags=re.MULTILINE,
    )

    if not match:
        raise ValueError(
            f"Could not find a line of the form "
            f"'Answer: INTEGER' in {solution_file}"
        )

    return int(match.group(1))


def grade_model_answer(answer, correct_answer, finish_reason):
    """
    Grade one model response.

    Rule 1: If finish_reason == "length", fail immediately.
            Do NOT inspect the answer for a possible result.

    Rule 2: Otherwise, look only at the final non-empty line.

    Rule 3: If that final line contains exactly one integer,
            use that integer as the model's suggested answer.
            Any text before the final line is ignored, and
            surrounding text on the final line is tolerated.

    Accepted final lines include:
        4
        Final answer: 4
        Therefore the answer is 4.
        \\boxed{4}

    Rejected final lines include:
        It is either 3 or 4.
        No numerical answer.

    Returns:
        suggested_answer, match, grading_reason
    """

    if finish_reason == "length":
        return "", False, "length"

    if answer is None:
        return "", False, "did not provide correct format"

    lines = [
        line.strip()
        for line in answer.splitlines()
        if line.strip()
    ]

    if not lines:
        return "", False, "did not provide correct format"

    final_line = lines[-1]

    integers = re.findall(
        r"(?<![\d,])[+-]?\d+(?:,\d{3})*(?![\d,])",
        final_line,
    )

    if len(integers) != 1:
        return "", False, "did not provide correct format"

    suggested_answer = int(
        integers[0].replace(",", "")
    )

    if suggested_answer == correct_answer:
        return suggested_answer, True, "correct"

    return suggested_answer, False, "incorrect"


# --------------------------------------------------
# Prepare folders and files
# --------------------------------------------------

RESULTS_DIR.mkdir(exist_ok=True)

prompt_files = sorted(
    PROMPTS_DIR.glob("*.txt"),
    key=natural_key,
)

usage_file = RESULTS_DIR / "usage.csv"
grading_file = RESULTS_DIR / "grading.csv"


# --------------------------------------------------
# Validate prompt/solution pairing before spending tokens
# --------------------------------------------------

for prompt_file in prompt_files:
    # This raises immediately if a solution is missing or malformed.
    get_correct_answer(prompt_file)


# --------------------------------------------------
# Token counters
# --------------------------------------------------

total_input_tokens = 0
total_output_tokens = 0
total_tokens = 0


# --------------------------------------------------
# Run benchmark
# --------------------------------------------------

with (
    usage_file.open("w", newline="", encoding="utf-8") as usage_csvfile,
    grading_file.open("w", newline="", encoding="utf-8") as grading_csvfile,
):

    usage_writer = csv.writer(usage_csvfile)
    grading_writer = csv.writer(grading_csvfile)

    usage_writer.writerow([
        "question",
        "run",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "reasoning_characters",
        "answer_characters",
        "finish_reason",
        "time_seconds",
        "attempts",
        "request_id",
    ])

    grading_writer.writerow([
        "question",
        "run",
        "difficulty",
        "correct_answer",
        "suggested_answer",
        "match",
        "finish_reason",
        "time_seconds",
        "grading_reason",
    ])

    for prompt_file in prompt_files:

        question = prompt_file.read_text(encoding="utf-8")
        difficulty = get_difficulty(prompt_file)
        correct_answer = get_correct_answer(prompt_file)

        for run_number in range(1, NUM_RUNS + 1):

            print(
                f"Running: {prompt_file.name} "
                f"— run {run_number}/{NUM_RUNS}"
            )

            round_start_time = time.perf_counter()

            response = None
            last_error = None
            last_request_id = None
            attempts_used = 0

            # --------------------------------------------------
            # Send question to Kolibri, with retries
            # --------------------------------------------------

            for attempt in range(1, MAX_RETRIES + 1):

                attempts_used = attempt

                try:
                    response = client.chat.completions.create(
                        model="Aleph-Alpha/Kolibri-1",
                        messages=[
                            {
                                "role": "user",
                                "content": question,
                            }
                        ],
                        max_tokens=MAX_TOKENS,
                        reasoning_effort="high",
                        temperature=1.0,
                        top_p=0.97,
                        stream=False,
                    )

                    break

                except InternalServerError as error:

                    last_error = error

                    status_code = getattr(
                        error,
                        "status_code",
                        None,
                    )

                    request_id = getattr(
                        error,
                        "request_id",
                        None,
                    )

                    response_headers = {}
                    response_body = None

                    if getattr(error, "response", None) is not None:

                        response_headers = dict(
                            error.response.headers
                        )

                        try:
                            response_body = error.response.json()
                        except Exception:
                            response_body = error.response.text

                        if request_id is None:
                            request_id = (
                                error.response.headers.get(
                                    "x-request-id"
                                )
                            )

                    last_request_id = request_id

                    print()
                    print("SERVER ERROR")
                    print("============")
                    print(
                        f"Attempt:    "
                        f"{attempt}/{MAX_RETRIES}"
                    )
                    print(f"HTTP code:  {status_code}")
                    print(f"Request ID: {request_id}")
                    print(f"Error:      {error}")
                    print(f"Body:       {response_body}")

                    for header_name in [
                        "x-request-id",
                        "x-ratelimit-remaining-tokens",
                        "x-ratelimit-reset",
                        "retry-after",
                    ]:

                        value = response_headers.get(
                            header_name
                        )

                        if value is not None:
                            print(
                                f"{header_name}: {value}"
                            )

                    print()

                    if attempt < MAX_RETRIES:

                        wait_time = 2 * attempt

                        print(
                            f"Retrying in "
                            f"{wait_time} seconds..."
                        )

                        time.sleep(wait_time)

            round_elapsed_time = (
                time.perf_counter()
                - round_start_time
            )

            # --------------------------------------------------
            # If every attempt failed
            # --------------------------------------------------

            if response is None:

                output_file = (
                    RESULTS_DIR
                    / f"{prompt_file.stem}_{run_number}.txt"
                )

                output_text = f"""QUESTION
========

{question}

ERROR
=====

The request failed after {MAX_RETRIES} attempts.

{last_error}

REQUEST ID
==========

{last_request_id}

TIME
====

{round_elapsed_time:.2f} seconds
"""

                output_file.write_text(
                    output_text,
                    encoding="utf-8",
                )

                usage_writer.writerow([
                    prompt_file.name,
                    run_number,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "ERROR",
                    f"{round_elapsed_time:.2f}",
                    attempts_used,
                    last_request_id,
                ])

                # API failure is distinct from a formatting failure.
                grading_writer.writerow([
                    prompt_file.name,
                    run_number,
                    difficulty,
                    correct_answer,
                    "",
                    False,
                    "ERROR",
                    f"{round_elapsed_time:.2f}",
                    "API ERROR",
                ])

                usage_csvfile.flush()
                grading_csvfile.flush()

                print(
                    f"FAILED after "
                    f"{MAX_RETRIES} attempts."
                )

                print(
                    f"Time: "
                    f"{round_elapsed_time:.2f} seconds"
                )

                print(
                    f"Last request ID: "
                    f"{last_request_id}"
                )

                print(
                    f"Saved error: "
                    f"{output_file}"
                )

                print()

                continue

            # --------------------------------------------------
            # Extract response
            # --------------------------------------------------

            choice = response.choices[0]
            message = choice.message

            answer = message.content or ""

            message_data = message.model_dump()

            reasoning = (
                message_data.get("reasoning")
                or message_data.get("reasoning_content")
                or ""
            )

            finish_reason = choice.finish_reason

            request_id = (
                getattr(response, "_request_id", None)
                or getattr(response, "request_id", None)
                or ""
            )

            if (
                not answer
                and finish_reason == "length"
            ):
                answer_for_file = (
                    "[NO FINAL ANSWER PRODUCED: "
                    "the model exhausted its token "
                    "budget during reasoning]"
                )
            else:
                answer_for_file = answer

            # --------------------------------------------------
            # Grade response
            # --------------------------------------------------

            suggested_answer, answers_match, grading_reason = (
                grade_model_answer(
                    answer,
                    correct_answer,
                    finish_reason,
                )
            )

            # --------------------------------------------------
            # Token usage
            # --------------------------------------------------

            usage = response.usage

            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            run_total_tokens = usage.total_tokens

            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            total_tokens += run_total_tokens

            # --------------------------------------------------
            # Save result
            # --------------------------------------------------

            output_file = (
                RESULTS_DIR
                / f"{prompt_file.stem}_{run_number}.txt"
            )

            output_text = f"""QUESTION
========

{question}

REASONING
=========

{reasoning}

ANSWER
======

{answer_for_file}

FINISH REASON
=============

{finish_reason}

GRADING REASON
==============

{grading_reason}

TIME
====

{round_elapsed_time:.2f} seconds

ATTEMPTS
========

{attempts_used}
"""

            output_file.write_text(
                output_text,
                encoding="utf-8",
            )

            # --------------------------------------------------
            # Log usage
            # --------------------------------------------------

            usage_writer.writerow([
                prompt_file.name,
                run_number,
                input_tokens,
                output_tokens,
                run_total_tokens,
                len(reasoning),
                len(answer),
                finish_reason,
                f"{round_elapsed_time:.2f}",
                attempts_used,
                request_id,
            ])

            # --------------------------------------------------
            # Log grading
            # --------------------------------------------------

            grading_writer.writerow([
                prompt_file.name,
                run_number,
                difficulty,
                correct_answer,
                suggested_answer,
                answers_match,
                finish_reason,
                f"{round_elapsed_time:.2f}",
                grading_reason,
            ])

            usage_csvfile.flush()
            grading_csvfile.flush()

            # --------------------------------------------------
            # Terminal output
            # --------------------------------------------------

            print(f"Saved: {output_file}")

            print(
                f"Input tokens:  "
                f"{input_tokens:,}"
            )

            print(
                f"Output tokens: "
                f"{output_tokens:,} / "
                f"{MAX_TOKENS:,} max"
            )

            print(
                f"Total billed tokens: "
                f"{run_total_tokens:,}"
            )

            print(
                f"Reasoning characters: "
                f"{len(reasoning):,} | "
                f"Answer characters: "
                f"{len(answer):,}"
            )

            print(
                f"Finish reason: "
                f"{finish_reason}"
            )

            print(
                f"Time: "
                f"{round_elapsed_time:.2f} seconds"
            )

            print(
                f"Attempts: "
                f"{attempts_used}"
            )

            print(
                f"Difficulty: "
                f"{difficulty}"
            )

            print(
                f"Correct answer: "
                f"{correct_answer}"
            )

            if suggested_answer == "":
                print(
                    f"Suggested answer: "
                    f"[none]"
                )
            else:
                print(
                    f"Suggested answer: "
                    f"{suggested_answer}"
                )

            print(
                f"Match: "
                f"{answers_match}"
            )

            print(
                f"Grading reason: "
                f"{grading_reason}"
            )

            if finish_reason == "length":
                print(
                    "GRADE FAILURE: finish reason was "
                    "'length'; answer was not checked."
                )

            elif grading_reason == "did not provide correct format":
                print(
                    "GRADE FAILURE: could not extract "
                    "an unambiguous integer from the "
                    "final non-empty line."
                )

            print(
                f"Benchmark total billed "
                f"so far: "
                f"{total_tokens:,} tokens"
            )

            print()


# --------------------------------------------------
# Final summary
# --------------------------------------------------

print("Finished.")
print()
print("FINAL TOKEN USAGE")
print("=================")

print(
    f"Input tokens:  "
    f"{total_input_tokens:,}"
)

print(
    f"Output tokens: "
    f"{total_output_tokens:,}"
)

print(
    f"Total billed tokens: "
    f"{total_tokens:,}"
)

print(
    f"Usage log: "
    f"{usage_file}"
)

print(
    f"Grading log: "
    f"{grading_file}"
)